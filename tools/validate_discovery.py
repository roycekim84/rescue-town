#!/usr/bin/env python3
"""Structural discovery audit. Standard library only. Not a runtime/pacing test."""
from __future__ import annotations
import argparse
import copy
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT_IDS = [f'CAT_{i:03}' for i in range(1, 51)]
KINDS = {'building_level','resident_count','resident_owned','development','flag'}

def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def project(root):
    c=load_json(root/'data/cats.json'); b=load_json(root/'data/buildings.json')
    p=load_json(root/'data/progression.json'); d=load_json(root/'data/development_score.json')
    o=load_json(root/'data/onboarding.json')
    return {'cats':[{'catalogId':x['catalogId'],'minimumCenterLevel':x['discovery']['minimumCenterLevel']} for x in c],
            'buildings':[{k:x[k] for k in ['id','maxLevel','unlock','staff']} for x in b['buildings']],
            'progression':{'levels':[{k:x[k] for k in ['level','cap','upgradeRequirements']} for x in p['levels']], 'ending':p['ending']},
            'development':{'awards':d['awards']},'onboarding':{'firstRescues':o['firstRescues'],'rescueRules':o['rescueRules']}}

def walk(expr):
    for key in ('all','any'):
        if key in expr:
            for child in expr[key]: yield from walk(child)
            return
    yield expr

def match(expr, state):
    if 'all' in expr: return all(match(x,state) for x in expr['all'])
    if 'any' in expr: return any(match(x,state) for x in expr['any'])
    k=expr['kind']
    if k=='building_level': return state['levels'].get(expr['id'],0)>=expr['gte']
    if k=='resident_count': return len(state['owned'])>=expr['gte']
    if k=='resident_owned': return expr['id'] in state['owned']
    if k=='development': return state['development']>=expr['gte']
    if k=='flag': return expr['id'] in state['flags']
    raise ValueError('Unknown condition: '+str(k))

def score(levels, source):
    a=source['development']['awards']; total=0
    for b in source['buildings']:
        n=levels.get(b['id'],0)
        if b['id']=='rescue_center' or not n: continue
        tag='lv5MaxBuilding' if b['maxLevel']==5 else 'lv10MaxBuilding'
        bonus=a['parkUpgradeBonusPerLevel'] if b['id']=='park' else a['townSquareUpgradeBonusPerLevel'] if b['id']=='town_square' else 0
        total+=a['buildingConstruction'][tag]+(n-1)*(a['buildingUpgrade'][tag+'PerLevel']+bonus)
    return total

def empty_state():
    return {'saveId':'reference-save','levels':{'rescue_center':1},'development':0,'owned':[], 'flags':[], 'job':None}

def eligible(data,state,cap):
    if state['job'] is not None or len(state['owned'])>=cap: return []
    early=next((id for id in CAT_IDS[:8] if id not in state['owned']),None)
    if early:
        return [r['catalogId'] for r in data['rules'] if r['catalogId']==early and match(r['eligibility'],state)]
    return [r['catalogId'] for r in data['rules'] if r['phase']!='onboarding' and r['catalogId'] not in state['owned'] and match(r['eligibility'],state)]

def reserve(data,state,id,cap):
    """Pure reference transaction. Persistence atomicity is an engine requirement."""
    s=copy.deepcopy(state)
    if s['job'] and s['job']['catalogId']==id: return s
    if id not in eligible(data,s,cap): raise ValueError('Ineligible, duplicate, busy, or capacity full')
    s['job']={'jobId':s['saveId']+'/rescue/'+id,'residentId':s['saveId']+'/'+id,'catalogId':id,'phase':'search_reserved'}
    return s

def advance(state,phase):
    s=copy.deepcopy(state)
    if not s['job']: raise ValueError('No reserved job')
    current=s['job']['phase']
    if phase==current: return s
    allowed={'search_reserved':'scene_ready','scene_ready':'care_pending'}
    if allowed.get(current)!=phase: raise ValueError('Illegal phase transition')
    s['job']['phase']=phase
    return s

def settle(state,id):
    s=copy.deepcopy(state)
    if id in s['owned']: return s
    if not s['job'] or s['job']['catalogId']!=id or s['job']['phase']!='care_pending':
        raise ValueError('Not ready for settlement')
    s['owned'].append(id); s['job']=None
    return s

def check_contract(data,source):
    def require(ok,msg):
        if not ok: raise ValueError(msg)
    ids=[r['catalogId'] for r in data['rules']]
    require(ids==CAT_IDS,'Exactly 50 ordered unique IDs required')
    cats={c['catalogId']:c for c in source['cats']}
    require(set(cats)==set(CAT_IDS),'Source roster mismatch')
    buildings={b['id']:b for b in source['buildings']}
    refs={r['catalogId']:r for r in data['rules']}
    def exprcheck(e):
        require(isinstance(e,dict),'Condition must be object')
        if 'all' in e or 'any' in e:
            key='all' if 'all' in e else 'any'
            require(set(e)=={key} and isinstance(e[key],list) and len(e[key])>0,'Invalid condition group')
            for child in e[key]: exprcheck(child)
            return
        kind=e.get('kind'); require(kind in KINDS,'Unknown condition kind')
        expected={'kind','id'} if kind in ('resident_owned','flag') else {'kind','gte'} if kind in ('resident_count','development') else {'kind','id','gte'}
        require(set(e)==expected,'Invalid condition fields')
        if 'gte' in e: require(type(e['gte']) is int and e['gte']>=0,'Nonnegative integer threshold required')
        if kind=='building_level': require(e['id'] in buildings and 1<=e['gte']<=buildings[e['id']]['maxLevel'],'Invalid building reference/level')
        if kind=='resident_owned': require(e['id'] in cats,'Unknown resident dependency')
        if kind=='resident_count': require(e['gte']<50,'Resident count would block the final rescue')
        if kind=='flag': require(e['id']=='first_business_started','Unknown flag or forbidden festival/weather gate')
    for r in data['rules']:
        id=r['catalogId']; exprcheck(r['eligibility'])
        require(r['phase'] in {'onboarding','normal','final'},'Unknown phase')
        minc=cats[id]['minimumCenterLevel']
        require(r['eligibility']['all'][0]=={'kind':'building_level','id':'rescue_center','gte':minc},'Center gate must match cats.json and be unconditional')
        require(bool(r['hints']['basicKo']) and bool(r['scene']['locationId']),'Missing hint/location')
        require(r['scene']['mechanic'] in {'food_lure','trust_wait','obstacle_clear','trail_search','sound_search','welcome'},'Unknown mechanic')
        if id not in CAT_IDS[:8]:
            require(r['eligibility']['all'][1]=={'kind':'flag','id':'first_business_started'},'Normal discovery must follow first business')
            require(all(x['kind']!='resident_owned' for x in walk(r['eligibility'])),'Normal rescues must not depend on specific optional residents')
    for f in source['onboarding']['firstRescues']:
        r=refs[f['catalogId']]
        expected=[{'kind':'building_level','id':'rescue_center','gte':f['center']}]
        if f['after']: expected.append({'kind':'resident_owned','id':f['after']})
        expected += [{'kind':'building_level','id':k,'gte':v} for k,v in f['requiresBuildings'].items()]
        require(r['eligibility']=={'all':expected},'First eight must exactly mirror onboarding conditions')
        require(r['phase']=='onboarding','Onboarding phase mismatch')
        require(r['scene']['locationId']==f['locationId'] and r['scene']['mechanic']==f['mechanic'],'First eight scene mismatch')
    final=refs['CAT_050']
    require(final['phase']=='final' and final['scene']['mechanic']=='welcome','Final cat must be a welcome')
    require(final['eligibility']=={'all':[{'kind':'building_level','id':'rescue_center','gte':10},{'kind':'flag','id':'first_business_started'},{'kind':'resident_count','gte':49}]},'Final cat needs center10 and previous49, not festival')
    # Explicit dependency cycle check; count gates are checked through closure below.
    graph={id:[x['id'] for x in walk(r['eligibility']) if x['kind']=='resident_owned'] for id,r in refs.items()}
    def visit(id,stack,done):
        require(id not in stack,'Resident prerequisite cycle')
        if id in done:return
        for dep in graph[id]:visit(dep,stack|{id},done)
        done.add(id)
    done=set()
    for id in CAT_IDS:visit(id,set(),done)
    require(data['selection']['maxConcurrentJobs']==1 and data['selection']['maxCapacity']==50,'Capacity contract changed')
    return True

def structural_route(data,source,seed=0,business='farm',fill_to_cap=True):
    """Constructive witness with eventually affordable buildings/mastery; no time model."""
    rng=random.Random(seed);s=empty_state();trace=[]
    levels=source['progression']['levels']
    for row in levels:
        n=row['level'];cap=row['cap']
        s['levels']={b['id']:min(b['maxLevel'],n) for b in source['buildings'] if b['unlock']<=n}
        if n<4:
            # Optional paid upgrades are hidden until the first real business.
            for k in list(s['levels']):
                if k!='rescue_center':s['levels'][k]=1
        if n>=4:
            # Either paid opening business is valid under the onboarding budget audit.
            assert business in s['levels'];s['flags']=['first_business_started']
        s['development']=score(s['levels'],source)
        target=cap if fill_to_cap or n==10 else levels[n]['upgradeRequirements']['residentCount']
        while len(s['owned'])<target:
            choices=eligible(data,s,cap)
            if not choices: raise ValueError(f'Blocked center{n}: {len(s["owned"])}/{target}')
            id=rng.choice(choices);s=reserve(data,s,id,cap)
            s=advance(s,'scene_ready');s=advance(s,'care_pending');s=settle(s,id)
        trace.append({'center':n,'cap':cap,'residents':len(s['owned']),'maxDevelopmentAtCenter':s['development']})
        if n<10:
            req=levels[n]['upgradeRequirements']
            if len(s['owned'])<req['residentCount'] or s['development']<req['villageDevelopment']:raise ValueError('Next center condition unreachable')
            mastery=req['jobMastery']
            slots=sum(max((v for k,v in b['staff'].items() if int(k)<=s['levels'].get(b['id'],0)),default=0) for b in source['buildings'])
            if mastery and min(slots,len(s['owned']))<mastery['count']:raise ValueError('Insufficient distinct potential workers')
    req=source['progression']['ending']['requires']
    if not(set(s['owned'])==set(CAT_IDS) and s['owned'][-1]=='CAT_050'):raise ValueError('Final roster mismatch')
    if s['development']<req['villageDevelopment']:raise ValueError('Festival score unreachable')
    if not all(s['levels'].get(k,0)>=v for k,v in req['requiredBuildingLevels'].items()):raise ValueError('Festival building unavailable')
    if not all(s['levels'].get(k,0)>=1 for k in req['majorBuildingsBuilt']):raise ValueError('Festival type missing')
    return trace,s['owned']

def report(data,source,seeds=100):
    check_contract(data,source)
    for seed in range(seeds):
        for biz in ('farm','fish_market'):
            for fill in (False,True): structural_route(data,source,seed,biz,fill)
    trace,order=structural_route(data,source)
    counts=[sum(c['minimumCenterLevel']<=n for c in source['cats']) for n in range(1,11)]
    return {'status':'structural_condition_checks_passed_not_runtime_or_duration_validation', 'sourceCommit':data['sourceCommit'],
            'ruleCount':len(data['rules']),'onboardingRules':8,'normalAndFinalRules':42,
            'minimumCenterPoolCumulative':counts,'routeChecks':seeds*4,'seedRange':[0,seeds-1],
            'variants':{'openingBusiness':['farm','fish_market'],'collectBeforeUpgrade':['minimum_requirement','fill_cap']},
            'allRoutesReached50':True,'allRoutesEndedWithCAT050':True,'centerCapacityWitness':trace,
            'oneWitnessOrder':order,'assumptions':['Buildings allowed by current center are eventually constructed/upgraded','Finite gold costs and positive base support are not simulated','Mastery may accumulate on distinct assigned residents with enough time','One rescue at a time; successful interaction/care completion is assumed','No clock, weather, ad, relationship or visible-NPC conditions'],
            'notValidated':['Full pacing with split grants and these discovery conditions','Engine rendering, scene fun, movement and art','Real crash-safe storage/ad SDK','All arbitrary purchase/assignment sequences','Exact normal search/care times and hint UI translation'],
            'unchanged':['50 cat IDs, names, base stats and art definitions','Building/center caps, economy costs, onboarding grants']}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--snapshot',action='store_true');parser.add_argument('--seeds',type=int,default=100);parser.add_argument('--output',default='reports/discovery_validation_v01.json');args=parser.parse_args()
    if args.seeds<1:parser.error('seeds must be positive')
    source=load_json(ROOT/'reports/discovery_source_projection.json') if args.snapshot else project(ROOT)
    data=load_json(ROOT/'data/discovery_rules.json')
    try: result=report(data,source,args.seeds)
    except (KeyError,ValueError,AssertionError,TypeError) as e:raise SystemExit('FAIL: '+str(e))
    result['inputMode']='pinned_projection' if args.snapshot else 'repository_data'
    out=ROOT/args.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: {result["ruleCount"]} rules, {result["routeChecks"]} structural routes. Report: {out}')
if __name__=='__main__':main()
