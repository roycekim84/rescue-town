#!/usr/bin/env python3
"""Integrated planning-model tests. Never a claim of game/SDK/crash safety."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path
from simulate_integrated_progression import IntegratedSimulation, load_inputs, read, validate_inputs
from economy_simulation_core import development, mastery
from validate_discovery import match
ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT='--snapshot' in sys.argv
if SNAPSHOT:sys.argv.remove('--snapshot')
INPUTS,PROVENANCE=load_inputs(ROOT,SNAPSHOT)
SETTINGS=read(ROOT/'data/integrated_simulation_scenarios.json')
TIMING=read(ROOT/'data/rescue_timing.json')

def model(**overrides):
    case={'id':'test','sessionsPerDay':2,'rewarded':False,**overrides}
    return IntegratedSimulation(copy.deepcopy(INPUTS),copy.deepcopy(SETTINGS),case,copy.deepcopy(TIMING))

def add_residents(s,n):
    for c in s.cats[:n]:
        s.residents[c['catalogId']]={'abilities':dict(c['baseAbilities']),'xp':dict.fromkeys(c['baseAbilities'],0.),'work':{},'job':None}

class Contracts(unittest.TestCase):
    def test_01_input_contract(self):validate_inputs(INPUTS,TIMING,SETTINGS)
    def test_02_initial_grant_only_1000(self):self.assertEqual(model().gold,1000)
    def test_03_support_requires_assignment(self):
        s=model();s.levels['rescue_center']=2;s.award_grants();self.assertEqual(s.gold,1000)
    def test_04_assignment_support_once(self):
        s=model();s.levels['rescue_center']=2;s.ever_assigned.add('rescue_center');s.award_grants();s.award_grants();self.assertEqual(s.gold,1600)
    def test_05_total_support_not10000(self):
        s=model();s.levels.update(rescue_center=4,housing=1,park=1);s.ever_assigned.add('rescue_center');s.award_grants();s.award_grants();self.assertEqual(s.gold,5500)
    def test_06_grant_checkpoint_reference(self):
        s=model();s.levels.update(rescue_center=4,housing=1,park=1);s.ever_assigned.add('rescue_center');s.award_grants()
        state=json.loads(json.dumps({'gold':s.gold,'claims':list(s.claimed)}));t=model();t.levels=dict(s.levels);t.ever_assigned=set(s.ever_assigned);t.gold=state['gold'];t.claimed=set(state['claims']);t.award_grants();self.assertEqual(t.gold,s.gold)
    def test_07_first_business_excludes_support(self):
        s=model();s.advance(10,True);self.assertNotIn('first_business_started',s.flags)
    def test_08_first_business_requires_one_gold(self):
        s=model();s.interval_record(.5,True,False,1,100,True);self.assertNotIn('first_business_started',s.flags)
        s.interval_record(.5,True,False,1,100,True);self.assertIn('first_business_started',s.flags)
    def test_09_ads_require_both_facts(self):
        s=model(rewarded=True);s.active_minutes=30;self.assertFalse(s.ad_allowed('offline'));s.flags.add('first_business_started');s.active_minutes=19.9;self.assertFalse(s.ad_allowed('offline'));s.active_minutes=20;self.assertTrue(s.ad_allowed('offline'))
    def test_10_no_ad_experience_multiplier(self):
        s=model();s.levels['rescue_center']=2;add_residents(s,1);s.assign();s.advance(1,True,ad=True);self.assertAlmostEqual(s.residents['CAT_001']['work']['rescue_center'],1);self.assertEqual(s.active_minutes,0)
    def test_11_no_boost_during_ad(self):
        s=model();s.boost_left=5;s.advance(1,True,ad=True);self.assertEqual(s.boost_left,5)
    def test_12_offline_eight_hour_cap(self):
        s=model();s.advance(720,False);self.assertAlmostEqual(s.gold,1960)
    def test_13_old_building_remains_during_upgrade(self):
        s=model();s.levels.update(rescue_center=4,farm=1);s.gold=10000;s.start('farm');self.assertEqual(s.levels['farm'],1);s.advance(s.jobs['farm']['end'],False);self.assertEqual(s.levels['farm'],2)
    def test_14_core_staff_max_three(self):
        s=model();s.levels={b:min(10,d['maxLevel']) for b,d in s.b.items()};add_residents(s,50);s.assign();self.assertTrue(all(sum(r['job']==b for r in s.residents.values())<=3 for b in s.b))
    def test_15_first_eight_order(self):
        s=model();self.assertEqual(s.choices(),['CAT_001']);add_residents(s,1);self.assertEqual(s.choices(),['CAT_002'])
    def test_16_no_future_farm_for_bori(self):
        s=model();s.levels['rescue_center']=3;add_residents(s,6);self.assertEqual(s.choices(),['CAT_007'])
    def test_17_normal_requires_first_business(self):
        s=model();s.levels['rescue_center']=4;add_residents(s,8);self.assertEqual(s.choices(),[])
    def test_18_oreo_requires_bakery(self):
        s=model();s.levels['rescue_center']=9;s.flags.add('first_business_started');add_residents(s,8);self.assertNotIn('CAT_042',s.choices());s.levels['bakery']=1;self.assertIn('CAT_042',s.choices())
    def test_19_capacity_includes_pending(self):
        s=model();s.levels['rescue_center']=4;s.flags.add('first_business_started');add_residents(s,11);s.act_rescue();self.assertEqual(s.choices(),[]);s.settle_events(False);self.assertEqual(s.max_occupancy,12)
    def test_20_final49_not_festival(self):
        s=model();s.levels['rescue_center']=10;s.flags.add('first_business_started');add_residents(s,48);self.assertNotIn('CAT_050',s.choices());add_residents(s,49);self.assertIn('CAT_050',s.choices())
    def test_21_no_offline_scene_auto_rescue(self):
        s=model();s.act_rescue();s.advance(720,False);self.assertEqual(s.search['phase'],'scene_ready');self.assertEqual(len(s.residents),0)
    def test_22_no_offline_scene_interaction(self):
        s=model();s.act_rescue();s.settle_events(True);s.act_rescue();rem=s.search['remaining'];s.advance(60,False);self.assertEqual(s.search['remaining'],rem)
    def test_23_offline_care_keeps_result(self):
        s=model();s.search={'id':'CAT_001','phase':'care_pending','end':1,'remaining':0,'ads':0};s.advance(720,False);self.assertEqual(s.search['phase'],'care_ready');self.assertNotIn('CAT_001',s.residents)
    def test_24_settlement_no_duplicate(self):
        s=model();s.search={'id':'CAT_001','phase':'care_ready','end':math.inf,'remaining':0,'ads':0};s.act_rescue();s.settle_events(True);s.settle_events(True);self.assertEqual(list(s.residents),['CAT_001'])
    def test_25_timer_uses_catalog_tier(self):
        s=model();s.levels.update(rescue_center=10,park=1);s.flags.add('first_business_started');add_residents(s,8);s.act_rescue();self.assertEqual(s.search['id'],'CAT_009');self.assertEqual(s.search['end'],3)
    def test_26_center_care_helps_without_ad(self):
        s=model();self.assertEqual(s.care_rate(),1);s.levels['rescue_center']=8;add_residents(s,1);s.assign();self.assertGreater(s.care_rate(),1)
    def test_27_any_condition_not_all(self):
        s=model();s.levels.update(rescue_center=9,cafe=3);s.flags.add('first_business_started');add_residents(s,35);self.assertIn('CAT_044',s.choices())
    def test_28_future_building_not_legal_plan(self):
        s=model();s.levels['rescue_center']=4;self.assertEqual(s.plans({'kind':'building_level','id':'bakery','gte':1}),[])
    def test_29_growth_keeps_job_history(self):
        s=model();s.levels.update(rescue_center=4,farm=1);add_residents(s,1);r=s.residents['CAT_001'];r['job']='rescue_center';s.advance(1,True);r['job']='farm';s.advance(2,True);self.assertAlmostEqual(r['work']['rescue_center'],1);self.assertAlmostEqual(r['work']['farm'],1)
    def test_30_mastery_curve(self):
        for m,t in INPUTS['economy_balance']['growth']['masteryCurve']:self.assertAlmostEqual(mastery(t,INPUTS['economy_balance']['growth']['masteryCurve']),m)
    def test_31_final_zero_search_and_care(self):
        s=model();s.levels['rescue_center']=10;s.flags.add('first_business_started');add_residents(s,49);s.act_rescue();self.assertEqual(s.search['id'],'CAT_050');self.assertEqual(s.search['end'],s.t)
    def test_32_cost_sensitivity_no_input_mutation(self):
        s=model(centerCostMultipliers={'10':.75});self.assertEqual(s.e['centerUpgrade']['costGoldByTargetLevel'][9],2400000);self.assertEqual(INPUTS['economy_balance']['centerUpgrade']['costGoldByTargetLevel'][9],3200000)

class SavedRunChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'reports/integrated_progression_v02.json'
        if not path.exists():raise unittest.SkipTest('Run integrated simulation with --include-events first')
        cls.runs=read(path)['results']
    def test_33_runs_end_50_final_last(self):
        for r in self.runs:
            self.assertEqual(r['final']['residents'],50);self.assertIsNotNone(r['festivalConditionsDay']);self.assertEqual([e for e in r['events'] if e['event']=='resident'][-1]['id'],'CAT_050')
    def test_34_wallet_conservation(self):
        for r in self.runs:self.assertAlmostEqual(r['final']['gold'],1000+sum(r['earnedGold'].values())-r['spentGold'],places=1)
    def test_35_support4500_once(self):
        for r in self.runs:
            self.assertEqual(r['earnedGold']['milestoneSupport'],4500);self.assertEqual(len([e for e in r['events'] if e['event']=='grant']),3)
    def test_36_onboarding_before_optional_purchases(self):
        for r in self.runs:
            first=r['firstBusinessMinutes'];allowed={('rescue_center',2),('rescue_center',3),('rescue_center',4),('housing',1),('park',1),(r['case'].get('openingBusiness','farm'),1)}
            for e in r['events']:
                if e['event']=='purchase' and e['minute']<first:self.assertIn((e['building'],e['target']),allowed)
    def test_37_replay_every_reservation_condition(self):
        for r in self.runs:
            if r['case'].get('discoveryGateAblation'):continue
            s=model();owned=[];pending=None;flags=[];levels=dict(s.levels)
            for e in r['events']:
                if e['event']=='center':levels['rescue_center']=e['value']
                elif e['event']=='building':levels[e['building']]=e['value']
                elif e['event']=='first_business':flags=['first_business_started']
                elif e['event']=='reserve':
                    self.assertIsNone(pending);pending=e['id'];self.assertNotIn(pending,owned)
                    state={'levels':levels,'owned':owned,'flags':flags,'development':development(levels,s.b,s.awards)}
                    self.assertTrue(match(s.rules[pending]['eligibility'],state),(r['case']['id'],e))
                    self.assertLessEqual(len(owned)+1,s.p['levels'][levels['rescue_center']-1]['cap'])
                elif e['event']=='resident':self.assertEqual(e['id'],pending);owned.append(pending);pending=None
    def test_38_no_early_ad(self):
        for r in self.runs:
            for e in r['events']:
                if e['event']=='ad':self.assertGreaterEqual(e['minute'],max(20,r['firstBusinessMinutes']))

if __name__=='__main__':unittest.main(verbosity=2)
