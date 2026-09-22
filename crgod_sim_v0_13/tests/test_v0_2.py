from crgod_sim import CRGodEnv, DECK_A_26_HOG, build_deck_b


def advance(env, n):
    for _ in range(n):
        env.step()


def test_deck_a_loads_and_reports_evolutions():
    env = CRGodEnv(seed=2)
    st = env.reset(deck_a=DECK_A_26_HOG)
    evo = st['players']['blue']['evolutions']
    assert evo['Musketeer Evolution']['cycles_required'] == 2
    assert evo['Skeletons Evolution']['cycles_required'] == 2


def test_build_deck_b_requires_exactly_five_extras():
    deck = build_deck_b(['Knight','Cannon','Fireball','Arrows','Valkyrie'])
    assert len(deck) == 8


def test_evolution_cycle_skeletons_becomes_evolved_on_third_play():
    deck = ['Skeletons Evolution','Knight','Archers','Musketeer','Hog Rider','Cannon','Fireball','Arrows']
    env = CRGodEnv(seed=1)
    env.reset(deck_a=deck)
    # Force hand/cycle state for mechanics unit test rather than waiting a full match.
    p = env.players['blue']
    p.elixir = 10
    env.play('blue','Skeletons Evolution',0,-6)
    assert p.evolution_progress['Skeletons Evolution'] == 1
    p.hand[0] = 'Skeletons Evolution'; p.elixir = 10
    env.play('blue','Skeletons Evolution',0,-6)
    assert p.evolution_progress['Skeletons Evolution'] == 2
    p.hand[0] = 'Skeletons Evolution'; p.elixir = 10
    env.play('blue','Skeletons Evolution',0,-6)
    assert p.evolution_progress['Skeletons Evolution'] == 0
    assert any(e.alive and e.owner == 'blue' and e.is_evolved and e.special.get('tag') == 'evo_skeletons'
               for e in env.entities.values())


def test_hero_ice_golem_ability_costs_elixir_and_schedules_pulses():
    deck = ['Hero Ice Golem','Knight','Skeletons','Archers','Musketeer','Hog Rider','Cannon','Fireball']
    env = CRGodEnv(seed=1)
    env.reset(deck_a=deck)
    env.players['blue'].elixir = 10
    env.play('blue','Hero Ice Golem',0,-5)
    advance(env, 21)
    before = env.players['blue'].elixir
    env.activate_ability('blue','Hero Ice Golem')
    hero = max(e for e in env.entities.values() if e.source_card == 'Hero Ice Golem')
    assert env.players['blue'].elixir <= before - 1.99
    assert len(hero.special['snowstorm_pulses']) == 3


def test_little_prince_royal_rescue_spawns_guardienne():
    deck = ['Little Prince','Knight','Skeletons','Archers','Musketeer','Hog Rider','Cannon','Fireball']
    env = CRGodEnv(seed=1)
    env.reset(deck_a=deck)
    env.players['blue'].elixir = 10
    env.play('blue','Little Prince',0,-6)
    advance(env, 21)
    env.players['blue'].elixir = 10
    env.activate_ability('blue','Little Prince')
    advance(env, 20)
    assert any(e.alive and e.name == 'Guardienne' and e.owner == 'blue' for e in env.entities.values())


def test_evo_skeleton_barrel_drops_first_barrel_at_75_percent():
    deck = ['Skeleton Barrel Evolution','Knight','Skeletons','Archers','Musketeer','Hog Rider','Cannon','Fireball']
    env = CRGodEnv(seed=1)
    env.reset(deck_a=deck)
    p = env.players['blue']
    # Make evolution ready and force it into hand.
    p.evolution_progress['Skeleton Barrel Evolution'] = 2
    p.hand[0] = 'Skeleton Barrel Evolution'; p.elixir = 10
    env.play('blue','Skeleton Barrel Evolution',0,-5)
    barrel = max(e for e in env.entities.values() if e.source_card == 'Skeleton Barrel Evolution')
    assert barrel.is_evolved
    env._damage(barrel, barrel.max_hp * 0.26)
    assert barrel.special['barrels_left'] == 1
    spawned = [e for e in env.entities.values() if e.source_card == 'Skeleton Barrel Evolution' and e.name == 'Skeletons']
    assert len(spawned) >= 7


def test_air_unit_ignores_cannon_as_target_and_cannon_cannot_target_air():
    blue = ['Skeleton Barrel','Knight','Skeletons','Archers','Musketeer','Hog Rider','Fireball','Arrows']
    red = ['Cannon','Knight','Skeletons','Archers','Musketeer','Hog Rider','Fireball','Arrows']
    env = CRGodEnv(seed=3)
    env.reset(deck_a=blue, deck_b=red)
    env.players['blue'].elixir = env.players['red'].elixir = 10
    env.play('blue','Skeleton Barrel',-3,-5)
    env.play('red','Cannon',-3,4)
    advance(env, 30)
    barrel = next(e for e in env.entities.values() if e.alive and e.source_card == 'Skeleton Barrel')
    target = env.entities.get(barrel.target_id)
    assert target is not None and target.kind in ('building','tower')
    cannon = next(e for e in env.entities.values() if e.alive and e.name == 'Cannon' and e.owner == 'red')
    assert cannon.target_id != barrel.id


def test_evo_musketeer_sniper_uses_ammo_and_ignores_towers():
    deck = ['Musketeer Evolution','Knight','Skeletons','Archers','Hog Rider','Cannon','Fireball','Arrows']
    env = CRGodEnv(seed=4)
    env.reset(deck_a=deck)
    p = env.players['blue']
    p.evolution_progress['Musketeer Evolution'] = 2
    p.hand[0] = 'Musketeer Evolution'; p.elixir = 10
    env.play('blue','Musketeer Evolution',0,-10)
    mus = max(e for e in env.entities.values() if e.source_card == 'Musketeer Evolution')
    mus.deploy_remaining = 0
    # Spawn a non-tower enemy 10 tiles away so sniper logic has a legal target.
    env.players['red'].hand[0] = 'Knight'; env.players['red'].elixir = 10
    env.play('red','Knight',0,2)
    target = max(e for e in env.entities.values() if e.owner == 'red' and e.name == 'Knight')
    target.deploy_remaining = 0
    before = mus.special['sniper_ammo']
    env._try_musketeer_snipe(mus)
    assert mus.special['sniper_ammo'] == before - 1
    assert any(p.tag == 'musketeer_sniper' for p in env.projectiles.values())


def test_evo_ebarbs_second_play_is_evolved_and_can_rage_path():
    deck = ['Elite Barbarians Evolution','Knight','Skeletons','Archers','Musketeer','Hog Rider','Cannon','Fireball']
    env = CRGodEnv(seed=6)
    env.reset(deck_a=deck)
    p = env.players['blue']
    p.elixir = 10
    env.play('blue','Elite Barbarians Evolution',0,-6)
    assert p.evolution_progress['Elite Barbarians Evolution'] == 1
    p.hand[0] = 'Elite Barbarians Evolution'; p.elixir = 10
    env.play('blue','Elite Barbarians Evolution',0,-6)
    evos = [e for e in env.entities.values() if e.owner == 'blue' and e.is_evolved and e.special.get('tag') == 'evo_elite_barbarians']
    assert len(evos) == 2
    # Directly validate the support path applies Rage to friendly units on it.
    ally = evos[0]
    env._apply_rage_path('blue', -1, -6, 1, -6, duration=2.0)
    assert ally.status.get('rage_remaining', 0) > 0


def test_snowstorm_current_baseline_slows_without_freeze():
    deck = ['Hero Ice Golem','Knight','Skeletons','Archers','Musketeer','Hog Rider','Cannon','Fireball']
    env = CRGodEnv(seed=8)
    env.reset(deck_a=deck)
    env.players['blue'].elixir = 10
    env.play('blue','Hero Ice Golem',0,-5)
    hero = max(e for e in env.entities.values() if e.source_card == 'Hero Ice Golem')
    hero.deploy_remaining = 0
    env.players['red'].hand[0] = 'Knight'; env.players['red'].elixir = 10
    env.play('red','Knight',0,2)
    enemy = max(e for e in env.entities.values() if e.owner == 'red' and e.name == 'Knight')
    enemy.deploy_remaining = 0
    enemy.x, enemy.y = 0, -2
    env._snowstorm_pulse(hero)
    assert enemy.status.get('slow_remaining', 0) > 0
    assert 'freeze_remaining' not in enemy.status


def test_little_prince_fire_rate_ramps_and_has_03s_movement_retention():
    deck = ['Little Prince','Knight','Skeletons','Archers','Musketeer','Hog Rider','Cannon','Fireball']
    env = CRGodEnv(seed=9)
    env.reset(deck_a=deck)
    env.players['blue'].elixir = 10
    env.play('blue','Little Prince',0,-6)
    prince = max(e for e in env.entities.values() if e.source_card == 'Little Prince')
    prince.deploy_remaining = 0
    prince.special['lp_attack_count'] = 6
    assert abs(env._effective_hit_speed(prince) - 0.4) < 1e-9
    # August-2026 buff: charge state survives up to 0.3 s of movement.
    enemy_tower = next(e for e in env.entities.values() if e.owner == 'red' and e.is_princess)
    prince.target_id = enemy_tower.id
    env._move_units(0.05)
    assert prince.special['lp_attack_count'] == 6
    for _ in range(6): env._move_units(0.05)
    assert prince.special['lp_attack_count'] == 0
