from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Any

@dataclass
class Entity:
    id: int
    name: str
    owner: str
    kind: str
    x: float
    y: float
    hp: float
    max_hp: float
    damage: float
    hit_speed: float
    first_hit: float
    move_speed: float
    attack_range: float
    sight_range: float
    radius: float
    targets: str = 'ground'
    transport: str = 'ground'
    projectile_speed: Optional[float] = None
    splash_radius: float = 0.0
    lifetime_remaining: Optional[float] = None
    deploy_remaining: float = 0.0
    target_id: Optional[int] = None
    attack_cooldown: float = 0.0
    alive: bool = True
    is_king: bool = False
    is_princess: bool = False
    source_card: Optional[str] = None
    is_evolved: bool = False
    special: dict[str, Any] = field(default_factory=dict)
    status: dict[str, float] = field(default_factory=dict)

@dataclass
class Projectile:
    id: int
    owner: str
    source_id: int
    target_id: int
    x: float
    y: float
    speed: float
    damage: float
    splash_radius: float = 0.0
    tag: Optional[str] = None
    vx: float = 0.0
    vy: float = 0.0
    remaining: Optional[float] = None
    hit_ids: list[int] = field(default_factory=list)

@dataclass
class PlayerState:
    side: str
    elixir: float
    deck: list[str]
    hand: list[str]
    queue: list[str]
    evolution_progress: dict[str, int] = field(default_factory=dict)

@dataclass
class BoardState:
    tick: int
    time_s: float
    phase: str
    players: dict[str, dict]
    entities: list[dict]
    projectiles: list[dict]
    done: bool
    winner: Optional[str]

    def as_dict(self) -> dict:
        return asdict(self)
