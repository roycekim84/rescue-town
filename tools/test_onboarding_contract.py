#!/usr/bin/env python3
"""First-session design contract tests; not engine/save/advertising SDK tests.
Default: current repository data. --snapshot: pinned calculation-field projection.
Python standard library only. Never writes game data.
"""
from __future__ import annotations
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = '--snapshot' in sys.argv
if SNAPSHOT:
    sys.argv.remove('--snapshot')


def read(name):
    if SNAPSHOT:
        return json.loads((ROOT/'reports/onboarding_source_projection.json').read_text(encoding='utf-8'))['files'][name]
    return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))


CONFIG = json.loads((ROOT/'data/onboarding.json').read_text(encoding='utf-8'))
ECON = read('economy_balance.json')
BUILDINGS = {b['id']: b for b in read('buildings.json')['buildings']}
PROGRESSION = {p['level']: p for p in read('progression.json')['levels']}
CATS = {c['catalogId']: c for c in read('cats.json')}
DEV = read('development_score.json')


def state():
    return {'walletGold': ECON['wallet']['initialGold'],
            'claimed_grant_ids': [ECON['wallet']['initialGrantClaimKey']],
            'buildingLevels': {'rescue_center': 1},
            'historical_assignment_buildings': []}


def eligible(s, condition):
    kind = condition['kind']
    if kind == 'building_level':
        return s['buildingLevels'].get(condition['id'], 0) >= condition['gte']
    if kind == 'assignment_ever':
        return condition['id'] in s['historical_assignment_buildings']
    raise ValueError(f'Unsupported predicate: {kind}')


def reconcile(s):
    """Pure reference reducer. Real durable atomic persistence is still required."""
    result = deepcopy(s)
    for grant in CONFIG['grants']:
        if grant['id'] not in result['claimed_grant_ids'] and all(eligible(result, c) for c in grant['all']):
            result['walletGold'] += grant['amount']
            result['claimed_grant_ids'].append(grant['id'])
    return result


def route(choice):
    """One legal spending trace, ignoring support income and all advertising."""
    s = state()
    out = [('start', deepcopy(s))]
    operations = [('rescue_center', 2), ('assign', 0), ('rescue_center', 3),
                  ('housing', 1), ('park', 1), ('rescue_center', 4), (choice, 1)]
    for key, level in operations:
        if key == 'assign':
            s['historical_assignment_buildings'].append('rescue_center')
        else:
            cost = (ECON['centerUpgrade']['costGoldByTargetLevel'][level-1]
                    if key == 'rescue_center' else ECON['buildingEconomy'][key]['baseBuildCostGold'])
            if s['walletGold'] < cost:
                raise ValueError(f'Insufficient gold before {key}:{level}')
            s['walletGold'] -= cost
            s['buildingLevels'][key] = level
        s = reconcile(s)
        out.append((f'{key}:{level}', deepcopy(s)))
    return out


def offer_ads(first_business, seconds):
    return first_business and seconds >= CONFIG['adPolicy']['minimumForegroundGameplaySeconds']


class OnboardingContract(unittest.TestCase):
    def test_01_initial_support_is_not_5500_twice(self):
        i = CONFIG['economyIntegration']
        self.assertEqual(i['initialGold'], ECON['wallet']['initialGold'])
        self.assertEqual(i['initialClaimKey'], ECON['wallet']['initialGrantClaimKey'])
        self.assertTrue(i['initialGrantIsReferenceOnly'])
        self.assertFalse(i['applyInitial5500ExperimentAlso'])

    def test_02_bonus_total(self):
        self.assertEqual(sum(g['amount'] for g in CONFIG['grants']), 4500)
        self.assertEqual(ECON['wallet']['initialGold'] + 4500, CONFIG['economyIntegration']['totalOneTimeSupport'])

    def test_03_grant_ids_unique(self):
        ids = [g['id'] for g in CONFIG['grants']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn(ECON['wallet']['initialGrantClaimKey'], ids)

    def test_04_unearned_bonus_not_paid(self):
        self.assertEqual(reconcile(state()), state())
        s = state(); s['buildingLevels']['rescue_center'] = 2
        self.assertEqual(reconcile(s)['walletGold'], 1000)

    def test_05_repeated_reconcile_no_duplicate(self):
        s = route('farm')[-1][1]
        for _ in range(10):
            s = reconcile(s)
        self.assertEqual(s['walletGold'], 600)
        self.assertEqual(len(s['claimed_grant_ids']), 4)

    def test_06_checkpoint_roundtrip(self):
        for choice in CONFIG['firstBusiness']['choices']:
            for _, s in route(choice):
                restored = json.loads(json.dumps(s))
                self.assertEqual(reconcile(restored), s)

    def test_07_missing_milestone_event_reconciles(self):
        s = state(); s['buildingLevels'].update(rescue_center=4, housing=1, park=1)
        s['historical_assignment_buildings'] = ['rescue_center']
        self.assertEqual(reconcile(s)['walletGold'], 5500)

    def test_08_assignment_history_not_current_job(self):
        s = route('farm')[2][1]
        self.assertIn('rescue_center', s['historical_assignment_buildings'])
        self.assertEqual(reconcile(s), s)

    def test_09_farm_route_no_passive_income(self):
        trace = route('farm')
        self.assertEqual(trace[-1][1]['walletGold'], 600)
        self.assertTrue(all(s['walletGold'] >= 0 for _, s in trace))

    def test_10_fish_route_no_passive_income(self):
        trace = route('fish_market')
        self.assertEqual(trace[-1][1]['walletGold'], 400)
        self.assertTrue(all(s['walletGold'] >= 0 for _, s in trace))

    def test_11_center_requirements(self):
        for level, count in [(2,3),(3,5),(4,8)]:
            self.assertEqual(PROGRESSION[level]['upgradeRequirements']['residentCount'], count)
            self.assertLessEqual(count, PROGRESSION[level-1]['cap'])

    def test_12_development_before_center4(self):
        two_buildings = 2 * DEV['awards']['buildingConstruction']['lv5MaxBuilding']
        self.assertEqual(two_buildings, 100)
        self.assertGreaterEqual(two_buildings, PROGRESSION[4]['upgradeRequirements']['villageDevelopment'])
        self.assertEqual(PROGRESSION[3]['upgradeRequirements']['villageDevelopment'], 0)

    def test_13_roster_and_chain(self):
        rescues = CONFIG['firstRescues']
        self.assertEqual([r['catalogId'] for r in rescues], [f'CAT_{i:03}' for i in range(1,9)])
        for index, r in enumerate(rescues):
            self.assertGreaterEqual(r['center'], CATS[r['catalogId']]['discovery']['minimumCenterLevel'])
            self.assertEqual(r['after'], rescues[index-1]['catalogId'] if index else None)

    def test_14_no_future_building_dependency(self):
        for rescue in CONFIG['firstRescues']:
            for bid, lvl in rescue['requiresBuildings'].items():
                self.assertLessEqual(BUILDINGS[bid]['unlock'], rescue['center'])
                self.assertLessEqual(lvl, min(rescue['center'], BUILDINGS[bid]['maxLevel']))
        self.assertNotIn('farm', CONFIG['firstRescues'][6]['requiresBuildings'])
        self.assertNotIn('cafe', CONFIG['firstRescues'][4]['requiresBuildings'])

    def test_15_reserved_capacity(self):
        for index, rescue in enumerate(CONFIG['firstRescues']):
            self.assertLessEqual(index + 1, PROGRESSION[rescue['center']]['cap'])
        self.assertTrue(CONFIG['rescueRules']['capacityIncludesReservedAndCarePending'])
        self.assertFalse(CONFIG['rescueRules']['spawningGrantsResident'])

    def test_16_ad_gate_both_conditions(self):
        self.assertFalse(offer_ads(False, 9999))
        self.assertFalse(offer_ads(True, 1199))
        self.assertTrue(offer_ads(True, 1200))
        self.assertFalse(CONFIG['adPolicy']['rewardsRequired'])
        self.assertTrue(CONFIG['adPolicy']['eligibleOfflineBaseAlwaysGranted'])

    def test_17_sequence_unique_and_no_deadline(self):
        ids = [s['id'] for s in CONFIG['steps']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(CONFIG['target']['deadline'])
        self.assertEqual(CONFIG['steps'][-1]['targetMinutes'][-1], 30)

    def test_18_rescue_timers_and_completion(self):
        self.assertTrue(all(0 <= r['searchSeconds'] <= 60 and 0 < r['careSeconds'] <= 90 for r in CONFIG['firstRescues']))
        self.assertTrue(CONFIG['rescueRules']['temporaryLodgingCounts'])
        self.assertFalse(CONFIG['rescueRules']['optionalAnimationIsProgressGate'])
        self.assertFalse(CONFIG['rescueRules']['nextRescueAutoStartsOffline'])
        self.assertTrue(CONFIG['firstBusiness']['noScriptedIncomeGrant'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
