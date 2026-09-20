# Art Direction & Asset Specification — v1.0

## World
- Portrait mobile presentation.
- Cozy 2D quarter-view village.
- Warm, readable, soft illustration style rather than strict pixel art.
- Buildings and paths must remain readable behind moving residents.
- The village is one continuous world; building interiors should prefer cutaway/zoom presentation over separate scenes.

## Cat Direction
Residents are four-legged domestic cats, not anthropomorphic humanoids.

Requirements:
- recognizable as cats at normal village zoom
- slightly simplified/cute proportions
- no human hands/body
- no upright humanoid working pose
- job identity comes from small accessories and behavior

## Single Source of Appearance
Each CAT_001~CAT_050 owns a fixed Appearance Definition. Structure, care, profile, village, work, rest and festival representations must preserve that identity.

Appearance dimensions:
- coat base color
- coat pattern
- face marking
- eye color/shape
- fur length
- tail
- body silhouette
- distinctive marking

Internal parts may be reused, but the shipped roster is 50 authored character designs, not unrestricted random generation.

## Portraits
Profile art must derive from the same Appearance Definition as the world character. Do not independently generate unrelated portrait illustrations.

## Common Animation Vocabulary
Core shared actions:
Idle, Walk, Run, Sit, Sleep, Eat, Play, Social, Happy, Work.

Building Work Points can add contextual actions without requiring a wholly independent animation set per cat.

## Emotion Readability
Use body pose plus small bubbles/icons where useful: food, sleep, play, affection, surprise. Do not rely only on tiny facial expressions.

## Job Accessories
Accessories are overlays on the base resident identity. Examples: farm hat, cafe scarf, medical marker, workshop headscarf. They must not transform cats into humanoid workers. Default appearance returns outside work.

## Cat-scale Architecture
Facilities are designed for cats: low counters, paw buttons, automatic machines, cat passages, small carts, low beds/exam tables, catwalks.

## Building Cutaway
Selecting a building should preferably zoom and reveal/cut away the roof/front so the assigned real residents can be seen working. Leaving the building restores the exterior.

## Prompt Specification
When generating production art, prompts must include:
- Rescue Town visual style
- four-legged domestic cat
- non-anthropomorphic
- consistent body proportions
- exact Appearance Definition
- readable silhouette
- cozy 2D mobile game art
- quarter-view compatibility
- transparent background where appropriate
- no human anatomy
- no upright humanoid pose
- no random clothing

Final model-specific prompt wording is deferred until the asset production pipeline is chosen.

## Art QA
### Thumbnail Test
View all 50 cats at normal/small game scale. Similar residents must still have enough distinguishing marks.

### Identity Test
For each resident compare rescue, care, profile, walking, working and sleeping representations. They must immediately read as the same cat.

### Production Principle
Avoid treating 50 cats × every animation as independent artwork. Reuse common rig/animation logic, fixed appearances, accessory overlays and building Work Points wherever technically appropriate.
