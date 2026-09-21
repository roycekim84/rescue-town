# Building Data Validation

Production validation requirements:

1. Exactly 13 v1 building IDs.
2. Unique building IDs.
3. maxLevel must be 5 or 10.
4. unlockCenterLevel must be 1~10.
5. Staff slot values must be 0~3.
6. No staffed building may exceed 3 slots.
7. Staff-slot milestone levels cannot exceed maxLevel.
8. Ability IDs must be one of care/social/focus/activity/sense or null.
9. Supply links must reference valid building IDs.
10. Every staffed building must define at least one work activity.
11. Every non-staff building must define resident/life activities.
12. Rescue Center must reach resident cap 50 at Lv10 (defined in progression data, not duplicated as building economy code).
13. Runtime economic ticks must not depend on a visible Work animation completing.
