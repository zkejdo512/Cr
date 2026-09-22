"""Dependency-free smoke test: PYTHONPATH=. python3 self_test.py"""
from crgod_sim import CRGodEnv, DECK_A_26_HOG


def run(seed):
    env = CRGodEnv(seed=seed)
    env.reset(deck_a=DECK_A_26_HOG)
    env.players['blue'].elixir = 10
    env.step({'card':'Hog Rider','x':-3,'y':-5}, None, ticks=400)
    return env.board_state()

assert run(123) == run(123), 'simulation is not deterministic'

E = CRGodEnv(seed=5)
S = E.reset(deck_a=DECK_A_26_HOG)
assert 'Musketeer Evolution' in S['players']['blue']['evolutions']
assert S['players']['blue']['evolutions']['Skeletons Evolution']['cycles_required'] == 2

# Active hero ability action path.
E.players['blue'].elixir = 10
# Hero Ice Golem starts as 6th card, force hand for this mechanics smoke test.
E.players['blue'].hand[0] = 'Hero Ice Golem'
E.play('blue','Hero Ice Golem',0,-5)
for _ in range(21): E.step()
E.players['blue'].elixir = 10
E.step({'type':'ability','card':'Hero Ice Golem'})
hero = max(e for e in E.entities.values() if e.source_card == 'Hero Ice Golem')
assert len(hero.special.get('snowstorm_pulses', [])) >= 1

print('CR-God Simulator v0.4 self-test: PASS')
