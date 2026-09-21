# Progression Data Specification

## Purpose
Connect the 50-resident roster, 13 buildings and Rescue Center Lv1~10 into one data-driven progression spine.

## Rescue Center
The Rescue Center is the sole source of:
- resident capacity
- current level cap for ordinary buildings
- system/building unlock stages

Current building level cap:
`min(building.maxLevel, rescueCenterLevel)`

## Upgrade Requirements
Center upgrades use only four progression axes:
1. resident count
2. village development score
3. job mastery milestones
4. gold

Player bond and resident relationships are deliberately excluded as mandatory gates.

## Working Center Requirements
The current baseline is encoded in `data/progression.json`.
Gold costs remain TBD until economy simulation.

Important: the player does not need to fill the current resident cap exactly before every center upgrade. This prevents one undiscovered cat from hard-blocking the main game.

## Village Development Score
Development score represents **physical village growth**.

Included:
- first construction of ordinary buildings
- ordinary building upgrades
- additional small weighting for park/town-square development

Excluded:
- number of cats
- catalog completion
- Rescue Center level itself
- job mastery
- bond
- relationships

Those systems already have their own meaning and should not be double-counted.

## Decoration
Interior collection is not part of mandatory development score in the initial v1 baseline. Players should be able to decorate for taste without feeling forced to craft every item for progression.

## Festival
Working ending requirements:
- Rescue Center Lv10
- 50/50 catalog
- village development 3500 (tunable)
- all major building types constructed

All buildings at max level are NOT required for the ending.

## Balance Boundary
Development award values and the final threshold are first-pass numbers, not release balance. They must be checked against the theoretical score ceiling and actual playtest pacing before lock.
