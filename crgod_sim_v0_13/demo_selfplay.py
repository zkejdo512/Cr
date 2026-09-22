from crgod_sim import CRGodEnv, DECK_A_26_HOG, DEFAULT_DECK, RandomLegalAgent, run_match, render_svg

# Plumbing demo only: Deck B is intentionally not fabricated, so Deck A fights the
# legacy baseline deck until the user's remaining five Deck-B cards are supplied.
blue = RandomLegalAgent(seed=10, play_probability=0.18, ability_probability=0.05)
red = RandomLegalAgent(seed=20, play_probability=0.18, ability_probability=0.02)
state, trace = run_match(DECK_A_26_HOG, DEFAULT_DECK, blue, red, seed=99,
                         decision_interval_ticks=4, max_ticks=6000)
render_svg(state, 'selfplay_final.svg')
print('winner:', state['winner'])
print('time:', state['time_s'])
print('trace events:', len(trace))
print('wrote selfplay_final.svg')
