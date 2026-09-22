import pytest
from crgod_sim.env import CRGodEnv
from crgod_sim.cards import CARD_SPECS, DECK_B_VIDEO_20260919


def test_rune_giant_level16_public_stats():
    s=CARD_SPECS['Rune Giant']
    assert s.hp == 4253
    assert s.damage == 192


def test_little_prince_stage_thresholds():
    env=CRGodEnv(); env.reset(DECK_B_VIDEO_20260919, DECK_B_VIDEO_20260919)
    s=CARD_SPECS['Little Prince']
    e=env._spawn_from_spec('blue', s, 0,-5,'troop', source_card='Little Prince')
    e.deploy_remaining=0
    for count, expected in [(0,1.2),(1,1.2),(2,0.8),(3,0.8),(4,0.4),(9,0.4)]:
        e.special['lp_attack_count']=count
        assert env._effective_hit_speed(e) == pytest.approx(expected)


def test_champion_ability_single_use_current_rules():
    env=CRGodEnv(); env.reset(DECK_B_VIDEO_20260919, DECK_B_VIDEO_20260919)
    s=CARD_SPECS['Little Prince']
    e=env._spawn_from_spec('blue', s, 0,-5,'troop', source_card='Little Prince')
    e.deploy_remaining=0
    env.players['blue'].elixir=10
    env.activate_ability('blue','Little Prince')
    with pytest.raises(ValueError, match='already used'):
        env.activate_ability('blue','Little Prince')


def test_exact_overlap_collision_separates():
    env=CRGodEnv(); env.reset()
    s=CARD_SPECS['Knight']
    a=env._spawn_from_spec('blue',s,0,-5,'troop'); b=env._spawn_from_spec('blue',s,0,-5,'troop')
    a.deploy_remaining=b.deploy_remaining=0
    env._resolve_collisions()
    assert env._dist(a,b) > 0
