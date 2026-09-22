# Training Readiness — v0.4

## Passed

- Deterministic headless engine.
- Hidden opponent hand/queue/deck/exact elixir masked from public observations.
- Fixed discrete action space and legal-action mask.
- Illegal discrete actions penalized and converted to no-op.
- King Tower starts dormant and activates after its activation delay.
- Regulation/overtime/tiebreak framework corrected.
- Elixir timing corrected for the five-minute standard battle timeline.
- Time-resolved Fireball, Arrows and Log baseline.
- Observation noise hooks.
- 23 automated tests.
- 8-match masked-action stress gate.
- 5-seed CPU convergence sanity gate.

## Still not certified for expensive 24–72 h self-play

- Exact live-game pathfinding is not yet calibrated.
- Collision/mass and building-pull geometry are approximate.
- Pocket geometry after tower destruction is a documented approximation.
- Several special-card constants remain public-data / research approximations.
- Deck B is incomplete because five user cards are still unknown.
- Full-game PPO/self-play has not yet passed a multi-seed improvement benchmark.

## Spending gate

1. Zero-cost Mac tests pass.
2. Real/native-engine calibration error is within chosen tolerances.
3. 30–60 minute cloud run shows learning.
4. 3–6 hour repeat on multiple seeds shows consistent improvement.
5. Only then run 24 h+.
