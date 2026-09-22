from crgod_sim.env import CRGodEnv
from crgod_sim.cards import CARD_SPECS, DECK_B_VIDEO_20260919

def env():
    e=CRGodEnv(seed=11); e.reset(DECK_B_VIDEO_20260919, DECK_B_VIDEO_20260919); return e

def test_september_evo_ebarbs_rage_duration_and_range():
    e=env(); s=CARD_SPECS['Elite Barbarians Evolution']; a=e._spawn_from_spec('blue',s,0,-4,'troop',source_card=s.name,is_evolved=True,special_override='evo_elite_barbarians'); a.deploy_remaining=0
    t=e._spawn_from_spec('red',CARD_SPECS['Elite Barbarians'],0,-0.5,'troop',source_card='Elite Barbarians'); t.deploy_remaining=0
    e._try_ebarbs_spear(a)
    assert a.status.get('rage_remaining',0) == 2.0

def test_evo_skeleton_barrel_lvl16_death_damage():
    e=env(); s=CARD_SPECS['Skeleton Barrel Evolution']; b=e._spawn_from_spec('blue',s,0,-2,'troop',source_card=s.name,is_evolved=True,special_override='evo_skeleton_barrel'); assert b.special['barrel_death_damage']==306.0

def test_royal_rescue_does_not_hit_buildings():
    e=env(); p=e._spawn_from_spec('blue',CARD_SPECS['Little Prince'],0,-3,'troop',source_card='Little Prince'); p.deploy_remaining=0
    tower=next(x for x in e.entities.values() if x.owner=='red' and x.is_princess); tower.x=0; tower.y=-1; hp=tower.hp
    e._royal_rescue(p); assert tower.hp==hp

def test_lightning_stuns_and_uses_explicit_crown_damage():
    e=env(); tower=next(x for x in e.entities.values() if x.owner=='red' and x.is_princess); hp=tower.hp
    s=CARD_SPECS['Lightning']; e._cast_spell('blue',s,tower.x,tower.y)
    for _ in range(8): e._update_spell_events(0.05)
    assert tower.hp == hp - s.crown_tower_damage
    assert tower.status.get('stun_remaining',0)>0

def test_rune_giant_enchants_two_and_expires_after_death():
    e=env(); r=e._spawn_from_spec('blue',CARD_SPECS['Rune Giant'],0,-5,'troop',source_card='Rune Giant'); r.deploy_remaining=0
    allies=[]
    for x in (-1,1,2):
        a=e._spawn_from_spec('blue',CARD_SPECS['Elite Barbarians'],x,-4,'troop',source_card='Elite Barbarians'); a.deploy_remaining=0; allies.append(a)
    e._update_rune_enchantments(.05)
    assert sum('rune_source_id' in a.special for a in allies)==2
    e._kill_entity(r,trigger_death=False)
    for _ in range(101): e._update_rune_enchantments(.05)
    assert sum('rune_source_id' in a.special for a in allies)==0

def test_executioner_axe_has_out_and_return_passes():
    e=env(); ex=e._spawn_from_spec('blue',CARD_SPECS['Executioner'],0,-4,'troop',source_card='Executioner'); ex.deploy_remaining=0
    t=e._spawn_from_spec('red',CARD_SPECS['Elite Barbarians'],0,0,'troop',source_card='Elite Barbarians'); t.deploy_remaining=0; hp=t.hp
    e._launch_executioner_axe(ex,t,ex.damage)
    for _ in range(60): e._move_projectiles(.05)
    assert t.hp <= hp - 2*ex.damage
