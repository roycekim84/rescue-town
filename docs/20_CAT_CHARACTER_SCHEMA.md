# Cat Character Data Schema — v1.0

## Goal
Define one data model that can drive catalog, discovery, rescue, appearance, personality, growth, preferences, profile and life simulation.

## Static Catalog Data
Each of the 50 cats has authored static data.

```text
CatDefinition
  catalogId
  localizationKey
  appearance
  personality
  baseAbilities
  discovery
  rescueScenario
  preferences
  behaviorBias
```

### appearance
- coatBase
- pattern
- faceMark
- eyeStyle
- furLength
- tailType
- bodyType
- distinctiveMark

### baseAbilities
- care
- social
- focus
- activity
- sense

Initial target range: 2~8.

### discovery
- minimumCenterLevel
- conditions[]
- catalogHintBasic
- catalogHintDetailed

### rescueScenario
- location
- mechanic
- characterVariation

Reusable mechanic families include food lure, obstacle clearing, height rescue, trail/sound search, and trust/waiting.

### preferences
- preferredFacilities[]
- preferredActivities[]
- favoriteInteractionOrObject

Preferences affect life behavior/character expression, not character rarity.

### behaviorBias
Weights used by life AI. Examples: social, food, outdoor, rest, play, quiet.

## Runtime Resident Data
Generated once when the catalog cat is rescued.

```text
ResidentInstance
  residentId
  catalogId
  customName
  rescueDate
  rescueRecord
  abilities
  jobMasteries
  playerBond
  relationships
  assignedBuilding
  home
  currentState
  lifeRecords
```

Static appearance/personality comes from CatDefinition; growth and history live on ResidentInstance.

## Identity Rule
One catalog cat can produce only one resident in v1.0. No duplicate residents for the same catalogId.

## Naming
Default display name comes from localization. Player may rename the resident without changing catalog identity.

## Data-driven Requirement
Astra implementation should keep roster data external/data-driven where practical so balance, discovery conditions and localization can be edited without rewriting resident simulation code.
