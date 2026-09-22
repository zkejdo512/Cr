import time
from crgod_sim import CRGodEnv

N = 5
TICKS = 2000
start = time.perf_counter()
steps = 0
for seed in range(N):
    env = CRGodEnv(seed=seed)
    env.reset()
    for _ in range(TICKS):
        if env.done:
            break
        env.step()
        steps += 1
elapsed = time.perf_counter() - start
print(f"{steps:,} ticks in {elapsed:.3f}s")
print(f"~{steps/elapsed:,.0f} env ticks/s on this machine (idle-board smoke benchmark)")
print("Combat-heavy matches will be slower; this is not a final performance claim.")
