#!/usr/bin/env python3
"""Integrate real discovery conditions, onboarding grants, and numeric economy.

Offline planning experiment, not game/runtime/SDK validation. --snapshot reads a
pinned projected input; default reads the repository's real data files. No writes
to data/. All output parameters and limitations are recorded in the result.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import random
from pathlib import Path
from collections import Counter
from economy_simulation_core import EconomyCore, EPS, development, mastery
from validate_discovery import match, eligible, check_contract

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['cats','buildings','progression','development_score','economy_balance','onboarding','discovery_rules']

def read(path): return json.loads(path.read_text(encoding='utf-8'))

def load_inputs(root, snapshot=False):
    if snapshot:
        bundle = read(root/'reports/integrated_source_projection.json')
        inputs=bundle['inputs']
        for name,ref in bundle.get('externalInputs',{}).items():
            raw=(root/ref['path']).read_bytes()
            sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if sha!=ref['gitBlobSha']:raise ValueError('Snapshot supplement changed: '+ref['path'])
            inputs[name]=json.loads(raw)
        return inputs, {'mode':bundle['mode'],'sourceCommit':bundle['sourceCommit'], 'sourceBlobShas':bundle['sourceBlobShas']}
    return {n:read(root/'data'/f'{n}.json') for n in NAMES}, {'mode':'repository_data'}

def validate_inputs(inputs, timing, settings):
    source={'cats':[{'catalogId':c['catalogId'],'minimumCenterLevel':c['discovery']['minimumCenterLevel']} for c in inputs['cats']],
            'buildings':inputs['buildings']['buildings'],'progression':inputs['progression'],
            'development':inputs['development_score'],'onboarding':inputs['onboarding']}
    check_contract(inputs['discovery_rules'],source)
    for c in inputs['cats']:
        if any(type(v) is not int or not 2<=v<=8 for v in c['baseAbilities'].values()):raise ValueError('Invalid initial ability')
    for tier in timing['normalByMinimumCenter'].values():
        if any(not isinstance(v,(int,float)) or v<0 for v in tier.values()):raise ValueError('Invalid rescue duration')
    for case in settings['cases']:
        if case['sessionsPerDay'] not in (1,2,3,4,6,8): raise ValueError('Unsupported session frequency')
        if case.get('openingBusiness','farm') not in inputs['onboarding']['firstBusiness']['choices']:raise ValueError('Bad opening business')
    m=settings['model']
    if not (0<m['onlineStepMinutes']<=1 and 0<m['offlineStepMinutes']<=10 and 0<m['horizonDays']<=365):raise ValueError('Invalid step/horizon')

class IntegratedSimulation(EconomyCore):
    def __init__(self, inputs, settings, case, timing):
        super().__init__(inputs, settings, case)
        self.on=inputs['onboarding']; self.discovery=inputs['discovery_rules']; self.timing=timing
        self.rules={r['catalogId']:r for r in self.discovery['rules']}
        self.cat_by_id={c['catalogId']:c for c in self.cats}
        self.early={c['catalogId']:c for c in self.on['firstRescues']}
        self.flags=set(); self.claimed=set(); self.ever_assigned=set()
        self.active_minutes=0.0; self.first_organic=0.0
        self.opening=self.case.get('openingBusiness','farm')
        for target,factor in self.case.get('centerCostMultipliers',{}).items():
            if not 2<=int(target)<=10 or not 0<factor<=2:raise ValueError('Invalid cost sensitivity')
            i=int(target)-1;self.e['centerUpgrade']['costGoldByTargetLevel'][i]*=factor
        self.rng=random.Random(self.case.get('seed',0)); self.phase_times=Counter()
        self.first_session=None; self.post_tutorial_target=None

    def state(self):
        return {'levels':self.levels,'owned':list(self.residents),'flags':list(self.flags),
                'development':development(self.levels,self.b,self.awards),'job':self.search}

    def award_grants(self):
        for g in self.on['grants']:
            if g['id'] in self.claimed:continue
            def ok(e):
                return (e['id'] in self.ever_assigned if e['kind']=='assignment_ever' else match(e,self.state()))
            if all(ok(e) for e in g['all']):
                self.gold+=g['amount'];self.earned['milestoneSupport']+=g['amount'];self.claimed.add(g['id'])
                self.logs.append({'minute':round(self.t,4),'event':'grant','id':g['id'],'gold':g['amount']})

    def care_rate(self):
        workers=sorted((self.efficiency(r,'rescue_center') for r in self.residents.values() if r['job']=='rescue_center'),reverse=True)
        return max(1.0,self.factor('rescue_center')*sum(w*x for w,x in zip(self.e['staff']['slotWeights'],workers)))

    def interval_boundary(self,end,foreground,ad):
        if self.search:
            j=self.search
            if j['phase'] in ('search_reserved','care_pending') and j['end']>self.t+EPS:end=min(end,j['end'])
            if j['phase']=='interacting' and foreground and not ad and j['remaining']>EPS:end=min(end,self.t+j['remaining'])
        return end

    def interval_record(self,minutes,foreground,ad,cash,support,credited):
        if self.search:
            self.phase_times[self.search['phase']]+=minutes
            if foreground and not ad and self.search['phase']=='interacting':
                self.search['remaining']=max(0,self.search['remaining']-minutes)
        if foreground and not ad:self.active_minutes+=minutes
        if credited and cash>0 and 'first_business_started' not in self.flags:
            # Only the opening farm/fish-market exists before the first business fact.
            self.first_organic+=cash*minutes
            if self.first_organic+EPS>=self.on['firstBusiness']['completeWhenAssignedBuildingOrganicGoldGte']:
                self.flags.add('first_business_started');self.first_cash=self.t+minutes
                self.logs.append({'minute':round(self.t+minutes,4),'event':'first_business','value':self.opening})

    def settle_events(self,foreground):
        for bid in list(self.jobs):
            if self.jobs[bid]['end']<=self.t+EPS:
                self.levels[bid]=self.jobs.pop(bid)['target']
                self.logs.append({'minute':round(self.t,4),'event':'center' if bid=='rescue_center' else 'building','building':bid,'value':self.levels[bid]})
        j=self.search
        if j:
            if j['phase']=='search_reserved' and j['end']<=self.t+EPS:
                j['phase']='scene_ready';j['end']=math.inf
            if j['phase']=='interacting' and j['remaining']<=EPS and foreground:
                j['phase']='care_pending'
                if j['id'] in self.early: duration=self.early[j['id']]['careSeconds']/60
                elif j['id']=='CAT_050':duration=0
                else:
                    tier=self.cat_by_id[j['id']]['discovery']['minimumCenterLevel']
                    duration=self.timing['normalByMinimumCenter'][str(tier)]['careWorkSeconds']/60/self.care_rate()
                    duration*=self.case.get('normalCareScale',1)
                j['end']=self.t+duration
            if j['phase']=='care_pending' and j['end']<=self.t+EPS:
                j['phase']='care_ready';j['end']=math.inf
        if foreground:
            self.assign()
            self.ever_assigned.update(r['job'] for r in self.residents.values() if r['job'])
            self.award_grants()
        occupied=len(self.residents)+int(self.search is not None)
        if occupied>self.p['levels'][self.center-1]['cap']:raise ValueError('Capacity overflow')
        self.max_occupancy=max(self.max_occupancy,occupied)
        req=self.p['ending']['requires']
        economic=(self.center==req['rescueCenterLevel'] and development(self.levels,self.b,self.awards)>=req['villageDevelopment']
                  and all(self.levels[b]>=1 for b in req['majorBuildingsBuilt'])
                  and all(self.levels[b]>=n for b,n in req['requiredBuildingLevels'].items()))
        if economic and self.economic_ready is None:self.economic_ready=self.t
        if len(self.residents)==50 and self.collection is None:self.collection=self.t
        if economic and len(self.residents)==50 and foreground and self.festival is None:self.festival=self.t

    def choices(self):
        cap=self.p['levels'][self.center-1]['cap']
        if self.case.get('discoveryGateAblation') and len(self.residents)>=8:
            if self.search or len(self.residents)>=cap or 'first_business_started' not in self.flags:return []
            return [c['catalogId'] for c in self.cats if c['catalogId'] not in self.residents and c['discovery']['minimumCenterLevel']<=self.center
                    and (c['catalogId']!='CAT_050' or len(self.residents)==49)]
        return eligible(self.discovery,self.state(),cap)

    def act_rescue(self):
        if self.search:
            j=self.search
            if j['phase']=='scene_ready':
                j['phase']='interacting'
                j['remaining']=(self.timing['finalWelcomeForegroundSeconds'] if j['id']=='CAT_050' else self.timing['interactionForegroundSeconds'])/60
            elif j['phase']=='care_ready':
                cid=j['id'];cat=self.cat_by_id[cid]
                if cid in self.residents:raise ValueError('Duplicate resident')
                self.residents[cid]={'abilities':dict(cat['baseAbilities']),'xp':dict.fromkeys(cat['baseAbilities'],0.0),'work':{},'job':None}
                self.logs.append({'minute':round(self.t,4),'event':'resident','id':cid})
                self.search=None
            return
        choices=self.choices()
        if not choices:return
        cid=self.rng.choice(choices) if self.case.get('randomSelection') else min(choices)
        if cid in self.early:search=self.early[cid]['searchSeconds']/60
        elif cid=='CAT_050':search=0
        else:
            tier=self.cat_by_id[cid]['discovery']['minimumCenterLevel']
            search=self.timing['normalByMinimumCenter'][str(tier)]['searchSeconds']/60*self.case.get('normalSearchScale',1)
        self.search={'id':cid,'jobId':'rescue/'+cid,'phase':'search_reserved','end':self.t+search,'ads':0,'remaining':0.0}
        self.logs.append({'minute':round(self.t,4),'event':'reserve','id':cid,'searchMinutes':search})

    def cost_for_target(self,bid,target):
        curve=self.e['levelCurves'][str(self.b[bid]['maxLevel'])]['cost'];base=self.e['buildingEconomy'][bid]['baseBuildCostGold'];rnd=self.e['construction']['costRoundUpToGold']
        return sum(math.ceil(base*curve[n-1]/rnd)*rnd for n in range(self.levels[bid]+1,target+1))

    def plans(self,expr):
        """Feasible prerequisite alternatives from current facts, without future-center assumptions."""
        if match(expr,self.state()):return [({},0)]
        if 'any' in expr:return [p for e in expr['any'] for p in self.plans(e)]
        if 'all' in expr:
            plans=[({},0)]
            for e in expr['all']:
                next_plans=[]
                for a,da in plans:
                    for b,db in self.plans(e):
                        merged=dict(a)
                        for k,v in b.items():merged[k]=max(merged.get(k,0),v)
                        next_plans.append((merged,max(da,db)))
                plans=next_plans
            return plans
        if expr['kind']=='building_level':
            bid=expr['id'];target=expr['gte'];b=self.b[bid]
            if bid=='rescue_center' or b['unlock']>self.center or target>min(b['maxLevel'],self.center):return []
            return [({bid:target},0)]
        if expr['kind']=='development':return [({},expr['gte'])]
        return []

    def options(self):
        return [bid for bid,b in self.b.items() if bid!='rescue_center' and bid not in self.jobs and b['unlock']<=self.center and self.levels[bid]<min(b['maxLevel'],self.center)]

    def buy_if_affordable(self,bid):
        if bid not in self.jobs and self.gold+EPS>=self.cost_time(bid)[0]:self.start(bid)

    def buy_development(self,target):
        current=development(self.levels,self.b,self.awards)
        if current>=target:return False
        opts=[]
        for bid in self.options():
            alt=dict(self.levels);alt[bid]+=1;gain=development(alt,self.b,self.awards)-current
            if gain>0:opts.append((self.cost_time(bid)[0]/gain,bid))
        if opts:self.buy_if_affordable(min(opts)[1])
        return True

    def buy_discovery_prerequisite(self):
        if self.search or len(self.residents)>=self.p['levels'][self.center-1]['cap'] or self.choices():return False
        candidates=[]
        for cid,r in self.rules.items():
            if cid in self.residents:continue
            for levels,dev in self.plans(r['eligibility']):
                cost=sum(self.cost_for_target(k,v) for k,v in levels.items())
                candidates.append((cost,dev,cid,levels))
        if not candidates:return False
        _,dev,cid,levels=min(candidates,key=lambda x:x[:3])
        for bid in sorted(levels,key=lambda k:self.cost_for_target(k,levels[k])):
            if self.levels[bid]<levels[bid]:
                if bid not in self.jobs:self.buy_if_affordable(bid)
                return True
        return self.buy_development(dev)

    def purchase(self):
        if self.festival is not None:return
        if 'first_business_started' not in self.flags:
            if self.center<3:
                if 'rescue_center' not in self.jobs and not self.center_gates():self.start('rescue_center')
                return
            for bid in ('housing','park'):
                if self.levels[bid]<1:self.buy_if_affordable(bid);return
            if self.center<4:
                if 'rescue_center' not in self.jobs and not self.center_gates():self.start('rescue_center')
                return
            if self.levels[self.opening]<1:self.buy_if_affordable(self.opening)
            return
        if self.center<10 and 'rescue_center' not in self.jobs and not self.center_gates():self.start('rescue_center');return
        options=self.options()
        fresh=[b for b in options if self.levels[b]==0 and self.e['buildingEconomy'][b]['baseGoldPerMinute']>0]
        if fresh:self.buy_if_affordable(min(fresh,key=lambda b:self.cost_time(b)[0]));return
        if self.buy_discovery_prerequisite():return
        target=(self.p['levels'][self.center]['upgradeRequirements']['villageDevelopment'] if self.center<10 else self.p['ending']['requires']['villageDevelopment'])
        if self.buy_development(target):return
        if self.center==10:
            req=self.p['ending']['requires']
            needed=[bid for bid in options if bid in req['majorBuildingsBuilt'] and self.levels[bid]<req['requiredBuildingLevels'].get(bid,1)]
            if needed:self.buy_if_affordable(min(needed,key=lambda b:self.cost_time(b)[0]));return
        cash,support=self.rates()
        wait=math.inf if self.center==10 else max(0,(self.cost_time('rescue_center')[0]-self.gold)/(cash+support))
        horizon=min(self.cfg['roiLookaheadCreditedMinutes'],wait*.7)
        candidates=[]
        for bid in options:
            if not self.e['buildingEconomy'][bid]['baseGoldPerMinute']:continue
            cost=self.cost_time(bid)[0]
            if cost>self.gold+EPS:continue
            saved={cid:r['job'] for cid,r in self.residents.items()}
            self.levels[bid]+=1;self.assign();gain=self.rates()[0]-cash;self.levels[bid]-=1
            for cid,job in saved.items():self.residents[cid]['job']=job
            if gain>EPS and cost/gain<horizon:candidates.append((cost/gain,bid))
        if candidates:self.start(min(candidates)[1])

    def ad_allowed(self,kind):
        return ('first_business_started' in self.flags and self.active_minutes*60+EPS>=self.on['adPolicy']['minimumForegroundGameplaySeconds']
                and self.case['rewarded'] and kind in self.case.get('adKinds',['offline','boost','speedup']))

    def watch(self,kind,end):
        duration=self.cfg['adSecondsAssumed']/60
        if self.t+duration>end+EPS:return False
        self.advance(self.t+duration,True,ad=True);self.ads[kind]+=1
        self.logs.append({'minute':round(self.t,4),'event':'ad','kind':kind})
        return True

    def snapshot(self):
        cash,support=self.rates()
        return {'day':round(self.t/1440,5),'center':self.center,'residents':len(self.residents),
                'gold':round(self.gold,2),'development':development(self.levels,self.b,self.awards),
                'organicGoldPerMinute':round(cash+support,3),'buildingLevels':dict(self.levels),'pendingRescuePhase':self.search['phase'] if self.search else None}

    def run(self):
        horizon=self.cfg['horizonDays']*1440;interval=1440/self.case['sessionsPerDay'];n=0
        while n*interval<horizon-EPS:
            start=n*interval;self.advance(start,False)
            duration=self.cfg['firstSessionMinutes'] if n==0 else self.cfg['sessionMinutes'];end=min(horizon,start+duration)
            base=self.offline_bank;gap=start-self.last_logout;self.offline_bank=0
            self.settle_events(True)
            if self.ad_allowed('offline') and gap*60>=self.e['ads']['offlineExtra']['minOfflineSeconds'] and base>0 and self.watch('offline',end):
                bonus=base*self.e['ads']['offlineExtra']['bonusMultiplierOfOrganicBase'];self.gold+=bonus;self.earned['offlineAdExtra']+=bonus
            boosted=False;sped=False
            while self.t<end-EPS:
                self.settle_events(True)
                if self.festival is not None:break
                self.act_rescue();self.settle_events(True)
                interacting=self.search and self.search['phase']=='interacting'
                if not interacting:
                    self.purchase();self.settle_events(True)
                    if self.ad_allowed('boost') and not boosted and self.rates()[0]>0 and self.boost_left<end-self.t-self.cfg['adSecondsAssumed']/60:
                        if self.watch('boost',end):
                            a=self.e['ads']['incomeBoost'];self.boost_left=min(a['maximumBankedSeconds']/60,self.boost_left+a['secondsPerCompletedAd']/60);boosted=True
                    if self.ad_allowed('speedup') and not sped:
                        a=self.e['ads']['speedup'];opts=list(self.jobs.items())
                        if self.search and self.search['phase']=='search_reserved':opts.append(('search',self.search))
                        opts=[(k,j) for k,j in opts if (j['end']-self.t)*60>=a['minRemainingSecondsToOffer'] and j['ads']<a['maxClaimsPerJob']]
                        if opts:
                            bid,j=max(opts,key=lambda x:(x[0]=='rescue_center',x[1]['end']))
                            if self.watch('speedup',end):
                                if j.get('end',math.inf)<math.inf:j['end']=max(self.t,j['end']-a['secondsPerCompletedAd']/60)
                                j['ads']+=1;sped=True
                if self.festival is None:self.advance(min(end,self.t+self.cfg['onlineStepMinutes']),True)
            if n==0:self.first_session=self.snapshot()
            self.last_logout=self.t;n+=1
            if self.festival is not None:break
        if self.festival is None:self.advance(horizon,False)
        def days(t):return None if t is None else round(t/1440,5)
        ordered=[x for x in self.logs if x['event']=='resident']
        gaps=[{'from':a['id'],'to':b['id'],'hours':round((b['minute']-a['minute'])/60,3)} for a,b in zip(ordered,ordered[1:])]
        return {'case':self.case,'firstBusinessMinutes':self.first_cash,'centerReachedDay':{str(x['value']):days(x['minute']) for x in self.logs if x['event']=='center'},
                'economicFestivalReadyDay':days(self.economic_ready),'collection50Day':days(self.collection),'festivalConditionsDay':days(self.festival),
                'firstSession':self.first_session,'final':self.snapshot(),'snapshots':self.snapshots,'adCounts':dict(self.ads),'grants':sorted(self.claimed),
                'earnedGold':{k:round(v,3) for k,v in self.earned.items()},'spentGold':self.spent,'maxReservedAndOwned':self.max_occupancy,
                'phaseWaitHours':{k:round(v/60,3) for k,v in self.phase_times.items()},'centerGateHoursOverlapping':{k:round(v/60,3) for k,v in self.waiting.items()},
                'largestRescueGaps':sorted(gaps,key=lambda x:x['hours'],reverse=True)[:5],'events':self.logs}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--snapshot',action='store_true')
    p.add_argument('--case',action='append');p.add_argument('--offline-step',type=float);p.add_argument('--online-step',type=float)
    p.add_argument('--output',default='reports/integrated_progression_v02.json');p.add_argument('--include-events',action='store_true');a=p.parse_args()
    try:
        inputs,provenance=load_inputs(a.root,a.snapshot);settings=read(a.root/'data/integrated_simulation_scenarios.json');timing=read(a.root/'data/rescue_timing.json')
        if a.offline_step is not None:settings['model']['offlineStepMinutes']=a.offline_step
        if a.online_step is not None:settings['model']['onlineStepMinutes']=a.online_step
        if a.case and set(a.case)-{c['id'] for c in settings['cases']}:raise ValueError('Unknown case ID')
        validate_inputs(inputs,timing,settings);results=[]
        for case in settings['cases']:
            if a.case and case['id'] not in a.case:continue
            r=IntegratedSimulation(inputs,settings,case,timing).run()
            print(case['id'],'first min',round(r['firstBusinessMinutes'] or 0,3),'center10',r['centerReachedDay'].get('10'),'festival',r['festivalConditionsDay'],'cats',r['final']['residents'],flush=True)
            if not a.include_events:r.pop('events')
            results.append(r)
        fingerprint=hashlib.sha256(json.dumps(inputs,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        output={'status':'hypothetical_integrated_model_not_real_player_or_engine_result','provenance':provenance,'inputFieldsSha256':fingerprint,'settings':settings,'timing':timing,'results':results}
        path=a.root/a.output;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
        summary={'sourceCommit':settings['sourceCommit'],'status':output['status'],'inputMode':provenance['mode'],'results':[{k:r[k] for k in ['case','firstBusinessMinutes','centerReachedDay','economicFestivalReadyDay','collection50Day','festivalConditionsDay','firstSession','final','adCounts','earnedGold','maxReservedAndOwned','largestRescueGaps']} for r in results]}
        path.with_name(path.stem+'.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    except (OSError,ValueError,KeyError,AssertionError,TypeError) as e:p.exit(1,'FAIL: '+str(e)+'\n')

if __name__=='__main__':main()
