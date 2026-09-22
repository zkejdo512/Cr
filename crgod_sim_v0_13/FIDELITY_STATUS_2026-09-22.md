# CR-God Simulator v0.12 — fidelity hardening

## Implemented / corrected
- Current September 2026 Evolved Elite Barbarians spear window 3.0–4.5 tiles and Rage duration 2.0 s.
- Level-16 base Elite Barbarians corrected to 2143 HP / 613 damage / 1.4 s / 0.5 s first hit / 1.2 melee / 6 sight.
- Little Prince firing ramp corrected to current 1.2 / 0.8 / 0.4 stages with 3 attacks required per stage; 0.3 s movement retention retained.
- Royal Rescue excludes buildings/towers from charge damage/knockback and uses distance-dependent pushback up to 2.5 tiles.
- Evolved Skeleton Barrel: two barrels, 75% first-drop trigger, level-16 306 death damage per barrel, 7 skeletons/barrel.
- Lightning: explicit Crown Tower damage path plus 0.5 s stun and top-3-highest-HP targeting.
- Arrows: explicit per-volley Crown Tower damage path; level-16 full troop damage corrected to 588.
- Rune Giant: building targeting, 8.5-tile nearest-two enchant selection, every-third-attack bonus hook, 5 s post-death expiry.
- Executioner: outbound + return axe projectile with independent hit sets on each pass.
- Princess Tower destruction now activates King Tower immediately rather than a fabricated 4 s delay.
- Regression suite expanded to 32 tests.

## Important validation boundary
No third-party reimplementation can truthfully be certified bit-for-bit identical to Supercell's closed server without native/server telemetry. The remaining uncertainty is therefore calibration, not intentionally omitted mechanics: exact navmesh polygons, hidden mass/push constants, sub-tick animation/projectile launch offsets, and exact live level-16 constants where only level-11 balance values are officially published. Use controlled 60-fps recordings to regression-fit those constants before expensive RL.
