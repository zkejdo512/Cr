from crgod_sim import CRGodEnv, DECK_A_26_HOG, render_svg

# Deck A against the old baseline deck. This demo is intentionally NOT the user's
# final Deck B, because its remaining five cards have not been specified yet.
env = CRGodEnv(seed=7)
state = env.reset(deck_a=DECK_A_26_HOG)
env.players['blue'].elixir = 10

# Put Hog and Hero Ice Golem together to exercise two Deck-A mechanics.
env.play('blue', 'Hog Rider', -3.0, -5.0)
# Force the hero into hand for a compact mechanics demo (not a match-policy example).
env.players['blue'].hand[0] = 'Hero Ice Golem'
env.players['blue'].elixir = 10
env.play('blue', 'Hero Ice Golem', -2.2, -5.8)
for _ in range(25):
    state, _, _, _ = env.step()
env.players['blue'].elixir = 10
env.activate_ability('blue', 'Hero Ice Golem')
for _ in range(50):
    state, _, _, _ = env.step()

render_svg(state, 'crgod_v0_2_demo.svg')
print('wrote crgod_v0_2_demo.svg')
print('blue hand:', state['players']['blue']['hand'])
print('blue evo state:', state['players']['blue']['evolutions'])
