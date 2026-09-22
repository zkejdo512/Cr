# Accuracy contract — v0.2

This simulator is intended for CR-God training research. It does **not** claim server-perfect Clash Royale reproduction yet.

Implemented mechanics for the first fixed archetype include evolution cycling, Evolved Skeleton multiplication (cap 8), Evolved Musketeer 3-shot non-tower sniper behavior, Hero Ice Golem Snowstorm active ability, Electro Spirit chain/stun approximation, The Log ground-only line hit, Hog building targeting, Cannon pull, spells, hand/cycle and elixir.

Implemented mechanics for the known core of the second archetype include Little Prince fire-rate ramp and Royal Rescue/Guardienne, Evolved Elite Barbarians ranged Rage spear/path approximation, air targeting, and Evolved Skeleton Barrel two-barrel/75%-HP trigger/death spawn behavior.

Public current mechanics were used for the shape of these abilities. Several raw stats, pathing details, projectile geometry, collision/mass, knockback magnitude, exact pulse/spear timings and tower modifiers remain explicit calibration targets. The simulator should be compared against real/native-engine trajectories before self-play results are trusted.
