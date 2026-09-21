# Building Production Data Specification

## Status
Working production-data baseline for Astra implementation. Numeric economy values remain balance data and are intentionally not hard-coded here yet.

## Core Rules
- v1.0 contains 13 building types.
- Staffed buildings have at most 3 assigned cats.
- A resident can be formally assigned to only one staffed building at a time.
- Reassignment is free and preserves job mastery.
- Staff slot unlocks are data-driven by building level.
- Building level is capped by both its own maxLevel and current Rescue Center level.
- Work animation and economic simulation are decoupled.
- Milestone levels should alter one or more of Economy / Staff / Visual / Behavior.
- Buildings without staff still provide resident behaviors and world value.

## Data Fields
Each building defines:
- id / localization name
- maxLevel
- unlockCenterLevel
- staffSlotsByLevel
- primaryAbility / secondaryAbility
- roles
- work or resident activities
- milestoneChanges

## Staff Slot Baseline
- Lv10 staffed buildings: 1 at Lv1, 2 at Lv3, 3 at Lv6.
- Lv5 staffed buildings: 1 at Lv1, 2 at Lv3, 3 at Lv5.
- Rescue Center exception: 0 at Lv1, 1 at Lv2, 2 at Lv3, 3 at Lv5.

## Current 13 Buildings
구조센터, 주택, 공원, 농장, 어시장, 카페, 식당, 잡화점, 공방, 미용실, 진료소, 빵집, 마을광장.

주민회관과 여관은 v1.0에서 제외.

## Supply Links
The first production baseline only formalizes:
- 농장 → 식당
- 어시장 → 식당
- 농장 → 빵집

Supply should be presented as readable efficiency/status rather than a heavy item-inventory simulation.

## Not Yet Locked
The following belong to later balance tables:
- construction prices
- upgrade prices
- build times
- base gold/minute
- supply coefficients
- interior slot counts per exact level
- exact development-score awards

Keep these outside core code so they can be tuned after vertical-slice testing.
