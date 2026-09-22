# CR-God Simulator v0.11 — Fidelity patch

This build is a **calibration build**, not a claim of bit-for-bit Supercell server equivalence.
Do not start a long paid RL run until the remaining physics gates below are validated against real-game trajectories.

## Corrected in v0.11

- Fixed Deck B is executable: Lightning / Rune Giant / Executioner / Little Prince / Evo Elite Barbarians / Evo Skeleton Barrel / Royal Delivery / Arrows.
- Level-16 Tower Princess baseline: 4858 HP, 173 damage, 0.8 s attack period.
- Level-16 King Tower baseline: 7704 HP, 173 damage, 1.0 s attack period.
- Little Prince level-16 damage baseline: 167.
- Little Prince attack ramp is now 1.2 s for shots 1–2, 0.6 s for shots 3–4, 0.4 s for shot 5+.
- August-2026 Little Prince movement retention implemented: charged fire-rate state is retained for up to 0.3 s of movement.
- Royal Rescue cast delay remains 0.944 s; pushback distance is 2.5 tiles; level-16 charge damage is 515 (scaled from the current level-11 320 baseline).
- Guardienne level-16 baseline: 2556 HP, 374 melee damage, 1.2 s hit period, 0.5 s first hit, 0.3 s deploy.
- King Tower no longer uses the fabricated 4-second activation delay after taking damage.
- Royal Delivery now has own-side placement, a 3.0 s delivery delay, troop-only area damage and Recruit spawn.
- Evolved Elite Barbarians spear damage/rage duration updated toward the August-2026 balance baseline.
- Rune Giant / Executioner level-16 baseline entries added.
- Regression suite: 26/26 tests pass.

## Still NOT certified 1:1

These are blockers before claiming physical equivalence:

1. Exact pathfinding/navigation mesh and bridge routing.
2. Collision solver, unit mass, pushing and body-blocking.
3. Projectile launch offsets, travel interpolation and retarget/despawn behavior.
4. Exact Executioner boomerang geometry/timing for outbound and return passes.
5. Full Rune Giant enchant lifecycle and every-third-attack bonus behavior.
6. Exact Evolved Skeleton Barrel two-stage balloon/drop physics.
7. Exact Evolved Elite Barbarians spear path/rage strip geometry.
8. Exact post-Princess-Tower deployment tile mask.
9. Current September-2026 per-spell Crown Tower chip values need explicit per-card values rather than a generic multiplier.
10. Every fixed-deck card must be trajectory-validated against recorded level-16 matches.

## Required calibration gate

For each fixed-deck card, record controlled interactions at 60 fps, extract event timestamps/positions, and compare simulator vs game for:
- deploy completion
- first hit
- subsequent hit intervals
- projectile impact
- movement over 1/2/4 seconds
- target acquisition/retarget
- knockback displacement
- death/spawn timing
- tower damage

Long RL training should start only after these errors are within the chosen tolerance and all mechanics tests remain green.
