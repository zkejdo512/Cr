from __future__ import annotations
import math
import random
from dataclasses import asdict
from typing import Optional

from .cards import CARD_SPECS, DEFAULT_DECK, CardSpec
from .state import Entity, Projectile, PlayerState, BoardState

SIDES = ('blue', 'red')
OPP = {'blue': 'red', 'red': 'blue'}

class CRGodEnv:
    """Deterministic, headless CR-God training simulator (v0.4).

    v0.4 focuses on the user's first two fixed archetypes. It is still a
    research simulator, not a claim of 1:1 server accuracy. Publicly described
    mechanics are implemented where practical; raw combat constants remain
    isolated for later native-engine/APK calibration.
    """

    ARENA_X = 9.0
    ARENA_Y = 16.0
    RIVER_HALF = 1.25
    BRIDGES = (-3.0, 3.0)

    def __init__(self, tick_s: float = 0.05, seed: int = 0):
        self.tick_s = tick_s
        self._seed = seed
        self.rng = random.Random(seed)
        self._next_id = 1
        self.tick = 0
        self.time_s = 0.0
        self.entities: dict[int, Entity] = {}
        self.projectiles: dict[int, Projectile] = {}
        self.players: dict[str, PlayerState] = {}
        self.spell_events: list[dict] = []
        self.history: list[dict] = []
        self.done = False
        self.winner: Optional[str] = None
        self._overtime_started = False
        self._overtime_crowns = {'blue': 0, 'red': 0}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reset(self, deck_a: Optional[list[str]] = None, deck_b: Optional[list[str]] = None,
              seed: Optional[int] = None) -> dict:
        if seed is not None:
            self._seed = seed
        self.rng = random.Random(self._seed)
        self._next_id = 1
        self.tick = 0
        self.time_s = 0.0
        self.entities = {}
        self.projectiles = {}
        self.spell_events = []
        self.history = []
        self.done = False
        self.winner = None
        self._overtime_started = False
        self._overtime_crowns = {'blue': 0, 'red': 0}

        da = list(deck_a or DEFAULT_DECK)
        db = list(deck_b or DEFAULT_DECK)
        self._validate_deck(da)
        self._validate_deck(db)
        self.players = {
            'blue': PlayerState('blue', 5.0, da, da[:4], da[4:], self._initial_evo_progress(da)),
            'red': PlayerState('red', 5.0, db, db[:4], db[4:], self._initial_evo_progress(db)),
        }
        self._spawn_towers('blue')
        self._spawn_towers('red')
        return self.board_state()

    def step(self, action_a: Optional[dict] = None, action_b: Optional[dict] = None,
             ticks: int = 1):
        if self.done:
            return self.board_state(), {'blue': 0.0, 'red': 0.0}, True, {'reason': 'already_done'}

        errors = {}
        for side, action in (('blue', action_a), ('red', action_b)):
            if not action:
                continue
            try:
                kind = action.get('type', 'play')
                if kind == 'ability':
                    self.activate_ability(side, action['card'])
                else:
                    self.play(side, action['card'], float(action['x']), float(action['y']))
            except Exception as exc:
                errors[side] = str(exc)

        reward_total = {'blue': 0.0, 'red': 0.0}
        for _ in range(max(1, ticks)):
            before = self._tower_hp_by_owner()
            self._tick_once()
            after = self._tower_hp_by_owner()
            for side in SIDES:
                enemy = OPP[side]
                reward_total[side] += (before[enemy] - after[enemy]) / 3000.0
                reward_total[side] -= (before[side] - after[side]) / 3000.0
            if self.done:
                break

        if self.done and self.winner in SIDES:
            reward_total[self.winner] += 1.0
            reward_total[OPP[self.winner]] -= 1.0
        return self.board_state(), reward_total, self.done, {'action_errors': errors}

    def play(self, side: str, card_name: str, x: float, y: float) -> None:
        if side not in SIDES:
            raise ValueError('side must be blue or red')
        p = self.players[side]
        if card_name not in p.hand:
            raise ValueError(f'{card_name} is not in {side} hand: {p.hand}')
        deck_spec = CARD_SPECS[card_name]
        if p.elixir + 1e-9 < deck_spec.elixir:
            raise ValueError(f'not enough elixir: have {p.elixir:.2f}, need {deck_spec.elixir}')

        is_evolved = False
        spawn_spec = deck_spec
        if deck_spec.evolution_of:
            progress = p.evolution_progress.get(card_name, 0)
            if progress >= deck_spec.evolution_cycles:
                is_evolved = True
                p.evolution_progress[card_name] = 0
            else:
                p.evolution_progress[card_name] = progress + 1
                spawn_spec = CARD_SPECS[deck_spec.evolution_of]

        x, y = self._validate_deploy(side, spawn_spec, x, y)
        p.elixir -= deck_spec.elixir
        self._cycle_card(p, card_name)
        self.history.append({'tick': self.tick, 'time_s': round(self.time_s, 3), 'side': side,
                             'type': 'play', 'card': card_name, 'x': round(x, 3), 'y': round(y, 3)})

        if spawn_spec.kind == 'spell':
            self._cast_spell(side, spawn_spec, x, y)
            return

        special_override = deck_spec.special if is_evolved else spawn_spec.special
        count = deck_spec.count if is_evolved else spawn_spec.count
        spread = deck_spec.deploy_spread if is_evolved else spawn_spec.deploy_spread
        actual_spec = deck_spec if is_evolved else spawn_spec

        if actual_spec.kind == 'building':
            self._spawn_from_spec(side, actual_spec, x, y, kind='building',
                                  source_card=card_name, is_evolved=is_evolved,
                                  special_override=special_override)
        else:
            offsets = self._formation_offsets(count, spread)
            group_id = self._id() if special_override == 'evo_skeletons' else None
            for ox, oy in offsets:
                e = self._spawn_from_spec(side, actual_spec, x + ox, y + oy, kind='troop',
                                          source_card=card_name, is_evolved=is_evolved,
                                          special_override=special_override)
                if group_id is not None:
                    e.special['evo_group'] = group_id

    def activate_ability(self, side: str, card_name: str) -> None:
        if side not in SIDES:
            raise ValueError('side must be blue or red')
        if card_name not in CARD_SPECS:
            raise ValueError(f'unknown card: {card_name}')
        spec = CARD_SPECS[card_name]
        if not spec.hero_ability:
            raise ValueError(f'{card_name} has no active ability in v0.4')

        candidates = [e for e in self.entities.values()
                      if e.alive and e.owner == side and e.source_card == card_name]
        if not candidates:
            raise ValueError(f'no active {card_name} on arena')
        e = max(candidates, key=lambda z: z.id)
        if e.deploy_remaining > 1e-9:
            raise ValueError('ability cannot be used before deployment completes')
        if e.special.get('ability_used', False):
            raise ValueError('ability already used by this deployed unit')
        cooldown = e.special.get('ability_cooldown_remaining', 0.0)
        if cooldown > 1e-9:
            raise ValueError(f'ability on cooldown: {cooldown:.2f}s')
        p = self.players[side]
        if p.elixir + 1e-9 < spec.hero_ability_cost:
            raise ValueError('not enough elixir for ability')
        p.elixir -= spec.hero_ability_cost
        e.special['ability_used'] = True
        e.special['ability_cooldown_remaining'] = 0.0
        self.history.append({'tick': self.tick, 'time_s': round(self.time_s, 3), 'side': side,
                             'type': 'ability', 'card': card_name})

        if spec.hero_ability == 'snowstorm':
            # Current (Sep 2026) mechanics baseline: 3 damaging slowing blasts,
            # no knockback, no final freeze. Exact pulse spacing remains calibratable.
            e.special['snowstorm_pulses'] = [1.00, 1.75, 2.50]
        elif spec.hero_ability == 'royal_rescue':
            e.special['royal_rescue_timer'] = 0.944
        else:
            raise ValueError(f'unsupported ability: {spec.hero_ability}')

    def board_state(self) -> dict:
        phase = 'normal' if self.time_s < 120 else ('double' if self.time_s < 240 else 'triple')
        players = {}
        for side, p in self.players.items():
            evo = {}
            for card in p.deck:
                spec = CARD_SPECS[card]
                if spec.evolution_of:
                    progress = p.evolution_progress.get(card, 0)
                    evo[card] = {
                        'progress': progress,
                        'cycles_required': spec.evolution_cycles,
                        'ready': progress >= spec.evolution_cycles,
                    }
            players[side] = {
                'elixir': round(p.elixir, 3),
                'hand': list(p.hand),
                'queue': list(p.queue),
                'deck': list(p.deck),
                'evolutions': evo,
            }

        st = BoardState(
            tick=self.tick,
            time_s=round(self.time_s, 3),
            phase=phase,
            players=players,
            entities=[self._entity_dict(e) for e in sorted(self.entities.values(), key=lambda z: z.id) if e.alive],
            projectiles=[asdict(p) for p in sorted(self.projectiles.values(), key=lambda z: z.id)],
            done=self.done,
            winner=self.winner,
        )
        out = st.as_dict()
        out['crowns'] = self._crowns_by_owner()
        out['spell_events'] = [self._public_spell_event(ev) for ev in self.spell_events]
        out['history'] = list(self.history[-64:])
        return out

    def observe(self, side: str, config=None) -> dict:
        from .observation import public_observation
        return public_observation(self, side, config)

    # ------------------------------------------------------------------
    # Setup / cards / evolution
    # ------------------------------------------------------------------
    def _validate_deck(self, deck: list[str]) -> None:
        if len(deck) != 8:
            raise ValueError('deck must contain exactly 8 cards')
        bad = [c for c in deck if c not in CARD_SPECS]
        if bad:
            raise ValueError(f'unknown card(s): {bad}')

    def _initial_evo_progress(self, deck: list[str]) -> dict[str, int]:
        return {c: 0 for c in deck if CARD_SPECS[c].evolution_of}

    def _id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i

    def _spawn_towers(self, side: str) -> None:
        sy = -1 if side == 'blue' else 1
        for x in (-3.25, 3.25):
            e = Entity(self._id(), 'Princess Tower', side, 'tower', x, sy * 12.0,
                       4858, 4858, 173, 0.8, 0.8, 0, 7.5, 8.0, 0.75,
                       targets='air_ground', projectile_speed=13.0, is_princess=True)
            self.entities[e.id] = e
        k = Entity(self._id(), 'King Tower', side, 'tower', 0.0, sy * 14.1,
                   7704, 7704, 173, 1.0, 1.0, 0, 7.0, 8.0, 0.9,
                   targets='air_ground', projectile_speed=13.0, is_king=True)
        k.special['king_active'] = False
        k.special['king_activation_remaining'] = None
        self.entities[k.id] = k

    def _cycle_card(self, p: PlayerState, card_name: str) -> None:
        idx = p.hand.index(card_name)
        next_card = p.queue.pop(0)
        p.hand[idx] = next_card
        p.queue.append(card_name)

    def _formation_offsets(self, count: int, spread: float):
        if count == 1:
            return [(0, 0)]
        if count == 2:
            return [(-spread / 2, 0), (spread / 2, 0)]
        if count == 3:
            return [(-spread, 0), (spread, 0), (0, spread * 0.7)]
        pts = []
        for i in range(count):
            angle = 2 * math.pi * i / count
            pts.append((math.cos(angle) * spread, math.sin(angle) * spread))
        return pts

    def _spawn_from_spec(self, side: str, s: CardSpec, x: float, y: float, kind: str,
                         source_card: Optional[str] = None, is_evolved: bool = False,
                         special_override: Optional[str] = None) -> Entity:
        e = Entity(
            self._id(), s.name, side, kind, x, y,
            s.hp, s.hp, s.damage, s.hit_speed, s.first_hit, s.move_speed,
            s.attack_range, s.sight_range, s.radius, s.targets, s.transport,
            s.projectile_speed, s.splash_radius, s.lifetime,
            deploy_remaining=s.deploy_time, attack_cooldown=s.first_hit,
            source_card=source_card or s.name, is_evolved=is_evolved,
        )
        tag = special_override or s.special
        if tag:
            e.special['tag'] = tag
        if s.hero_ability:
            e.special['ability_cooldown_remaining'] = 0.0
        if tag == 'little_prince':
            e.special['lp_attack_count'] = 0
            e.special['lp_move_grace'] = 0.0
        if tag == 'rune_giant':
            e.special['enchanted_ids'] = []
        if tag == 'executioner':
            e.special['axe_active'] = False
        if tag == 'evo_musketeer':
            e.special['sniper_ammo'] = 3
            e.special['sniper_cooldown'] = 0.0
        if tag == 'evo_elite_barbarians':
            e.special['spear_cooldown'] = 0.0
        if tag == 'skeleton_barrel':
            e.special['barrels_left'] = 1
            e.special['barrel_death_damage'] = 145.0
            e.special['skeletons_per_barrel'] = 7
        if tag == 'evo_skeleton_barrel':
            e.special['barrels_left'] = 2
            e.special['barrel_death_damage'] = 306.0
            e.special['skeletons_per_barrel'] = 7
            e.special['first_barrel_dropped'] = False
        self.entities[e.id] = e
        return e

    # ------------------------------------------------------------------
    # Deployment / spells
    # ------------------------------------------------------------------
    def can_deploy(self, side: str, card_name: str, x: float, y: float) -> bool:
        if side not in SIDES or card_name not in CARD_SPECS:
            return False
        spec = CARD_SPECS[card_name]
        if not (-self.ARENA_X + 0.5 <= x <= self.ARENA_X - 0.5
                and -self.ARENA_Y + 0.5 <= y <= self.ARENA_Y - 0.5):
            return False
        # Most spells are global. The Log is a rolling spell and obeys territory/pocket placement.
        if spec.kind == 'spell' and spec.special not in ('the_log', 'royal_delivery'):
            return True
        own_side = (y <= -self.RIVER_HALF) if side == 'blue' else (y >= self.RIVER_HALF)
        if own_side:
            return True
        # Pocket approximation after a Princess Tower is destroyed. Geometry is isolated here
        # so it can be replaced by exact tile masks during native-engine calibration.
        enemy = OPP[side]
        dead_princesses = [e for e in self.entities.values() if e.owner == enemy and e.is_princess and not e.alive]
        for tower in dead_princesses:
            same_lane = (x < 0) == (tower.x < 0)
            if not same_lane:
                continue
            if side == 'blue' and self.RIVER_HALF <= y <= 10.75:
                return True
            if side == 'red' and -10.75 <= y <= -self.RIVER_HALF:
                return True
        return False

    def _validate_deploy(self, side: str, spec: CardSpec, x: float, y: float):
        x = max(-self.ARENA_X + 0.5, min(self.ARENA_X - 0.5, x))
        y = max(-self.ARENA_Y + 0.5, min(self.ARENA_Y - 0.5, y))
        if not self.can_deploy(side, spec.name, x, y):
            raise ValueError(f'illegal deployment for {side}: {spec.name} at ({x:.2f},{y:.2f})')
        return x, y

    def _cast_spell(self, side: str, s: CardSpec, x: float, y: float):
        # Spells are time-resolved in v0.4 instead of applying damage instantly.
        if s.special == 'the_log':
            direction = 1.0 if side == 'blue' else -1.0
            self.spell_events.append({
                'kind': 'rolling_log', 'owner': side, 'x': x, 'y': y, 'dir': direction,
                'speed': 10.0, 'remaining': 10.1, 'width': 3.9, 'damage': s.damage,
                'tower_multiplier': s.spell_tower_multiplier, 'hit_ids': set(),
            })
            return
        if s.special == 'fireball':
            sy = -14.1 if side == 'blue' else 14.1
            self.spell_events.append({
                'kind': 'fireball', 'owner': side, 'x': 0.0, 'y': sy, 'tx': x, 'ty': y,
                'speed': 10.0, 'damage': s.damage, 'radius': s.spell_radius,
                'tower_multiplier': s.spell_tower_multiplier,
            })
            return
        if s.special == 'arrows':
            # Three volleys; exact per-volley timing remains a calibration constant.
            per = s.damage / 3.0
            for timer in (0.20, 0.30, 0.40):
                self.spell_events.append({
                    'kind': 'area_delayed', 'owner': side, 'timer': timer, 'x': x, 'y': y,
                    'damage': per, 'radius': s.spell_radius,
                    'tower_multiplier': s.spell_tower_multiplier, 'crown_tower_damage': (s.crown_tower_damage / 3.0 if s.crown_tower_damage is not None else None), 'targets': 'air_ground',
                })
            return
        if s.special == 'lightning':
            self.spell_events.append({
                'kind': 'lightning_delayed', 'owner': side, 'timer': 0.35, 'x': x, 'y': y,
                'damage': s.damage, 'radius': s.spell_radius,
                'tower_multiplier': s.spell_tower_multiplier, 'crown_tower_damage': s.crown_tower_damage,
            })
            return
        if s.special == 'royal_delivery':
            self.spell_events.append({
                'kind': 'royal_delivery', 'owner': side, 'timer': 3.0, 'x': x, 'y': y,
                'damage': s.damage, 'radius': s.spell_radius,
            })
            return
        self.spell_events.append({
            'kind': 'area_delayed', 'owner': side, 'timer': 0.30, 'x': x, 'y': y,
            'damage': s.damage, 'radius': s.spell_radius,
            'tower_multiplier': s.spell_tower_multiplier, 'crown_tower_damage': (s.crown_tower_damage / 3.0 if s.crown_tower_damage is not None else None), 'targets': 'air_ground',
        })

    def _update_spell_events(self, dt: float):
        keep = []
        for ev in self.spell_events:
            kind = ev['kind']
            if kind == 'fireball':
                dx, dy = ev['tx'] - ev['x'], ev['ty'] - ev['y']
                d = math.hypot(dx, dy)
                step = ev['speed'] * dt
                if d <= step + 1e-9:
                    self._apply_area_spell(ev['owner'], ev['tx'], ev['ty'], ev['radius'],
                                           ev['damage'], ev['tower_multiplier'])
                    continue
                if d > 1e-9:
                    ev['x'] += dx / d * step
                    ev['y'] += dy / d * step
                keep.append(ev)
            elif kind == 'rolling_log':
                travel = min(ev['speed'] * dt, ev['remaining'])
                y0 = ev['y']
                y1 = y0 + ev['dir'] * travel
                half_width = ev['width'] / 2.0
                for ent in list(self.entities.values()):
                    if (not ent.alive or ent.owner == ev['owner'] or ent.transport != 'ground'
                            or ent.id in ev['hit_ids']):
                        continue
                    if self._point_segment_distance(ent.x, ent.y, ev['x'], y0, ev['x'], y1) <= half_width + ent.radius:
                        mult = ev['tower_multiplier'] if ent.kind == 'tower' else 1.0
                        self._damage(ent, ev['damage'] * mult)
                        ev['hit_ids'].add(ent.id)
                        if ent.alive and ent.kind == 'troop':
                            ent.y += ev['dir'] * 0.7
                ev['y'] = y1
                ev['remaining'] -= travel
                if ev['remaining'] > 1e-9:
                    keep.append(ev)
            elif kind in ('area_delayed', 'lightning_delayed', 'royal_delivery'):
                ev['timer'] -= dt
                if ev['timer'] > 1e-9:
                    keep.append(ev)
                    continue
                if kind == 'royal_delivery':
                    for ent in list(self.entities.values()):
                        if (ent.alive and ent.owner != ev['owner'] and ent.kind == 'troop'
                                and self._dist_xy(ev['x'], ev['y'], ent.x, ent.y) <= ev['radius'] + ent.radius):
                            self._damage(ent, ev['damage'])
                    # Level-16 Royal Recruit with shield; shield absorption is represented as extra HP here.
                    recruit = CardSpec('Royal Recruit', 'troop', 0, hp=2110, damage=218, hit_speed=1.3,
                                       first_hit=0.4, move_speed=1.0, attack_range=1.2, sight_range=5.5,
                                       radius=0.42, deploy_time=0.0)
                    self._spawn_from_spec(ev['owner'], recruit, ev['x'], ev['y'], kind='troop', source_card='Royal Delivery')
                elif kind == 'lightning_delayed':
                    enemies = [e for e in self.entities.values()
                               if e.alive and e.owner != ev['owner']
                               and self._dist_xy(ev['x'], ev['y'], e.x, e.y) <= ev['radius'] + e.radius]
                    enemies.sort(key=lambda e: (-e.hp, e.id))
                    for ent in enemies[:3]:
                        amount = (ev.get('crown_tower_damage') if ent.kind == 'tower' and ev.get('crown_tower_damage') is not None
                                  else ev['damage'] * (ev['tower_multiplier'] if ent.kind == 'tower' else 1.0))
                        self._damage(ent, amount)
                        if ent.alive:
                            ent.status['stun_remaining'] = max(ent.status.get('stun_remaining', 0.0), 0.5)
                else:
                    self._apply_area_spell(ev['owner'], ev['x'], ev['y'], ev['radius'],
                                           ev['damage'], ev['tower_multiplier'], ev.get('crown_tower_damage'))
            else:
                keep.append(ev)
        self.spell_events = keep

    def _apply_area_spell(self, side: str, x: float, y: float, radius: float, damage: float, tower_multiplier: float, crown_tower_damage=None):
        for ent in list(self.entities.values()):
            if not ent.alive or ent.owner == side:
                continue
            if self._dist_xy(x, y, ent.x, ent.y) <= radius + ent.radius:
                amount = crown_tower_damage if ent.kind == 'tower' and crown_tower_damage is not None else damage * (tower_multiplier if ent.kind == 'tower' else 1.0)
                self._damage(ent, amount)

    # ------------------------------------------------------------------
    # Tick loop
    # ------------------------------------------------------------------
    def _tick_once(self):
        dt = self.tick_s
        self.tick += 1
        self.time_s += dt
        self._regen_elixir(dt)
        self._update_statuses(dt)
        self._update_specials(dt)
        self._update_spell_events(dt)
        self._update_lifetimes(dt)
        self._update_deploy(dt)
        self._acquire_targets()
        self._move_units(dt)
        self._resolve_collisions()
        self._special_pre_attacks(dt)
        self._attacks(dt)
        self._move_projectiles(dt)
        self._cleanup()
        self._check_end()

    def _regen_elixir(self, dt: float):
        interval = 2.8 if self.time_s < 120 else (1.4 if self.time_s < 240 else 2.8 / 3.0)
        for p in self.players.values():
            p.elixir = min(10.0, p.elixir + dt / interval)

    def _update_statuses(self, dt: float):
        for e in self.entities.values():
            if not e.alive:
                continue
            for key in ('slow_remaining', 'rage_remaining', 'stun_remaining'):
                if key in e.status:
                    e.status[key] = max(0.0, e.status[key] - dt)

    def _update_specials(self, dt: float):
        for e in list(self.entities.values()):
            if not e.alive:
                continue
            if e.is_king and e.special.get('king_activation_remaining') is not None:
                rem = max(0.0, float(e.special['king_activation_remaining']) - dt)
                e.special['king_activation_remaining'] = rem
                if rem <= 1e-9:
                    e.special['king_active'] = True
                    e.special['king_activation_remaining'] = None
            if 'ability_cooldown_remaining' in e.special:
                e.special['ability_cooldown_remaining'] = max(
                    0.0, e.special['ability_cooldown_remaining'] - dt
                )
            if 'sniper_cooldown' in e.special:
                e.special['sniper_cooldown'] = max(0.0, e.special['sniper_cooldown'] - dt)
            if 'spear_cooldown' in e.special:
                e.special['spear_cooldown'] = max(0.0, e.special['spear_cooldown'] - dt)

            pulses = e.special.get('snowstorm_pulses')
            if pulses:
                new_pulses = []
                for t in pulses:
                    t -= dt
                    if t <= 1e-9:
                        self._snowstorm_pulse(e)
                    else:
                        new_pulses.append(t)
                e.special['snowstorm_pulses'] = new_pulses

            if 'royal_rescue_timer' in e.special:
                e.special['royal_rescue_timer'] -= dt
                if e.special['royal_rescue_timer'] <= 0:
                    e.special.pop('royal_rescue_timer', None)
                    self._royal_rescue(e)

        self._update_rune_enchantments(dt)

    def _update_rune_enchantments(self, dt: float):
        # Each living Rune Giant enchants the two nearest allied troops in 8.5 tiles.
        # Enchantment survives its source's death for 5 seconds.
        runes = [r for r in self.entities.values() if r.alive and r.special.get('tag') == 'rune_giant' and r.deploy_remaining <= 0]
        active_sources = {r.id for r in runes}
        for r in runes:
            allies = [a for a in self.entities.values() if a.alive and a.owner == r.owner and a.kind == 'troop'
                      and a.id != r.id and self._dist(r, a) <= 8.5 + a.radius]
            allies.sort(key=lambda a: (self._dist(r, a), a.id))
            chosen = {a.id for a in allies[:2]}
            for a in allies:
                if a.id in chosen:
                    a.special['rune_source_id'] = r.id
                    a.special['rune_expiry'] = None
                    a.special.setdefault('rune_attack_count', 0)
        for a in self.entities.values():
            if not a.alive or 'rune_source_id' not in a.special:
                continue
            src = a.special['rune_source_id']
            if src in active_sources:
                continue
            expiry = a.special.get('rune_expiry')
            if expiry is None:
                a.special['rune_expiry'] = 5.0
            else:
                expiry = max(0.0, expiry - dt); a.special['rune_expiry'] = expiry
                if expiry <= 1e-9:
                    for k in ('rune_source_id','rune_expiry','rune_attack_count'):
                        a.special.pop(k, None)

    def _update_lifetimes(self, dt: float):
        for e in list(self.entities.values()):
            if e.alive and e.lifetime_remaining is not None:
                e.lifetime_remaining -= dt
                if e.lifetime_remaining <= 0:
                    self._kill_entity(e)

    def _update_deploy(self, dt: float):
        for e in self.entities.values():
            if e.alive and e.deploy_remaining > 0:
                e.deploy_remaining = max(0.0, e.deploy_remaining - dt)

    # ------------------------------------------------------------------
    # Targeting / movement / pathing
    # ------------------------------------------------------------------
    def _can_target_transport(self, attacker: Entity, target: Entity) -> bool:
        if attacker.targets == 'air_ground':
            return True
        if attacker.targets == 'ground':
            return target.transport == 'ground'
        if attacker.targets == 'building':
            return target.kind in ('building', 'tower')
        return False

    def _valid_target(self, attacker: Entity, target: Entity) -> bool:
        if not target.alive or target.owner == attacker.owner:
            return False
        return self._can_target_transport(attacker, target)

    def _acquire_targets(self):
        alive = [e for e in self.entities.values() if e.alive]
        for a in alive:
            if a.deploy_remaining > 0 or a.status.get('stun_remaining', 0) > 0:
                continue
            if a.is_king and not a.special.get('king_active', False):
                a.target_id = None
                continue
            cur = self.entities.get(a.target_id) if a.target_id else None
            if cur and self._valid_target(a, cur):
                if self._dist(a, cur) <= a.sight_range * 1.35 + cur.radius:
                    continue
            candidates = [t for t in alive if self._valid_target(a, t)]
            if not candidates:
                a.target_id = None
                continue
            in_sight = [t for t in candidates if self._dist(a, t) <= a.sight_range + t.radius]
            if in_sight:
                chosen = min(in_sight, key=lambda t: (self._dist(a, t), t.id))
            else:
                if a.kind in ('tower', 'building'):
                    a.target_id = None
                    continue
                towers = [t for t in candidates if t.kind == 'tower']
                chosen = min(towers or candidates, key=lambda t: (self._route_distance(a, t), t.id))
            a.target_id = chosen.id

    def _effective_move_speed(self, e: Entity) -> float:
        speed = e.move_speed
        if e.status.get('slow_remaining', 0) > 0:
            speed *= e.status.get('slow_multiplier', 0.7)
        if e.status.get('rage_remaining', 0) > 0:
            speed *= e.status.get('rage_multiplier', 1.35)
        return speed

    def _effective_hit_speed(self, e: Entity) -> float:
        hs = e.hit_speed
        if e.special.get('tag') == 'little_prince':
            count = int(e.special.get('lp_attack_count', 0))
            stage = 0 if count < 2 else (1 if count < 4 else 2)
            hs = (1.2, 0.8, 0.4)[stage]
        if e.status.get('slow_remaining', 0) > 0:
            hs /= max(1e-6, e.status.get('slow_multiplier', 0.7))
        if e.status.get('rage_remaining', 0) > 0:
            hs /= max(1e-6, e.status.get('rage_multiplier', 1.35))
        return hs

    def _move_units(self, dt: float):
        for a in self.entities.values():
            if (not a.alive or a.kind != 'troop' or a.deploy_remaining > 0 or a.move_speed <= 0
                    or a.status.get('stun_remaining', 0) > 0):
                continue
            t = self.entities.get(a.target_id) if a.target_id else None
            if not t or not t.alive:
                continue
            if self._dist(a, t) <= a.attack_range + a.radius + t.radius:
                if a.special.get('tag') == 'little_prince':
                    a.special['lp_move_grace'] = 0.0
                continue
            wx, wy = self._next_waypoint(a, t)
            dx, dy = wx - a.x, wy - a.y
            d = math.hypot(dx, dy)
            if d < 1e-9:
                continue
            step = min(self._effective_move_speed(a) * dt, d)
            if step > 0:
                a.x += dx / d * step
                a.y += dy / d * step
                if a.special.get('tag') == 'little_prince':
                    a.special['lp_move_grace'] = float(a.special.get('lp_move_grace', 0.0)) + dt
                    if a.special['lp_move_grace'] > 0.3 + 1e-9:
                        a.special['lp_attack_count'] = 0

    def _next_waypoint(self, a: Entity, t: Entity):
        if a.transport == 'air':
            return t.x, t.y
        opposite = ((a.y < -self.RIVER_HALF and t.y > self.RIVER_HALF)
                    or (a.y > self.RIVER_HALF and t.y < -self.RIVER_HALF))
        if opposite:
            bx = min(self.BRIDGES, key=lambda x: abs(a.x - x) + 0.35 * abs(t.x - x))
            if abs(a.y) > self.RIVER_HALF + 0.15:
                return bx, 0.0
        return t.x, t.y

    def _resolve_collisions(self):
        troops = [e for e in self.entities.values()
                  if e.alive and e.kind == 'troop' and e.deploy_remaining <= 0]
        for i in range(len(troops)):
            for j in range(i + 1, len(troops)):
                a, b = troops[i], troops[j]
                if a.transport != b.transport:
                    continue
                dx, dy = b.x - a.x, b.y - a.y
                d = math.hypot(dx, dy)
                min_d = a.radius + b.radius
                if d < min_d:
                    if d <= 1e-7:
                        # Deterministic axis prevents permanently overlapping troops.
                        nx, ny = (1.0, 0.0) if a.id < b.id else (-1.0, 0.0)
                        d = 0.0
                    else:
                        nx, ny = dx / d, dy / d
                    overlap = (min_d - d) * 0.5
                    a.x = max(-self.ARENA_X + a.radius, min(self.ARENA_X - a.radius, a.x - nx * overlap))
                    a.y = max(-self.ARENA_Y + a.radius, min(self.ARENA_Y - a.radius, a.y - ny * overlap))
                    b.x = max(-self.ARENA_X + b.radius, min(self.ARENA_X - b.radius, b.x + nx * overlap))
                    b.y = max(-self.ARENA_Y + b.radius, min(self.ARENA_Y - b.radius, b.y + ny * overlap))

    # ------------------------------------------------------------------
    # Special mechanics
    # ------------------------------------------------------------------
    def _special_pre_attacks(self, dt: float):
        for e in list(self.entities.values()):
            if not e.alive or e.deploy_remaining > 0 or e.status.get('stun_remaining', 0) > 0:
                continue
            tag = e.special.get('tag')
            if tag == 'evo_musketeer':
                self._try_musketeer_snipe(e)
            elif tag == 'evo_elite_barbarians':
                self._try_ebarbs_spear(e)
            elif tag in ('skeleton_barrel', 'evo_skeleton_barrel'):
                self._try_skeleton_barrel_contact(e)

    def _try_musketeer_snipe(self, e: Entity):
        if e.special.get('sniper_ammo', 0) <= 0 or e.special.get('sniper_cooldown', 0) > 0:
            return
        candidates = []
        for t in self.entities.values():
            if not t.alive or t.owner == e.owner or t.kind == 'tower':
                continue
            if not self._can_target_transport(e, t):
                continue
            d = self._dist(e, t)
            if 6.0 <= d <= 30.0:
                candidates.append(t)
        if not candidates:
            return
        target = min(candidates, key=lambda t: (self._dist(e, t), t.id))
        p = Projectile(self._id(), e.owner, e.id, target.id, e.x, e.y,
                       26.5, 392.0, 0.0, tag='musketeer_sniper')
        self.projectiles[p.id] = p
        e.special['sniper_ammo'] -= 1
        e.special['sniper_cooldown'] = 1.0

    def _try_ebarbs_spear(self, e: Entity):
        if e.special.get('spear_cooldown', 0) > 0:
            return
        candidates = []
        for t in self.entities.values():
            if not t.alive or t.owner == e.owner or t.transport != 'ground':
                continue
            d = self._dist(e, t)
            if 3.0 <= d <= 4.5:
                candidates.append(t)
        if not candidates:
            return
        t = min(candidates, key=lambda z: (self._dist(e, z), z.id))
        # Supercell does not publish spear damage; keep it an explicit calibration constant.
        self._damage(t, 354.0)
        self._apply_rage_path(e.owner, e.x, e.y, t.x, t.y, duration=2.0)
        e.special['spear_cooldown'] = 5.0

    def _apply_rage_path(self, owner: str, x1: float, y1: float, x2: float, y2: float, duration: float):
        for ally in self.entities.values():
            if not ally.alive or ally.owner != owner:
                continue
            if self._point_segment_distance(ally.x, ally.y, x1, y1, x2, y2) <= 1.0 + ally.radius:
                ally.status['rage_remaining'] = max(ally.status.get('rage_remaining', 0.0), duration)
                ally.status['rage_multiplier'] = 1.35

    def _try_skeleton_barrel_contact(self, e: Entity):
        t = self.entities.get(e.target_id) if e.target_id else None
        if not t or not t.alive:
            return
        if self._dist(e, t) <= e.attack_range + e.radius + t.radius:
            while e.alive and e.special.get('barrels_left', 0) > 0:
                self._drop_barrel(e)
            self._kill_entity(e, trigger_death=False)

    def _drop_barrel(self, e: Entity):
        barrels = int(e.special.get('barrels_left', 0))
        if barrels <= 0:
            return
        e.special['barrels_left'] = barrels - 1
        dmg = float(e.special.get('barrel_death_damage', 145.0))
        for target in list(self.entities.values()):
            if target.alive and target.owner != e.owner and self._dist(e, target) <= 2.0 + target.radius:
                mult = 0.35 if target.kind == 'tower' else 1.0
                self._damage(target, dmg * mult)
        n = int(e.special.get('skeletons_per_barrel', 7))
        sk = CARD_SPECS['Skeletons']
        for i in range(n):
            angle = 2 * math.pi * i / max(1, n)
            r = 0.55
            self._spawn_from_spec(e.owner, sk,
                                  e.x + math.cos(angle) * r,
                                  e.y + math.sin(angle) * r,
                                  kind='troop', source_card=e.source_card)

    def _snowstorm_pulse(self, hero: Entity):
        if not hero.alive:
            return
        for e in list(self.entities.values()):
            if not e.alive or e.owner == hero.owner:
                continue
            if self._dist(hero, e) <= 4.0 + e.radius:
                self._damage(e, 69.0)
                if e.alive:
                    e.status['slow_remaining'] = max(e.status.get('slow_remaining', 0.0), 2.0)
                    e.status['slow_multiplier'] = 0.70

    def _royal_rescue(self, prince: Entity):
        if not prince.alive:
            return
        direction = 1.0 if prince.owner == 'blue' else -1.0
        x1, y1 = prince.x, prince.y - direction * 0.8
        x2, y2 = prince.x, prince.y + direction * 4.0
        for e in list(self.entities.values()):
            # Royal Rescue affects opposing ground troops, not buildings/towers.
            if not e.alive or e.owner == prince.owner or e.transport != 'ground' or e.kind != 'troop':
                continue
            if self._point_segment_distance(e.x, e.y, x1, y1, x2, y2) <= 1.0 + e.radius:
                self._damage(e, 515.0)
                if e.alive:
                    # Push is strongest around the charge sweet spot and tapers toward its ends.
                    u = max(0.0, min(1.0, ((e.y - y1) * direction) / max(1e-6, (y2 - y1) * direction)))
                    push = 2.5 * max(0.0, 1.0 - abs(u - 0.55) / 0.55)
                    e.y += direction * push
        guardian = CardSpec(
            'Guardienne', 'troop', 0, hp=2556, damage=374, hit_speed=1.2,
            first_hit=0.5, move_speed=1.0, attack_range=1.2,
            sight_range=5.5, radius=0.42, deploy_time=0.3,
        )
        self._spawn_from_spec(prince.owner, guardian, prince.x, prince.y + direction * 3.2,
                              kind='troop', source_card='Little Prince')

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------
    def _attacks(self, dt: float):
        for a in list(self.entities.values()):
            if not a.alive or a.deploy_remaining > 0 or a.status.get('stun_remaining', 0) > 0:
                continue
            if a.is_king and not a.special.get('king_active', False):
                continue
            a.attack_cooldown = max(0.0, a.attack_cooldown - dt)
            t = self.entities.get(a.target_id) if a.target_id else None
            if not t or not self._valid_target(a, t):
                continue
            in_range = self._dist(a, t) <= a.attack_range + a.radius + t.radius
            if not in_range or a.attack_cooldown > 0:
                continue

            tag = a.special.get('tag')
            if tag in ('skeleton_barrel', 'evo_skeleton_barrel'):
                continue
            if tag == 'electro_spirit':
                self._electro_spirit_chain(a, t)
                continue

            a.attack_cooldown = self._effective_hit_speed(a)
            attack_damage = a.damage
            if 'rune_source_id' in a.special:
                n = int(a.special.get('rune_attack_count', 0)) + 1
                a.special['rune_attack_count'] = n
                if n % 3 == 0:
                    # Level-16 bonus is isolated as a calibration constant until native capture validates it.
                    attack_damage += 351.0
            if tag == 'executioner':
                self._launch_executioner_axe(a, t, attack_damage)
            elif a.projectile_speed:
                p = Projectile(self._id(), a.owner, a.id, t.id, a.x, a.y,
                               a.projectile_speed, attack_damage, a.splash_radius)
                self.projectiles[p.id] = p
            else:
                self._apply_hit(a, t, attack_damage, a.splash_radius)
            if tag == 'little_prince':
                a.special['lp_attack_count'] = int(a.special.get('lp_attack_count', 0)) + 1
                a.special['lp_move_grace'] = 0.0

    def _launch_executioner_axe(self, source: Entity, target: Entity, damage: float):
        dx, dy = target.x-source.x, target.y-source.y
        d = max(1e-9, math.hypot(dx,dy)); ux,uy=dx/d,dy/d
        # Public projectile range is 7.5 tiles. One projectile hits on outbound and return passes.
        p=Projectile(self._id(),source.owner,source.id,target.id,source.x,source.y,5.5,damage,0.0,
                     tag='executioner_out',vx=ux,vy=uy,remaining=7.5,hit_ids=[])
        self.projectiles[p.id]=p

    def _move_executioner_axe(self, p: Projectile, dt: float):
        src=self.entities.get(p.source_id)
        if not src:
            self.projectiles.pop(p.id,None); return
        if p.tag == 'executioner_return':
            dx, dy = src.x - p.x, src.y - p.y
            home_d = math.hypot(dx, dy)
            if home_d <= p.speed * dt + src.radius:
                self.projectiles.pop(p.id, None)
                return
            if home_d > 1e-9:
                p.vx, p.vy = dx / home_d, dy / home_d
        step=min(p.speed*dt, p.remaining if p.remaining is not None else p.speed*dt)
        x0,y0=p.x,p.y; p.x += p.vx*step; p.y += p.vy*step
        for ent in list(self.entities.values()):
            if not ent.alive or ent.owner==p.owner or ent.id in p.hit_ids: continue
            if self._point_segment_distance(ent.x,ent.y,x0,y0,p.x,p.y) <= 1.0 + ent.radius:
                self._damage(ent,p.damage); p.hit_ids.append(ent.id)
        if p.remaining is not None: p.remaining -= step
        if p.remaining is not None and p.remaining <= 1e-9:
            if p.tag=='executioner_out':
                p.tag='executioner_return'; p.vx=-p.vx; p.vy=-p.vy; p.remaining=7.5; p.hit_ids=[]
            else:
                self.projectiles.pop(p.id,None)

    def _electro_spirit_chain(self, source: Entity, first: Entity):
        current = first
        hit_ids = set()
        for _ in range(9):
            if not current or current.id in hit_ids or not current.alive:
                break
            hit_ids.add(current.id)
            self._damage(current, source.damage)
            if current.alive:
                current.status['stun_remaining'] = max(current.status.get('stun_remaining', 0.0), 0.5)
            candidates = [e for e in self.entities.values()
                          if e.alive and e.owner != source.owner and e.id not in hit_ids
                          and self._dist(current, e) <= 4.0 + e.radius]
            current = min(candidates, key=lambda e: (self._dist(current, e), e.id)) if candidates else None
        self._kill_entity(source, trigger_death=False)

    def _move_projectiles(self, dt: float):
        for p in list(self.projectiles.values()):
            if p.tag in ('executioner_out','executioner_return'):
                self._move_executioner_axe(p, dt); continue
            t = self.entities.get(p.target_id)
            if not t or not t.alive:
                self.projectiles.pop(p.id, None)
                continue
            dx, dy = t.x - p.x, t.y - p.y
            d = math.hypot(dx, dy)
            step = p.speed * dt
            if d <= step + t.radius:
                source = self.entities.get(p.source_id)
                if source and source.alive:
                    self._apply_hit(source, t, p.damage, p.splash_radius)
                elif t.alive:
                    self._damage(t, p.damage)
                self.projectiles.pop(p.id, None)
            elif d > 1e-9:
                p.x += dx / d * step
                p.y += dy / d * step

    def _apply_hit(self, source: Entity, target: Entity, damage: float, splash_radius: float):
        if splash_radius <= 0:
            self._damage(target, damage)
        else:
            for e in list(self.entities.values()):
                if e.alive and e.owner != source.owner and self._dist(target, e) <= splash_radius + e.radius:
                    self._damage(e, damage)

        if source.alive and source.special.get('tag') == 'evo_skeletons':
            self._evo_skeleton_multiply(source)

    def _evo_skeleton_multiply(self, source: Entity):
        group = source.special.get('evo_group')
        if group is None:
            return
        alive_group = [e for e in self.entities.values()
                       if e.alive and e.owner == source.owner
                       and e.special.get('tag') == 'evo_skeletons'
                       and e.special.get('evo_group') == group]
        if len(alive_group) >= 8:
            return
        spec = CARD_SPECS['Skeletons Evolution']
        angle = (source.id * 2.399963229728653) % (2 * math.pi)
        e = self._spawn_from_spec(source.owner, spec,
                                  source.x + math.cos(angle) * 0.35,
                                  source.y + math.sin(angle) * 0.35,
                                  kind='troop', source_card='Skeletons Evolution',
                                  is_evolved=True, special_override='evo_skeletons')
        e.deploy_remaining = 0.0
        e.special['evo_group'] = group

    def _damage(self, e: Entity, amount: float):
        if not e.alive or amount <= 0:
            return
        if e.is_king and not e.special.get('king_active', False) and e.special.get('king_activation_remaining') is None:
            e.special['king_active'] = True
            e.special['king_activation_remaining'] = None
        before_fraction = e.hp / e.max_hp if e.max_hp else 0.0
        e.hp -= amount
        after_fraction = e.hp / e.max_hp if e.max_hp else 0.0

        if (e.alive and e.special.get('tag') == 'evo_skeleton_barrel'
                and e.special.get('barrels_left', 0) == 2
                and before_fraction > 0.75 >= after_fraction):
            self._drop_barrel(e)
            e.special['first_barrel_dropped'] = True

        if e.hp <= 0:
            e.hp = 0.0
            self._kill_entity(e)

    def _kill_entity(self, e: Entity, trigger_death: bool = True):
        if not e.alive:
            return
        if trigger_death and e.special.get('tag') in ('skeleton_barrel', 'evo_skeleton_barrel'):
            while e.special.get('barrels_left', 0) > 0:
                self._drop_barrel(e)
        e.alive = False
        if e.is_princess:
            kings = [k for k in self.entities.values() if k.owner == e.owner and k.is_king and k.alive]
            if kings:
                k = kings[0]
                if not k.special.get('king_active', False):
                    k.special['king_active'] = True
                    k.special['king_activation_remaining'] = None

    # ------------------------------------------------------------------
    # Cleanup / match end
    # ------------------------------------------------------------------
    def _cleanup(self):
        for e in self.entities.values():
            if e.target_id and (e.target_id not in self.entities or not self.entities[e.target_id].alive):
                e.target_id = None

    def _check_end(self):
        kings = {s: [e for e in self.entities.values() if e.owner == s and e.is_king] for s in SIDES}
        dead_kings = [s for s in SIDES if kings[s] and not kings[s][0].alive]
        if len(dead_kings) == 2:
            self.done = True; self.winner = None; return
        if len(dead_kings) == 1:
            self.done = True; self.winner = OPP[dead_kings[0]]; return

        crowns = self._crowns_by_owner()
        # End of regulation: more crowns wins; tied crowns enter 2-minute sudden-death overtime.
        if not self._overtime_started and self.time_s >= 180.0:
            if crowns['blue'] != crowns['red']:
                self.done = True
                self.winner = 'blue' if crowns['blue'] > crowns['red'] else 'red'
                return
            self._overtime_started = True
            self._overtime_crowns = dict(crowns)

        # In overtime the first *net* new crown wins. If both gain one in the same tick, play continues.
        if self._overtime_started and self.time_s < 300.0:
            gain_b = crowns['blue'] - self._overtime_crowns['blue']
            gain_r = crowns['red'] - self._overtime_crowns['red']
            if gain_b > gain_r:
                self.done = True; self.winner = 'blue'; return
            if gain_r > gain_b:
                self.done = True; self.winner = 'red'; return
            if gain_b == gain_r and gain_b > 0:
                self._overtime_crowns = dict(crowns)

        if self.time_s >= 300.0:
            # Tiebreaker: all surviving Crown Towers lose HP together, so the lowest
            # absolute-HP tower determines the loser. Exact-tie -> draw in this model.
            mins = {}
            for side in SIDES:
                towers = [e.hp for e in self.entities.values() if e.owner == side and e.kind == 'tower' and e.alive]
                mins[side] = min(towers) if towers else 0.0
            if abs(mins['blue'] - mins['red']) <= 1e-9:
                self.winner = None
            else:
                self.winner = 'blue' if mins['blue'] > mins['red'] else 'red'
            self.done = True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _crowns_by_owner(self):
        out = {}
        for side in SIDES:
            enemy = OPP[side]
            king = next((e for e in self.entities.values() if e.owner == enemy and e.is_king), None)
            if king is not None and not king.alive:
                out[side] = 3
                continue
            out[side] = sum(1 for e in self.entities.values() if e.owner == enemy and e.is_princess and not e.alive)
        return out

    def _tower_hp_by_owner(self):
        return {s: sum(e.hp for e in self.entities.values()
                       if e.alive and e.owner == s and e.kind == 'tower') for s in SIDES}

    def _dist(self, a: Entity, b: Entity):
        return math.hypot(a.x - b.x, a.y - b.y)

    def _dist_xy(self, x1, y1, x2, y2):
        return math.hypot(x1 - x2, y1 - y2)

    def _route_distance(self, a: Entity, b: Entity):
        wx, wy = self._next_waypoint(a, b)
        if (wx, wy) == (b.x, b.y):
            return self._dist(a, b)
        return self._dist_xy(a.x, a.y, wx, wy) + self._dist_xy(wx, wy, b.x, b.y)

    def _point_segment_distance(self, px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        denom = dx * dx + dy * dy
        if denom <= 1e-12:
            return self._dist_xy(px, py, x1, y1)
        t = ((px - x1) * dx + (py - y1) * dy) / denom
        t = max(0.0, min(1.0, t))
        qx, qy = x1 + t * dx, y1 + t * dy
        return self._dist_xy(px, py, qx, qy)

    def _public_spell_event(self, ev: dict):
        out = {}
        for k, v in ev.items():
            if k == 'hit_ids':
                continue
            out[k] = round(v, 4) if isinstance(v, float) else v
        return out

    def _entity_dict(self, e: Entity):
        d = asdict(e)
        d['hp_fraction'] = round(e.hp / e.max_hp if e.max_hp else 0.0, 5)
        for k in ('x', 'y', 'hp', 'max_hp', 'attack_cooldown', 'deploy_remaining'):
            if isinstance(d.get(k), float):
                d[k] = round(d[k], 4)
        for container in ('status', 'special'):
            clean = {}
            for k, v in d.get(container, {}).items():
                clean[k] = round(v, 4) if isinstance(v, float) else v
            d[container] = clean
        return d
