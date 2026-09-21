#!/usr/bin/env python3
"""Validate Rescue Town's draft economy. Standard-library only; NOT a game playtest."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

ABILITIES = {"care", "social", "focus", "activity", "sense"}

def load(root: Path, name: str):
    return json.loads((root / "data" / name).read_text(encoding="utf-8"))

def development(building: dict, level: int, rules: dict) -> int:
    if level <= 0 or building["id"] == "rescue_center":
        return 0
    a = rules["awards"]
    key = f'lv{building["maxLevel"]}MaxBuilding'
    bonus = {"park": a["parkUpgradeBonusPerLevel"],
             "town_square": a["townSquareUpgradeBonusPerLevel"]}.get(building["id"], 0)
    return a["buildingConstruction"][key] + (level - 1) * (
        a["buildingUpgrade"][key + "PerLevel"] + bonus)

def efficiency(primary: float, secondary: float, mastery: float, eco: dict) -> float:
    e = eco["staff"]["efficiency"]
    return e["constant"] + e["abilityCoefficient"] * (
        e["primaryWeight"] * primary + e["secondaryWeight"] * secondary
    ) + e["masteryCoefficient"] * mastery

def staff_factor(efficiencies: list[float], eco: dict) -> float:
    if len(efficiencies) > eco["staff"]["maximum"]:
        raise ValueError("More than three workers.")
    return sum(e * w for e, w in zip(sorted(efficiencies, reverse=True),
                                    eco["staff"]["slotWeights"]))

def building_rate(building: dict, level: int, efficiencies: list[float], eco: dict,
                  coverage: float = 0.0) -> float:
    if level == 0 or not efficiencies:
        return 0.0
    output = eco["levelCurves"][str(building["maxLevel"])]["output"][level - 1]
    m = eco["supply"]["missingSupplyMultiplier"]
    if building["id"] in eco["supply"]["consumers"]:
        m += (eco["supply"]["fullSupplyMultiplier"] - m) * max(0, min(1, coverage))
    return eco["buildingEconomy"][building["id"]]["baseGoldPerMinute"] * output * staff_factor(efficiencies, eco) * m

def offline_gold(rate: float, elapsed_seconds: float, eco: dict) -> float:
    seconds = max(0, min(elapsed_seconds, eco["offline"]["maxCreditedSeconds"]))
    return rate * seconds / 60 * eco["offline"]["organicIncomeMultiplier"]

def mastery_at(minutes: float, eco: dict) -> float:
    curve = eco["growth"]["masteryCurve"]
    if minutes <= 0:
        return 0
    for (ma, ta), (mb, tb) in zip(curve, curve[1:]):
        if minutes <= tb:
            return ma + (mb - ma) * (minutes - ta) / (tb - ta)
    return curve[-1][0]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        bdoc = load(args.root, "buildings.json")
        prog = load(args.root, "progression.json")
        dev = load(args.root, "development_score.json")
        eco = load(args.root, "economy_balance.json")
        buildings = bdoc["buildings"]
        by_id = {b["id"]: b for b in buildings}
        checks: list[str] = []

        def check(name: str, valid: bool) -> None:
            if not valid:
                raise ValueError(name)
            checks.append(name)

        check("13 unique building IDs", len(buildings) == len(by_id) == 13)
        check("economic entries match buildings", set(by_id) == set(eco["buildingEconomy"]))
        check("center levels 1..10", [r["level"] for r in prog["levels"]] == list(range(1, 11)))
        caps = [r["cap"] for r in prog["levels"]]
        check("monotonic caps end at 50", caps == sorted(caps) and caps[-1] == 50)
        check("development aggregation excludes repeat housing",
              dev["aggregation"] == "sum_score_of_highest_completed_level_per_building_type"
              and not dev["repeatHousingCopiesAddDevelopment"])
        for b in buildings:
            check(f'{b["id"]}: levels and abilities',
                  b["maxLevel"] in (5, 10) and 1 <= b["unlock"] <= 10
                  and (b["primary"] is None or b["primary"] in ABILITIES)
                  and (b["secondary"] is None or b["secondary"] in ABILITIES))
            slots = [(int(k), v) for k, v in b["staff"].items()]
            slots.sort()
            check(f'{b["id"]}: staff milestones',
                  all(1 <= l <= b["maxLevel"] and 0 <= n <= 3 for l, n in slots)
                  and [n for _, n in slots] == sorted(n for _, n in slots))
        for mx, curve in eco["levelCurves"].items():
            for field in ("output", "cost", "durationSeconds"):
                values = curve[field]
                check(f'Lv{mx}: {field} curve', len(values) == int(mx)
                      and all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0 for v in values)
                      and values == sorted(values))
        for field in ("costGoldByTargetLevel", "durationSecondsByTargetLevel"):
            values = eco["centerUpgrade"][field]
            check(field, len(values) == 10 and values == sorted(values)
                  and all(isinstance(v, int) and v >= 0 for v in values))
        ceilings = {}
        for c in range(1, 11):
            ceilings[c] = sum(development(b, min(c, b["maxLevel"]), dev)
                              for b in buildings if b["unlock"] <= c)
        gates = []
        for row in prog["levels"][1:]:
            target = row["level"]
            req = row["upgradeRequirements"]
            check(f'Lv{target}: score gate reachable', req["villageDevelopment"] <= ceilings[target - 1])
            check(f'Lv{target}: count fits previous capacity', req["residentCount"] <= caps[target - 2])
            check(f'Lv{target}: mirrors and balance key',
                  row["dev"] == req["villageDevelopment"] and row["mastery"] == req["jobMastery"]
                  and req["goldBalanceKey"] == "centerUpgrade.costGoldByTargetLevel"
                  and req["goldBalanceIndex"] == target - 1)
            mastery = req["jobMastery"]
            if mastery:
                slots = sum(max((n for l, n in b["staff"].items() if int(l) <= target - 1), default=0)
                            for b in buildings if b["unlock"] < target)
                check(f'Lv{target}: mastery gate structurally feasible',
                      0 <= mastery["threshold"] <= 100 and mastery["count"] <= min(slots, caps[target - 2]))
            gates.append({"from": target - 1, "to": target, "developmentCeiling": ceilings[target - 1],
                          "required": req["villageDevelopment"]})
        check("festival building IDs", set(prog["ending"]["requires"]["majorBuildingsBuilt"]) == set(by_id) - {"rescue_center"})
        witness = {b["id"]: min(b["maxLevel"], 5) for b in buildings if b["id"] != "rescue_center"}
        witness_score = sum(development(by_id[k], v, dev) for k, v in witness.items())
        check("festival achievable without all buildings max",
              witness_score >= prog["ending"]["requires"]["villageDevelopment"]
              and any(v < by_id[k]["maxLevel"] for k, v in witness.items())
              and all(witness[k] >= v for k, v in prog["ending"]["requires"]["requiredBuildingLevels"].items()))
        check("starting grant covers first village",
              eco["wallet"]["initialGold"] >= sum(eco["centerUpgrade"]["costGoldByTargetLevel"][1:3])
              + eco["buildingEconomy"]["housing"]["baseBuildCostGold"]
              + eco["buildingEconomy"]["park"]["baseBuildCostGold"])
        check("no-staff deadlock fallback", eco["wallet"]["baseSupportGoldPerMinute"] > 0
              and not eco["wallet"]["supportRequiresStaff"] and not eco["wallet"]["careActionsCostGold"])
        check("zero workers = zero shop income", building_rate(by_id["cafe"], 3, [], eco) == 0)
        check("worker list order irrelevant", math.isclose(staff_factor([0.9, 1.2, 1.05], eco), staff_factor([1.05, 0.9, 1.2], eco)))
        check("equal worker contributions 1, 1.7, 2.2",
              all(math.isclose(staff_factor([1.0] * n, eco), v) for n, v in ((1, 1), (2, 1.7), (3, 2.2))))
        e = efficiency(8, 4, 50, eco)
        check("cafe example 16.497 G/min", math.isclose(building_rate(by_id["cafe"], 3, [e], eco), 16.497))
        check("offline cap and negative elapsed", offline_gold(100, 43200, eco) == 48000
              and offline_gold(100, -60, eco) == 0 and offline_gold(100, 21600, eco) == 36000)
        check("mastery checkpoints", all(math.isclose(mastery_at(t, eco), m) for m, t in eco["growth"]["masteryCurve"]))
        links = {(x["from"], x["to"]) for x in bdoc["supplyLinks"]}
        check("supply links match economy", links == {(src, dst) for dst, inputs in eco["supply"]["consumers"].items() for src in inputs})
        check("supply capacity shared and never hard-stops consumers",
              eco["supply"]["providerCoverage"] == "min(1,output/sum_active_consumer_demand)"
              and eco["supply"]["missingSupplyMultiplier"] == 1)
        check("ads do not gate content or multiply training",
              not eco["ads"]["requiredForProgress"] and not eco["growth"]["adsMultiplyGrowth"]
              and not eco["ads"]["incomeBoost"]["multiplyWithOfflineBonus"])
        check("speedup and boost bounded", eco["ads"]["speedup"]["maxClaimsPerJob"] == 3
              and eco["ads"]["incomeBoost"]["maximumBankedSeconds"] == 1800
              and eco["ads"]["offlineExtra"]["maxClaimsPerSettlement"] == 1)
        check("pace explicitly unvalidated", eco["pace"]["validated"] is False)
        print(json.dumps({"status": "PASS", "checks": len(checks), "gates": gates,
                          "maxDevelopment": ceilings[10], "festivalWitness": witness,
                          "festivalWitnessScore": witness_score,
                          "limitations": ["No playthrough-duration simulation.", "No full cat discovery-condition validation.",
                                          "No runtime ad SDK, save/reload, reward-ledger or device tests.",
                                          "No numeric shared-supply integration or offline event-timeline tests."]},
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
