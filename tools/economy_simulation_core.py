#!/usr/bin/env python3
"""Shared numeric economy model for an offline design simulation. Not game runtime.

Run: python3 tools/simulate_progression.py --output reports/progression_simulation_v01.json
Only standard library. Reads repository data; never rewrites canonical balance.
Derived from the prior attached v0.1 calculator; integrated runner supplies actual discovery rules.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
from collections import Counter
from pathlib import Path

EPS = 1e-8


def load(root: Path, name: str):
    return json.loads((root / 'data' / name).read_text(encoding='utf-8'))


def mastery(minutes: float, curve: list) -> float:
    for (lo, start), (hi, end) in zip(curve, curve[1:]):
        if minutes <= end:
            return lo + (hi - lo) * max(0, minutes - start) / (end - start)
    return float(curve[-1][0])


def development(levels: dict, buildings: dict, awards: dict) -> int:
    total = 0
    for bid, level in levels.items():
        if bid == 'rescue_center' or level == 0:
            continue
        kind = f"lv{buildings[bid]['maxLevel']}MaxBuilding"
        bonus = awards.get({'park': 'parkUpgradeBonusPerLevel',
                            'town_square': 'townSquareUpgradeBonusPerLevel'}.get(bid, ''), 0)
        total += awards['buildingConstruction'][kind]
        total += (level - 1) * (awards['buildingUpgrade'][kind + 'PerLevel'] + bonus)
    return total


class EconomyCore:
    def __init__(self, inputs, settings, case):
        self.cfg = copy.deepcopy(settings['model'])
        self.case = copy.deepcopy(case)
        self.e = copy.deepcopy(inputs['economy_balance'])
        self.b = {b['id']: b for b in inputs['buildings']['buildings']}
        self.cats = sorted(inputs['cats'], key=lambda c: c['catalogId'])
        self.p = inputs['progression']
        self.awards = inputs['development_score']['awards']
        self.t = 0.0
        self.levels = dict.fromkeys(self.b, 0); self.levels['rescue_center'] = 1
        self.gold = float(self.e['wallet']['initialGold'])
        self.residents = {}; self.jobs = {}; self.search = None
        self.last_logout = 0.0; self.offline_bank = 0.0; self.boost_left = 0.0
        self.logs = [{'minute':0.0, 'event':'center', 'value':1}]
        self.ads = Counter(); self.earned = Counter(); self.spent = 0.0
        self.snapshots = {}; self.first_cash = None; self.festival = None
        self.economic_ready = None; self.collection = None; self.waiting = Counter()
        self.max_occupancy = 0

    @property
    def center(self):
        return self.levels['rescue_center']

    def slots(self, bid):
        return max([int(n) for lev, n in self.b[bid]['staff'].items()
                    if int(lev) <= self.levels[bid]] or [0])

    def factor(self, bid, level=None):
        lev = self.levels[bid] if level is None else level
        return self.e['levelCurves'][str(self.b[bid]['maxLevel'])]['output'][lev-1] if lev else 0

    def efficiency(self, r, bid):
        z = self.e['staff']['efficiency']
        ability = z['primaryWeight'] * r['abilities'][self.b[bid]['primary']]
        ability += z['secondaryWeight'] * r['abilities'][self.b[bid]['secondary']]
        m = mastery(r['work'].get(bid, 0), self.e['growth']['masteryCurve'])
        return z['constant'] + z['abilityCoefficient'] * ability + z['masteryCoefficient'] * m

    def assign(self):
        # Stable assignments: do not erase prior careers by globally reshuffling every tick.
        desired = {}
        for bid in self.b:
            slots = self.slots(bid)
            if bid == 'rescue_center':
                slots = min(slots, self.cfg['careWorkersReserved'])
            elif self.e['buildingEconomy'][bid]['baseGoldPerMinute'] == 0:
                slots = min(slots, self.cfg['cashlessServiceWorkers'])
            desired[bid] = slots
        for layer in range(1, 4):
            order = sorted(self.b, key=lambda bid: (bid != 'rescue_center',
                           -self.e['buildingEconomy'][bid]['baseGoldPerMinute'], bid))
            for bid in order:
                have = sum(r['job'] == bid for r in self.residents.values())
                if desired[bid] < layer or have >= layer:
                    continue
                free = [(cid, r) for cid, r in self.residents.items() if r['job'] is None]
                if free:
                    cid, resident = max(free, key=lambda pair: (self.efficiency(pair[1], bid), pair[0]))
                    resident['job'] = bid

    def rates(self):
        factors = {}
        grouped = {bid: [] for bid in self.b}
        for r in self.residents.values():
            if r['job'] is not None:
                grouped[r['job']].append(r)
        for bid in self.b:
            workers = sorted([self.efficiency(r, bid) for r in grouped[bid]], reverse=True)
            staff = sum(w * x for w, x in zip(self.e['staff']['slotWeights'], workers))
            factors[bid] = self.factor(bid) * staff
        supply = self.e['supply']
        coverage = {}
        for provider, data in supply['providers'].items():
            demand = sum(parts.get(provider, 0) * factors[consumer]
                         for consumer, parts in supply['consumers'].items())
            coverage[provider] = min(1.0, data['baseUnitsPerMinute'] * factors[provider] / demand) if demand else 1.0
        income = 0.0
        for bid, data in self.e['buildingEconomy'].items():
            multiplier = 1.0
            if bid in supply['consumers']:
                parts = supply['consumers'][bid]
                fraction = sum(weight * coverage[p] for p, weight in parts.items()) / sum(parts.values())
                multiplier = supply['missingSupplyMultiplier'] + (supply['fullSupplyMultiplier'] - supply['missingSupplyMultiplier']) * fraction
            income += data['baseGoldPerMinute'] * factors[bid] * multiplier
        return income, self.e['wallet']['baseSupportGoldPerMinute']

    def cost_time(self, bid):
        target = self.levels[bid] + 1
        if bid == 'rescue_center':
            c = self.e['centerUpgrade']
            return c['costGoldByTargetLevel'][target-1], c['durationSecondsByTargetLevel'][target-1] / 60
        curve = self.e['levelCurves'][str(self.b[bid]['maxLevel'])]
        rounding = self.e['construction']['costRoundUpToGold']
        cost = self.e['buildingEconomy'][bid]['baseBuildCostGold'] * curve['cost'][target-1]
        return math.ceil(cost / rounding) * rounding, curve['durationSeconds'][target-1] / 60

    def center_gates(self):
        if self.center == 10:
            return []
        req = self.p['levels'][self.center]['upgradeRequirements']
        gates = []
        if len(self.residents) < req['residentCount']:
            gates.append('residents')
        if development(self.levels, self.b, self.awards) < req['villageDevelopment']:
            gates.append('development')
        m = req['jobMastery']
        if m:
            count = sum(any(mastery(v, self.e['growth']['masteryCurve']) >= m['threshold'] - EPS
                            for v in r['work'].values()) for r in self.residents.values())
            if count < m['count']:
                gates.append('mastery')
        if self.gold + EPS < self.cost_time('rescue_center')[0]:
            gates.append('gold')
        return gates

    def start(self, bid):
        cost, minutes = self.cost_time(bid)
        if self.gold + EPS < cost or bid in self.jobs:
            raise ValueError('Invalid spending/job')
        self.gold -= cost
        self.spent += cost
        self.jobs[bid] = {'target': self.levels[bid]+1, 'end': self.t+minutes, 'ads': 0}
        self.logs.append({'minute': round(self.t, 4), 'event': 'purchase', 'building': bid,
                          'target': self.levels[bid]+1, 'gold': cost})

    def advance(self, target, foreground, ad=False):
        while self.t < target - EPS:
            step = self.cfg['onlineStepMinutes'] if foreground else self.cfg['offlineStepMinutes']
            end = min(target, self.t+step)
            if not foreground and self.t >= self.last_logout + self.e['offline']['maxCreditedSeconds']/60 - EPS:
                end = target
                for day in self.cfg['snapshotsDays']:
                    if self.t + EPS < day*1440 < end:
                        end = day*1440
            for job in self.jobs.values():
                if job['end'] > self.t + EPS:
                    end = min(end, job['end'])
            credit_end = self.last_logout + self.e['offline']['maxCreditedSeconds']/60
            if not foreground and self.t < credit_end - EPS:
                end = min(end, credit_end)
            if foreground and not ad and self.boost_left > EPS:
                end = min(end, self.t+self.boost_left)
            end = self.interval_boundary(end, foreground, ad)
            minutes = end-self.t
            if minutes <= EPS: raise ValueError('Non-positive integration interval')
            credited = foreground or self.t < credit_end-EPS
            cash, support = self.rates()
            if credited:
                organic = (cash+support)*minutes
                if not foreground:
                    organic *= self.e['offline']['organicIncomeMultiplier']
                    self.offline_bank += organic
                self.gold += organic
                self.earned['organic'] += organic
                if foreground and not ad and self.boost_left > EPS:
                    extra = cash*(self.e['ads']['incomeBoost']['goldMultiplier']-1)*minutes
                    self.gold += extra
                    self.earned['boost'] += extra
                    self.boost_left = max(0, self.boost_left-minutes)
                g = self.e['growth']
                for r in self.residents.values():
                    bid = r['job']
                    if bid is None:
                        continue
                    r['work'][bid] = r['work'].get(bid, 0)+minutes
                    for key, fraction in [('primary','primaryXpFraction'),('secondary','secondaryXpFraction')]:
                        ability = self.b[bid][key]
                        r['xp'][ability] += minutes*g['abilityXpPerWorkMinute']*g[fraction]
                        while r['abilities'][ability] < g['abilityMax']:
                            needed = 10*r['abilities'][ability]**2
                            if r['xp'][ability]+EPS < needed:
                                break
                            r['xp'][ability] -= needed
                            r['abilities'][ability] += 1
                        if r['abilities'][ability] == g['abilityMax']:
                            r['xp'][ability] = 0.0
            self.interval_record(minutes, foreground, ad, cash, support, credited)
            if self.center < 10 and 'rescue_center' not in self.jobs:
                for gate in self.center_gates():
                    self.waiting[f'L{self.center}:{gate}'] += minutes
            self.t = end
            self.settle_events(foreground and not ad)
            if self.gold < -EPS:
                raise ValueError('Negative gold')
            for day in self.cfg['snapshotsDays']:
                if day not in self.snapshots and self.t >= day*1440-EPS:
                    self.snapshots[day] = self.snapshot()

