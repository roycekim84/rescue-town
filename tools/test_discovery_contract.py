#!/usr/bin/env python3
"""Tests of a pure discovery reference reducer, not engine or disk atomicity."""
import copy
import json
import sys
import unittest
import validate_discovery as v
SNAPSHOT='--snapshot' in sys.argv
if SNAPSHOT:sys.argv.remove('--snapshot')
class DiscoveryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=v.load_json(v.ROOT/'reports/discovery_source_projection.json') if SNAPSHOT else v.project(v.ROOT)
        cls.data=v.load_json(v.ROOT/'data/discovery_rules.json')
    def late(self,count=49,center=10):
        s=v.empty_state();s['levels']={b['id']:min(center,b['maxLevel']) for b in self.source['buildings'] if b['unlock']<=center};s['owned']=v.CAT_IDS[:count];s['flags']=['first_business_started'];s['development']=v.score(s['levels'],self.source);return s
    def test_01_contract(self):self.assertTrue(v.check_contract(self.data,self.source))
    def test_02_id_count(self):self.assertEqual([r['catalogId'] for r in self.data['rules']],v.CAT_IDS)
    def test_03_duplicate_rejected(self):
        d=copy.deepcopy(self.data);d['rules'][-1]['catalogId']='CAT_001'
        with self.assertRaises(ValueError):v.check_contract(d,self.source)
    def test_04_future_building_in_onboarding_rejected(self):
        d=copy.deepcopy(self.data);d['rules'][5]['eligibility']['all'].append({'kind':'building_level','id':'farm','gte':1})
        with self.assertRaises(ValueError):v.check_contract(d,self.source)
    def test_05_unknown_building_rejected(self):
        d=copy.deepcopy(self.data);d['rules'][8]['eligibility']['all'].append({'kind':'building_level','id':'unknown','gte':1})
        with self.assertRaises(ValueError):v.check_contract(d,self.source)
    def test_06_impossible_building_level_rejected(self):
        d=copy.deepcopy(self.data);d['rules'][8]['eligibility']['all'].append({'kind':'building_level','id':'park','gte':6})
        with self.assertRaises(ValueError):v.check_contract(d,self.source)
    def test_07_weather_cannot_be_hard_gate(self):
        d=copy.deepcopy(self.data);d['rules'][43]['eligibility']['all'].append({'kind':'weather','id':'rain'})
        with self.assertRaises(ValueError):v.check_contract(d,self.source)
    def test_08_final_cannot_require_festival(self):
        d=copy.deepcopy(self.data);d['rules'][49]['eligibility']['all'].append({'kind':'flag','id':'festival_complete'})
        with self.assertRaises(ValueError):v.check_contract(d,self.source)
    def test_09_exact_onboarding_order(self):
        s=v.empty_state()
        for f in self.source['onboarding']['firstRescues']:
            s['levels']['rescue_center']=f['center'];s['levels'].update(f['requiresBuildings'])
            cap=self.source['progression']['levels'][f['center']-1]['cap'];self.assertEqual(v.eligible(self.data,s,cap),[f['catalogId']])
            s=v.reserve(self.data,s,f['catalogId'],cap);s=v.advance(s,'scene_ready');s=v.advance(s,'care_pending');s=v.settle(s,f['catalogId'])
    def test_10_normal_waits_for_first_business(self):
        s=self.late(8,4);s['flags']=[];self.assertEqual(v.eligible(self.data,s,12),[])
    def test_11_no_farm_dependency_for_bori(self):
        r=self.data['rules'][6];self.assertFalse(any(x.get('id')=='farm' for x in v.walk(r['eligibility'])))
    def test_12_final_needs_49(self):
        s=self.late(48);self.assertNotIn('CAT_050',v.eligible(self.data,s,50));s['owned'].append('CAT_049');self.assertIn('CAT_050',v.eligible(self.data,s,50))
    def test_13_final_needs_center10(self):
        s=self.late(49,9);self.assertFalse(v.match(self.data['rules'][-1]['eligibility'],s))
    def test_14_capacity_full(self):self.assertEqual(v.eligible(self.data,self.late(50),50),[])
    def test_15_reserved_slot_blocks_second_job(self):
        s=v.reserve(self.data,self.late(48),'CAT_049',50);self.assertEqual(v.eligible(self.data,s,50),[])
        with self.assertRaises(ValueError):v.reserve(self.data,s,'CAT_050',50)
    def test_16_reservation_idempotent_and_same_identity(self):
        s=v.reserve(self.data,self.late(49),'CAT_050',50);self.assertEqual(v.reserve(self.data,s,'CAT_050',50),s)
        t=v.advance(s,'scene_ready');self.assertEqual(t['job']['residentId'],s['job']['residentId'])
    def test_17_care_not_counted_as_settled(self):
        s=v.reserve(self.data,self.late(49),'CAT_050',50);s=v.advance(v.advance(s,'scene_ready'),'care_pending');self.assertEqual(len(s['owned']),49);self.assertEqual(len(v.settle(s,'CAT_050')['owned']),50)
    def test_18_no_settle_before_care(self):
        s=v.reserve(self.data,self.late(49),'CAT_050',50)
        with self.assertRaises(ValueError):v.settle(s,'CAT_050')
    def test_19_duplicate_settlement_no_new_resident(self):
        s=v.reserve(self.data,self.late(49),'CAT_050',50);s=v.advance(v.advance(s,'scene_ready'),'care_pending');s=v.settle(s,'CAT_050');self.assertEqual(v.settle(s,'CAT_050'),s)
    def test_20_checkpoint_roundtrip(self):
        s=v.reserve(self.data,self.late(49),'CAT_050',50);s=v.advance(s,'scene_ready');s=json.loads(json.dumps(s));s=v.advance(s,'care_pending');s=v.settle(s,'CAT_050');self.assertEqual(s['owned'],v.CAT_IDS)
    def test_21_context_not_gate(self):
        s=self.late(8);a=v.eligible(self.data,s,50);s.update({'weather':'clear','gamePhase':'morning','visibleResidents':[],'adsViewed':0,'relationships':{}});self.assertEqual(a,v.eligible(self.data,s,50))
    def test_22_bakery_condition_changes_candidates(self):
        s=self.late(8,9);del s['levels']['bakery'];self.assertNotIn('CAT_042',v.eligible(self.data,s,44));s['levels']['bakery']=1;self.assertIn('CAT_042',v.eligible(self.data,s,44))
    def test_23_danbi_fallback(self):
        s=self.late(35,9);del s['levels']['town_square'];s['levels']['cafe']=3;self.assertIn('CAT_044',v.eligible(self.data,s,44))
    def test_24_impossible_population_mutation_blocks_route(self):
        d=copy.deepcopy(self.data)
        for r in d['rules'][8:14]:r['eligibility']['all'].append({'kind':'resident_count','gte':49})
        with self.assertRaises(ValueError):v.structural_route(d,self.source)
    def test_25_all_400_routes(self):
        for seed in range(100):
            for b in ['farm','fish_market']:
                for fill in [False,True]:
                    _,order=v.structural_route(self.data,self.source,seed,b,fill);self.assertEqual(order[-1],'CAT_050');self.assertEqual(set(order),set(v.CAT_IDS))
    def test_26_no_all_max_required_witness(self):
        s=self.late();s['levels']={b['id']:(10 if b['id']=='rescue_center' else 7 if b['id']=='farm' else 5) for b in self.source['buildings']};s['development']=v.score(s['levels'],self.source)
        self.assertGreaterEqual(s['development'],self.source['progression']['ending']['requires']['villageDevelopment'])
        self.assertTrue(all(v.match(r['eligibility'],s) for r in self.data['rules'][8:]));self.assertLess(s['levels']['cafe'],10)
    def test_27_50th_not_automatically_settled(self):
        s=self.late(49);self.assertIn('CAT_050',v.eligible(self.data,s,50));self.assertEqual(len(s['owned']),49)
    def test_28_unknown_condition_rejected(self):
        with self.assertRaises(ValueError):v.match({'kind':'arbitrary_script','id':'something'},v.empty_state())
if __name__=='__main__':unittest.main(verbosity=2)
