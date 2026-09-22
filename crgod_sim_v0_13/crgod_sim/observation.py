from __future__ import annotations
import copy, math, random
from dataclasses import dataclass

@dataclass(frozen=True)
class ObservationConfig:
    position_std: float = 0.0
    hp_fraction_std: float = 0.0
    miss_probability: float = 0.0
    hide_internal_timers: bool = True
    history_limit: int = 32


def _noise_rng(env, side: str):
    # Deterministic observation noise that does not perturb simulator RNG.
    salt = 0 if side == 'blue' else 1
    return random.Random((env._seed + 1) * 1000003 + env.tick * 17 + salt)


def public_observation(env, side: str, config: ObservationConfig | None = None) -> dict:
    """Return information a real player/perception stack could plausibly expose.

    Own hand/deck/elixir are known. Opponent exact hand, queue, deck and elixir are hidden.
    Visible played cards remain inferable from entity names and public action history.
    """
    if side not in ('blue', 'red'):
        raise ValueError('side must be blue or red')
    cfg = config or ObservationConfig()
    st = env.board_state()
    enemy = 'red' if side == 'blue' else 'blue'
    out = {
        'tick': st['tick'], 'time_s': st['time_s'], 'phase': st['phase'],
        'side': side, 'done': st['done'], 'winner': st['winner'],
        'crowns': copy.deepcopy(st.get('crowns', {})),
        'players': {}, 'entities': [], 'projectiles': copy.deepcopy(st['projectiles']),
        'spell_events': copy.deepcopy(st.get('spell_events', [])),
        'history': copy.deepcopy(st.get('history', [])[-cfg.history_limit:]),
    }
    own = copy.deepcopy(st['players'][side])
    opp = st['players'][enemy]
    out['players'][side] = own
    out['players'][enemy] = {
        'elixir': None,
        'hand': [None, None, None, None],
        'queue': None,
        'deck': None,
        'evolutions': {},
        'revealed_cards': sorted({h['card'] for h in out['history'] if h.get('side') == enemy and h.get('type') == 'play'}),
    }

    rng = _noise_rng(env, side)
    # Placement history is public in principle, but real vision will not recover exact sub-tile
    # coordinates. Apply the same optional position noise to opponent history.
    if cfg.position_std > 0:
        for h in out['history']:
            if h.get('side') == enemy and h.get('type') == 'play' and 'x' in h and 'y' in h:
                h['x'] = round(h['x'] + rng.gauss(0, cfg.position_std), 4)
                h['y'] = round(h['y'] + rng.gauss(0, cfg.position_std), 4)
    for ent in st['entities']:
        # In a real screen some non-tower entities can be missed by perception.
        if ent['owner'] == enemy and ent['kind'] != 'tower' and cfg.miss_probability > 0 and rng.random() < cfg.miss_probability:
            continue
        e = {
            'id': ent['id'], 'name': ent['name'], 'owner': ent['owner'], 'kind': ent['kind'],
            'x': ent['x'], 'y': ent['y'], 'hp_fraction': ent['hp_fraction'],
            'transport': ent['transport'], 'is_king': ent['is_king'], 'is_princess': ent['is_princess'],
            'is_evolved': ent['is_evolved'], 'source_card': ent['source_card'],
        }
        if cfg.position_std > 0 and ent['kind'] != 'tower':
            e['x'] = round(e['x'] + rng.gauss(0, cfg.position_std), 4)
            e['y'] = round(e['y'] + rng.gauss(0, cfg.position_std), 4)
        if cfg.hp_fraction_std > 0 and ent['kind'] != 'tower':
            e['hp_fraction'] = round(max(0.0, min(1.0, e['hp_fraction'] + rng.gauss(0, cfg.hp_fraction_std))), 5)
        # King activation is visually observable; hidden combat timers are not.
        if ent['is_king']:
            e['king_active'] = bool(ent.get('special', {}).get('king_active', False))
        if not cfg.hide_internal_timers:
            e['target_id'] = ent.get('target_id')
            e['attack_cooldown'] = ent.get('attack_cooldown')
            e['deploy_remaining'] = ent.get('deploy_remaining')
            e['status'] = copy.deepcopy(ent.get('status', {}))
            e['special'] = copy.deepcopy(ent.get('special', {}))
        out['entities'].append(e)
    return out
