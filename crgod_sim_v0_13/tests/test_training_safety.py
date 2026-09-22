import math
from crgod_sim import CRGodEnv, GridActionCodec, public_observation, ObservationConfig, DECK_A_26_HOG


def test_public_observation_masks_hidden_enemy_information():
    env = CRGodEnv(seed=10)
    env.reset(deck_a=DECK_A_26_HOG, deck_b=DECK_A_26_HOG)
    obs = public_observation(env, 'blue')
    assert obs['players']['red']['elixir'] is None
    assert obs['players']['red']['queue'] is None
    assert obs['players']['red']['deck'] is None
    assert obs['players']['red']['hand'] == [None]*4
    assert obs['players']['blue']['elixir'] == 5.0


def test_public_observation_noise_is_deterministic_and_does_not_change_truth():
    env = CRGodEnv(seed=11)
    env.reset(deck_a=DECK_A_26_HOG, deck_b=DECK_A_26_HOG)
    env.players['blue'].elixir = 10
    env.play('blue', 'Hog Rider', -3, -5)
    for _ in range(30): env.step()
    truth1 = env.board_state()
    cfg = ObservationConfig(position_std=0.2, hp_fraction_std=0.02, miss_probability=0.0)
    a = public_observation(env, 'red', cfg)
    b = public_observation(env, 'red', cfg)
    truth2 = env.board_state()
    assert a == b
    assert truth1 == truth2


def test_discrete_action_mask_prevents_illegal_actions():
    env = CRGodEnv(seed=1)
    env.reset(deck_a=DECK_A_26_HOG, deck_b=DECK_A_26_HOG)
    codec = GridActionCodec(spacing=2.0)
    mask = codec.legal_mask(env, 'blue')
    assert mask[0]
    # Deliberately pass out-of-range id; it becomes a penalized no-op, never an env exception.
    obs, rew, done, info = codec.step_discrete(env, codec.n + 99, 0, ticks=1)
    assert info['illegal_discrete_actions']['blue'] is True
    assert not info.get('action_errors')
    assert rew['blue'] < 0


def test_masked_legal_sample_has_no_action_error():
    env = CRGodEnv(seed=2)
    env.reset(deck_a=DECK_A_26_HOG, deck_b=DECK_A_26_HOG)
    codec = GridActionCodec(spacing=2.0)
    legal = [i for i,v in enumerate(codec.legal_mask(env,'blue')) if v]
    aid = legal[-1]
    obs, rew, done, info = codec.step_discrete(env, aid, 0, ticks=1)
    assert info['illegal_discrete_actions']['blue'] is False
    assert not info.get('action_errors')


def test_king_tower_starts_dormant_then_activates_on_damage():
    env = CRGodEnv(seed=3)
    deck = ['Fireball','Knight','Skeletons','Archers','Musketeer','Hog Rider','Cannon','Arrows']
    env.reset(deck_a=deck, deck_b=deck)
    king = next(e for e in env.entities.values() if e.owner=='red' and e.is_king)
    assert king.special['king_active'] is False
    env.players['blue'].elixir = 10
    env.play('blue','Fireball',0,14.1)
    # King Tower is combat-active as soon as damage lands; no fabricated 4 s delay.
    for _ in range(60): env.step()
    assert king.hp < king.max_hp
    assert king.special['king_active'] is True
    assert king.special['king_activation_remaining'] is None


def test_princess_tower_death_opens_same_lane_pocket_only():
    env = CRGodEnv(seed=4)
    env.reset(deck_a=DECK_A_26_HOG, deck_b=DECK_A_26_HOG)
    # Before tower loss, blue cannot deploy a troop across river.
    assert not env.can_deploy('blue','Hog Rider',-3,5)
    left_red = next(e for e in env.entities.values() if e.owner=='red' and e.is_princess and e.x < 0)
    env._damage(left_red, left_red.hp + 1)
    assert env.can_deploy('blue','Hog Rider',-3,5)
    assert not env.can_deploy('blue','Hog Rider',3,5)


def test_match_timing_elixir_phases_and_overtime():
    env = CRGodEnv(seed=5)
    env.reset(deck_a=DECK_A_26_HOG, deck_b=DECK_A_26_HOG)
    env.time_s = 119.9
    env._tick_once()
    assert env.time_s < 120.0 or env.board_state()['phase'] in ('normal','double')
    env.time_s = 180.0
    env._overtime_started = False
    env._check_end()
    assert env._overtime_started and not env.done
    env.time_s = 240.0
    assert env.board_state()['phase'] == 'triple'


def test_fireball_is_not_instant_and_arrows_are_three_volleys():
    env = CRGodEnv(seed=6)
    deck = ['Fireball','Arrows','Knight','Skeletons','Archers','Musketeer','Hog Rider','Cannon']
    env.reset(deck_a=deck, deck_b=deck)
    red_left = next(e for e in env.entities.values() if e.owner=='red' and e.is_princess and e.x<0)
    hp = red_left.hp
    env.players['blue'].elixir=10
    env.play('blue','Fireball',red_left.x,red_left.y)
    assert red_left.hp == hp
    assert any(ev['kind']=='fireball' for ev in env.spell_events)
    for _ in range(60): env.step()
    assert red_left.hp < hp
    env.players['blue'].hand[0]='Arrows'; env.players['blue'].elixir=10
    env.play('blue','Arrows',red_left.x,red_left.y)
    assert sum(ev['kind']=='area_delayed' for ev in env.spell_events) >= 3
