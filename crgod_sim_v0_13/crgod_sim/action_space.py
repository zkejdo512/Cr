from __future__ import annotations
from dataclasses import dataclass
from .cards import CARD_SPECS
from .observation import public_observation, ObservationConfig

@dataclass
class GridActionCodec:
    """Fixed discrete action space suitable for PPO/DQN-style policies.

    Action 0 = no-op.
    Then 4 hand slots x every arena grid cell.
    Final 8 actions address hero/champion abilities by deck slot, even after the card leaves hand.
    """
    x_min: float = -7.5
    x_max: float = 7.5
    y_min: float = -14.5
    y_max: float = 14.5
    spacing: float = 1.5

    def __post_init__(self):
        self.xs = self._grid(self.x_min, self.x_max)
        self.ys = self._grid(self.y_min, self.y_max)
        self.cells = [(x, y) for y in self.ys for x in self.xs]
        self.n_cells = len(self.cells)
        self.play_offset = 1
        self.ability_offset = self.play_offset + 4 * self.n_cells
        self.n = self.ability_offset + 8

    def _grid(self, lo, hi):
        vals=[]; v=lo
        while v <= hi + 1e-9:
            vals.append(round(v, 4)); v += self.spacing
        return vals

    def decode(self, action_id: int, env, side: str):
        if action_id == 0:
            return None
        if self.play_offset <= action_id < self.ability_offset:
            z = action_id - self.play_offset
            slot, cell_idx = divmod(z, self.n_cells)
            hand = env.players[side].hand
            if slot >= len(hand):
                return None
            x, y = self.cells[cell_idx]
            return {'type':'play', 'card':hand[slot], 'x':x, 'y':y}
        if self.ability_offset <= action_id < self.n:
            deck_slot = action_id - self.ability_offset
            deck = env.players[side].deck
            if deck_slot >= len(deck):
                return None
            return {'type':'ability', 'card':deck[deck_slot]}
        return None

    def legal_mask(self, env, side: str) -> list[bool]:
        mask = [False] * self.n
        mask[0] = True
        p = env.players[side]
        for slot, card in enumerate(p.hand[:4]):
            spec = CARD_SPECS[card]
            if p.elixir + 1e-9 < spec.elixir:
                continue
            base = self.play_offset + slot * self.n_cells
            for ci, (x,y) in enumerate(self.cells):
                if env.can_deploy(side, card, x, y):
                    mask[base+ci] = True
        for deck_slot, card in enumerate(p.deck[:8]):
            spec = CARD_SPECS[card]
            if not spec.hero_ability or p.elixir + 1e-9 < spec.hero_ability_cost:
                continue
            active = [e for e in env.entities.values() if e.alive and e.owner == side and e.source_card == card
                      and e.deploy_remaining <= 1e-9 and e.special.get('ability_cooldown_remaining',0.0) <= 1e-9]
            if active:
                mask[self.ability_offset + deck_slot] = True
        return mask

    def step_discrete(self, env, blue_action: int, red_action: int, ticks: int = 1,
                      illegal_penalty: float = -0.02,
                      observation_config: ObservationConfig | None = None):
        masks = {'blue': self.legal_mask(env, 'blue'), 'red': self.legal_mask(env, 'red')}
        raw = {'blue': blue_action, 'red': red_action}
        acts = {}
        illegal = {}
        for side in ('blue','red'):
            aid = int(raw[side])
            ok = 0 <= aid < self.n and masks[side][aid]
            illegal[side] = not ok
            acts[side] = self.decode(aid, env, side) if ok else None
        state, rewards, done, info = env.step(acts['blue'], acts['red'], ticks=ticks)
        for side in ('blue','red'):
            if illegal[side]:
                rewards[side] += illegal_penalty
        info['illegal_discrete_actions'] = illegal
        obs = {
            'blue': public_observation(env, 'blue', observation_config),
            'red': public_observation(env, 'red', observation_config),
        }
        return obs, rewards, done, info
