# CR-God Simulator v0.4

Deterministic, headless training simulator for CR-God.

This release is focused on **training safety**, not adding more cards. It fixes the major ways an RL agent could learn the wrong thing from v0.2/v0.3.

## What v0.4 fixes

- Public observations no longer expose opponent exact hand, queue, deck, or elixir.
- `GridActionCodec` provides a fixed discrete action space and legal-action mask.
- Illegal discrete actions become penalized no-ops instead of silently corrupting trajectories.
- King Tower begins dormant and has a 4 s activation sequence after damage / Princess Tower destruction.
- Regulation / overtime / tiebreak structure now follows 3 min regulation + 2 min sudden-death overtime.
- Elixir phases are x1 for minutes 1–2, x2 for minute 3 and overtime minute 4, x3 in minute 5.
- Destroying a Princess Tower opens a lane-specific pocket deployment region (geometry is still marked for calibration).
- Fireball is time-resolved instead of instant.
- Arrows use three delayed volleys instead of one instant hit.
- The Log rolls through space over time and only hits units it reaches.
- Public observation noise can simulate position/HP error and missed enemy detections.
- Real/native-engine trajectory comparison utilities are included.

## Fixed Deck A

- Hog Rider
- Fireball
- The Log
- Cannon
- Electro Spirit
- Hero Ice Golem
- Musketeer Evolution
- Skeletons Evolution

## Deck B core currently known

- Little Prince
- Elite Barbarians Evolution
- Skeleton Barrel Evolution

The remaining five cards were never specified, so v0.4 does not invent them.

## Quick start on macOS

```bash
cd crgod_sim_v0_4
python3 -m venv .venv
source .venv/bin/activate
pip install -e . pytest
PYTHONPATH=. pytest -q
PYTHONPATH=. python3 stress_training.py
```

Optional CPU convergence test requires PyTorch:

```bash
pip install torch
PYTHONPATH=. python3 train_sanity_cannon.py
```

## RL-facing API

```python
from crgod_sim import CRGodEnv, GridActionCodec, DECK_A_26_HOG

env = CRGodEnv(seed=42)
env.reset(DECK_A_26_HOG, DECK_A_26_HOG)
codec = GridActionCodec(spacing=2.0)

obs_blue = env.observe('blue')
mask_blue = codec.legal_mask(env, 'blue')

# choose only among legal ids
blue_action = 0
red_action = 0
obs, reward, done, info = codec.step_discrete(
    env, blue_action, red_action, ticks=4
)
```

## True state vs public observation

`env.board_state()` is privileged simulator truth for debugging / teacher models.

`env.observe("blue")` or `env.observe("red")` is what a learned real-game policy should consume. It masks hidden enemy information and can add perception-like noise.

Do **not** train the deployable policy directly on `board_state()`.

## Validation status packaged with v0.4

- 23/23 automated tests passed.
- 8/8 masked-action stress matches completed.
- 44,232 stress ticks, 0 masked illegal actions, 0 non-finite entity states.
- CPU REINFORCE sanity task converged from 50% to 100% success.
- The same sanity task reached 100% final success on 5 tested random seeds.

These results prove the training plumbing and runtime stability of this build. They do **not** prove 1:1 live Clash Royale fidelity or full-game self-play convergence.

## The remaining gate before a 24–72 h paid RL run

Long paid training should still wait for:

1. the real remaining five cards of Deck B;
2. real/native-engine calibration of pathing, collision/mass, pull geometry and pocket geometry;
3. real-game timing calibration for spells / special mechanics;
4. a short full-game learning benchmark that improves on held-out seeds.

Use `crgod_sim.calibration.compare_tracks()` to quantify simulator-vs-reference trajectory error.

See `docs/TRAINING_READINESS.md` and `docs/CALIBRATION.md`.


## v0.12 fidelity hardening (2026-09-22)
See `FIDELITY_STATUS_2026-09-22.md`. Current regression suite: 32 tests.
