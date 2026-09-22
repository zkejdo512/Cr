# Calibration workflow

The simulator should be treated as a model that must be measured against a reference.

For a fixed scripted scenario:

1. use the same deck;
2. deploy the same cards at the same timestamps and coordinates;
3. record reference entity tracks every 50–100 ms;
4. record simulator tracks at the same times;
5. compare position, HP, target changes, first-hit time, death time and tower damage;
6. adjust only isolated calibration constants / mechanics;
7. rerun regression tests.

`crgod_sim.snapshot(env)` creates compact simulator track rows.
`crgod_sim.compare_tracks(reference, simulated)` reports position RMSE, HP error and missing rows.

Recommended first scenarios:

- Hog -> Cannon pull in each standard placement.
- Hog alone to Princess Tower first-hit / second-hit timings.
- Musketeer vs Knight projectile and hit timing.
- Fireball on moving Musketeer.
- Arrows vs Skeletons crossing the target region.
- Log vs Skeletons / Knight and Crown Tower at edge of path.
- King activation by spell damage.
- Princess Tower destruction -> pocket deployment legality.
