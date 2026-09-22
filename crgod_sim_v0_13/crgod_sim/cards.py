from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional

TargetKind = Literal['ground', 'air_ground', 'building']
CardKind = Literal['troop', 'building', 'spell']
TransportKind = Literal['ground', 'air']

@dataclass(frozen=True)
class CardSpec:
    name: str
    kind: CardKind
    elixir: int
    hp: float = 0.0
    damage: float = 0.0
    hit_speed: float = 1.0
    first_hit: float = 0.35
    move_speed: float = 0.0
    attack_range: float = 0.8
    sight_range: float = 5.5
    radius: float = 0.35
    targets: TargetKind = 'ground'
    transport: TransportKind = 'ground'
    projectile_speed: Optional[float] = None
    splash_radius: float = 0.0
    lifetime: Optional[float] = None
    count: int = 1
    deploy_spread: float = 0.45
    deploy_time: float = 1.0
    spell_radius: float = 0.0
    spell_tower_multiplier: float = 0.35
    crown_tower_damage: Optional[float] = None
    special: Optional[str] = None
    evolution_of: Optional[str] = None
    evolution_cycles: int = 0
    hero_ability: Optional[str] = None
    hero_ability_cost: int = 0
    hero_ability_cooldown: float = 0.0

# CR-God v0.4 mechanics-first calibration values.
# Timing/ability mechanics for highlighted cards follow current public descriptions,
# while many raw HP/damage/radius values remain calibration placeholders until the
# native/APK comparison harness replaces them.
CARD_SPECS: dict[str, CardSpec] = {
    # ---- Existing/basic cards ----
    'Knight': CardSpec('Knight', 'troop', 3, hp=1450, damage=170, hit_speed=1.2,
                       first_hit=0.45, move_speed=1.0, attack_range=0.8, sight_range=5.5, radius=0.38),
    'Skeletons': CardSpec('Skeletons', 'troop', 1, hp=130, damage=130, hit_speed=1.1,
                          first_hit=0.50, move_speed=1.35, attack_range=0.5, sight_range=5.5,
                          radius=0.22, count=3, deploy_spread=0.42),
    'Archers': CardSpec('Archers', 'troop', 3, hp=300, damage=105, hit_speed=1.0,
                        first_hit=0.45, move_speed=1.0, attack_range=5.0, sight_range=6.5,
                        radius=0.30, projectile_speed=9.0, count=2, deploy_spread=0.55,
                        targets='air_ground'),
    'Musketeer': CardSpec('Musketeer', 'troop', 4, hp=1160, damage=346, hit_speed=1.0,
                          first_hit=0.70, move_speed=1.0, attack_range=6.0, sight_range=7.0,
                          radius=0.32, projectile_speed=10.0, targets='air_ground'),
    'Hog Rider': CardSpec('Hog Rider', 'troop', 4, hp=2738, damage=483, hit_speed=1.6,
                          first_hit=0.60, move_speed=1.65, attack_range=0.85, sight_range=6.0,
                          radius=0.43, targets='building'),
    'Cannon': CardSpec('Cannon', 'building', 3, hp=1321, damage=266, hit_speed=0.9,
                       first_hit=0.45, attack_range=5.5, sight_range=6.5, radius=0.55,
                       projectile_speed=11.0, lifetime=30.0, targets='ground'),
    'Fireball': CardSpec('Fireball', 'spell', 4, damage=902, spell_radius=2.5,
                         spell_tower_multiplier=0.30, special='fireball'),
    'Arrows': CardSpec('Arrows', 'spell', 3, damage=588, spell_radius=3.5,
                       spell_tower_multiplier=0.0, crown_tower_damage=120, special='arrows'),
    'Valkyrie': CardSpec('Valkyrie', 'troop', 4, hp=1900, damage=270, hit_speed=1.5,
                         first_hit=0.45, move_speed=1.0, attack_range=1.2, sight_range=5.5,
                         radius=0.42, splash_radius=1.2),
    'Lightning': CardSpec('Lightning', 'spell', 6, damage=1690, spell_radius=3.5,
                          spell_tower_multiplier=0.0, crown_tower_damage=424, special='lightning'),

    # ---- Fixed Deck A: 2.6 Hog, 2026 variant ----
    'Electro Spirit': CardSpec('Electro Spirit', 'troop', 1, hp=370, damage=209,
                               hit_speed=0.3, first_hit=0.30, move_speed=1.65,
                               attack_range=2.5, sight_range=5.5, radius=0.20,
                               targets='air_ground', special='electro_spirit'),
    'The Log': CardSpec('The Log', 'spell', 2, damage=467, spell_tower_multiplier=0.15, special='the_log'),
    'Hero Ice Golem': CardSpec('Hero Ice Golem', 'troop', 2, hp=1930, damage=135,
                               hit_speed=2.5, first_hit=1.5, move_speed=0.75,
                               attack_range=1.2, sight_range=5.5, radius=0.45,
                               targets='building', special='hero_ice_golem',
                               hero_ability='snowstorm', hero_ability_cost=2,
                               hero_ability_cooldown=17.0),
    'Skeletons Evolution': CardSpec('Skeletons Evolution', 'troop', 1, hp=130, damage=130,
                                    hit_speed=1.1, first_hit=0.50, move_speed=1.35,
                                    attack_range=0.5, sight_range=5.5, radius=0.22,
                                    count=3, deploy_spread=0.42,
                                    special='evo_skeletons', evolution_of='Skeletons', evolution_cycles=2),
    'Musketeer Evolution': CardSpec('Musketeer Evolution', 'troop', 4, hp=1160, damage=346,
                                    hit_speed=1.0, first_hit=0.70, move_speed=1.0,
                                    attack_range=6.0, sight_range=7.0, radius=0.32,
                                    projectile_speed=10.0, targets='air_ground',
                                    special='evo_musketeer', evolution_of='Musketeer', evolution_cycles=2),

    # ---- Fixed Deck B core ----
    'Little Prince': CardSpec('Little Prince', 'troop', 3, hp=1115, damage=167,
                              hit_speed=1.2, first_hit=0.40, move_speed=1.0,
                              attack_range=5.5, sight_range=7.0, radius=0.28,
                              projectile_speed=10.0, targets='air_ground',
                              special='little_prince', hero_ability='royal_rescue',
                              hero_ability_cost=3, hero_ability_cooldown=30.0),
    'Elite Barbarians': CardSpec('Elite Barbarians', 'troop', 6, hp=2143, damage=613,
                                 hit_speed=1.4, first_hit=0.5, move_speed=1.5,
                                 attack_range=1.2, sight_range=6.0, radius=0.38,
                                 count=2, deploy_spread=0.65),
    'Elite Barbarians Evolution': CardSpec('Elite Barbarians Evolution', 'troop', 6,
                                           hp=2143, damage=613, hit_speed=1.4,
                                           first_hit=0.5, move_speed=1.5,
                                           attack_range=1.2, sight_range=6.0, radius=0.38,
                                           count=2, deploy_spread=0.65,
                                           special='evo_elite_barbarians',
                                           evolution_of='Elite Barbarians', evolution_cycles=1),
    'Skeleton Barrel': CardSpec('Skeleton Barrel', 'troop', 3, hp=857, damage=0,
                                hit_speed=1.0, first_hit=0.1, move_speed=1.45,
                                attack_range=0.35, sight_range=8.0, radius=0.38,
                                targets='building', transport='air', special='skeleton_barrel'),
    'Skeleton Barrel Evolution': CardSpec('Skeleton Barrel Evolution', 'troop', 3, hp=1071, damage=0,
                                          hit_speed=1.0, first_hit=0.1, move_speed=1.45,
                                          attack_range=0.35, sight_range=8.0, radius=0.40,
                                          targets='building', transport='air',
                                          special='evo_skeleton_barrel',
                                          evolution_of='Skeleton Barrel', evolution_cycles=2),
    # ---- Fixed Deck B remaining cards (level 16 baseline) ----
    'Rune Giant': CardSpec('Rune Giant', 'troop', 4, hp=4253, damage=192, hit_speed=1.5,
                           first_hit=0.5, move_speed=1.0, attack_range=1.2, sight_range=5.5,
                           radius=0.50, targets='building', special='rune_giant'),
    'Executioner': CardSpec('Executioner', 'troop', 5, hp=2045, damage=288, hit_speed=0.9,
                            first_hit=0.5, move_speed=1.0, attack_range=4.5, sight_range=5.5,
                            radius=0.60, targets='air_ground', special='executioner'),
    'Royal Delivery': CardSpec('Royal Delivery', 'spell', 3, damage=587, spell_radius=3.0,
                               spell_tower_multiplier=0.0, special='royal_delivery'),

}

DECK_A_26_HOG = [
    'Hog Rider', 'Fireball', 'The Log', 'Cannon',
    'Electro Spirit', 'Hero Ice Golem', 'Musketeer Evolution', 'Skeletons Evolution'
]

# The user has only specified these three cards for Deck B so far. Do not invent
# the remaining five. `build_deck_b()` turns the core into a runnable 8-card deck
# once those names are known.
DECK_B_CORE = [
    'Little Prince', 'Elite Barbarians Evolution', 'Skeleton Barrel Evolution'
]

DECK_B_VIDEO_20260919 = [
    'Lightning', 'Rune Giant', 'Executioner', 'Little Prince',
    'Elite Barbarians Evolution', 'Skeleton Barrel Evolution', 'Royal Delivery', 'Arrows'
]

def build_deck_b(extra_cards: list[str]) -> list[str]:
    if len(extra_cards) != 5:
        raise ValueError('Deck B still needs exactly five additional cards')
    return DECK_B_CORE + list(extra_cards)

DEFAULT_DECK = [
    'Knight', 'Skeletons', 'Archers', 'Musketeer',
    'Hog Rider', 'Cannon', 'Fireball', 'Arrows'
]
