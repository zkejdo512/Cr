from __future__ import annotations
import random
from .cards import CARD_SPECS

class RandomLegalAgent:
    """Tiny baseline bot for simulator regression/self-play plumbing tests.

    It is intentionally weak. Its purpose is to verify that two policies can drive
    the same environment API that a learned policy will later use.
    """
    def __init__(self, seed: int = 0, play_probability: float = 0.10, ability_probability: float = 0.03):
        self.rng = random.Random(seed)
        self.play_probability = play_probability
        self.ability_probability = ability_probability

    def act(self, state: dict, side: str):
        p = state['players'][side]
        # Occasionally try an active ability for an alive hero/champion.
        if self.rng.random() < self.ability_probability:
            active_sources = {e.get('source_card') for e in state['entities'] if e['owner'] == side}
            ability_cards = [c for c in active_sources if c in CARD_SPECS and CARD_SPECS[c].hero_ability]
            if ability_cards:
                c = self.rng.choice(sorted(ability_cards))
                if p['elixir'] >= CARD_SPECS[c].hero_ability_cost:
                    return {'type':'ability', 'card':c}

        if self.rng.random() >= self.play_probability:
            return None
        affordable = [c for c in p['hand'] if CARD_SPECS[c].elixir <= p['elixir'] + 1e-9]
        if not affordable:
            return None
        card = self.rng.choice(affordable)
        spec = CARD_SPECS[card]
        x = self.rng.uniform(-7.5, 7.5)
        if spec.kind == 'spell':
            y = self.rng.uniform(-14.5, 14.5)
        elif side == 'blue':
            y = self.rng.uniform(-14.5, -1.5)
        else:
            y = self.rng.uniform(1.5, 14.5)
        return {'type':'play', 'card':card, 'x':x, 'y':y}
