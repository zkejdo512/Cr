from __future__ import annotations
import math, random, time
from crgod_sim import CRGodEnv, GridActionCodec, DECK_A_26_HOG


def sample_action(rng, mask, play_p=0.12):
    if rng.random() > play_p:
        return 0
    legal=[i for i,v in enumerate(mask) if v and i != 0]
    return rng.choice(legal) if legal else 0


def main(matches=8):
    codec=GridActionCodec(spacing=2.0)
    total_ticks=0; illegal=0; nonfinite=0; completed=0
    t0=time.perf_counter()
    for m in range(matches):
        env=CRGodEnv(seed=100+m); env.reset(DECK_A_26_HOG, DECK_A_26_HOG, seed=100+m)
        rng=random.Random(9000+m)
        while not env.done and env.tick < 6000:
            mb=codec.legal_mask(env,'blue'); mr=codec.legal_mask(env,'red')
            a=sample_action(rng,mb); b=sample_action(rng,mr)
            _,_,done,info=codec.step_discrete(env,a,b,ticks=4)
            illegal += int(info['illegal_discrete_actions']['blue']) + int(info['illegal_discrete_actions']['red'])
            for e in env.entities.values():
                for v in (e.x,e.y,e.hp,e.attack_cooldown,e.deploy_remaining):
                    if isinstance(v,float) and not math.isfinite(v): nonfinite += 1
            if done: break
        total_ticks += env.tick; completed += int(env.done)
    wall=time.perf_counter()-t0
    print(f'matches={matches} completed={completed} ticks={total_ticks} wall_s={wall:.3f} ticks_per_s={total_ticks/max(wall,1e-9):.0f}')
    print(f'illegal_masked_actions={illegal} nonfinite_values={nonfinite}')
    if completed != matches or illegal or nonfinite:
        raise SystemExit('FAIL')
    print('PASS: masked-action stress gate')

if __name__=='__main__': main()
