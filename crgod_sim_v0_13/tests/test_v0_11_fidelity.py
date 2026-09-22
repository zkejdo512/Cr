from crgod_sim.env import CRGodEnv
from crgod_sim.cards import CARD_SPECS, DECK_B_VIDEO_20260919


def test_level16_towers_and_little_prince():
    env=CRGodEnv(seed=1); env.reset(DECK_B_VIDEO_20260919, DECK_B_VIDEO_20260919)
    pt=next(e for e in env.entities.values() if e.owner=='blue' and e.is_princess)
    kt=next(e for e in env.entities.values() if e.owner=='blue' and e.is_king)
    assert (pt.max_hp, pt.damage)==(4858,173)
    assert (kt.max_hp, kt.damage)==(7704,173)
    assert CARD_SPECS['Little Prince'].damage==167


def test_little_prince_exact_ramp_stages():
    env=CRGodEnv(seed=2); env.reset(DECK_B_VIDEO_20260919, DECK_B_VIDEO_20260919)
    env.players['blue'].elixir=10
    # cycle LP into hand if needed by direct spawn semantics for unit test
    s=CARD_SPECS['Little Prince']; p=env._spawn_from_spec('blue',s,0,-6,'troop',source_card='Little Prince')
    p.deploy_remaining=0
    expected={0:1.2,1:1.2,2:0.8,3:0.8,4:0.4,5:0.4,6:0.4,8:0.4}
    for hits,hs in expected.items():
        p.special['lp_attack_count']=hits
        assert abs(env._effective_hit_speed(p)-hs)<1e-9


def test_royal_rescue_level16_guardienne_and_push_damage():
    env=CRGodEnv(seed=3); env.reset(DECK_B_VIDEO_20260919, DECK_B_VIDEO_20260919)
    lp=CARD_SPECS['Little Prince']; prince=env._spawn_from_spec('blue',lp,0,-3,'troop',source_card='Little Prince')
    prince.deploy_remaining=0
    enemy=CARD_SPECS['Elite Barbarians']; target=env._spawn_from_spec('red',enemy,0,-1,'troop',source_card='Elite Barbarians')
    target.deploy_remaining=0; hp0=target.hp
    env._royal_rescue(prince)
    assert target.hp==hp0-515
    g=max(e for e in env.entities.values() if e.name=='Guardienne')
    assert (g.max_hp,g.damage,g.hit_speed,g.first_hit)==(2556,374,1.2,0.5)
