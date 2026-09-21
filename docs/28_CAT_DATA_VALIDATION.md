# Cat Data Validation — v1.0

## Automated Working Audit
- Count: 50
- Sequential CAT_001~CAT_050: true
- Initial total-stat range: 24~29

## Personality Counts
- active: 8
- relaxed: 7
- clever: 5
- social: 8
- foodie: 5
- caring: 7
- shy: 5
- playful: 5

## Ability Averages
- care: 4.96
- social: 5.46
- focus: 5.14
- activity: 4.88
- sense: 5.6

## Required Validation Rules
1. Exactly 50 catalog entries.
2. IDs unique and sequential CAT_001~CAT_050.
3. Personality must be one of: active, relaxed, social, shy, foodie, clever, playful, caring.
4. Every base ability must be integer 2~8.
5. minimumCenterLevel must be 1~10.
6. No duplicate catalog ID.
7. Every cat must define a rescue mechanic and at least one preferred facility or documented exception.
8. CAT_050 must require Center Lv10 and final-collection state in production logic; the compact data file marks its primary condition as final_arrival.
9. Discovery difficulty must not modify base power/rarity.
10. Runtime ResidentInstance must reference catalogId rather than duplicate static appearance/personality data.

## Content QA Still Required
This JSON intentionally normalizes the roster but does not replace the richer Character Sheet documents. Before production lock, enrich/verify exact face marks, eyes, fur length, tail/body definitions, localized hints, full discovery condition arrays, rescue locations/variations, and signature behavior IDs.
