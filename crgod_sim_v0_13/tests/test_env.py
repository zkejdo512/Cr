from crgod_sim import CRGodEnv


def test_reset_and_cycle():
    env = CRGodEnv(seed=1)
    s = env.reset()
    assert s['players']['blue']['hand'] == ['Knight','Skeletons','Archers','Musketeer']
    env.play('blue','Knight',0,-6)
    s = env.board_state()
    assert 'Hog Rider' in s['players']['blue']['hand']
    assert s['players']['blue']['queue'][-1] == 'Knight'


def test_spell_damage():
    env = CRGodEnv(seed=1)
    deck = ['Fireball','Knight','Skeletons','Archers','Musketeer','Hog Rider','Cannon','Arrows']
    env.reset(deck_a=deck)
    hp0 = [e['hp'] for e in env.board_state()['entities'] if e['owner']=='red' and e['is_princess'] and e['x'] < 0][0]
    env.play('blue','Fireball',-3.25,12.0)
    for _ in range(60): env.step()
    hp1 = [e['hp'] for e in env.board_state()['entities'] if e['owner']=='red' and e['is_princess'] and e['x'] < 0][0]
    assert hp1 < hp0


def test_deterministic_trajectory():
    def run():
        env = CRGodEnv(seed=99)
        env.reset()
        env.step({'card':'Knight','x':-2,'y':-6}, {'card':'Knight','x':2,'y':6}, ticks=500)
        st = env.board_state()
        return [(e['name'], e['owner'], e['x'], e['y'], e['hp']) for e in st['entities']]
    assert run() == run()


def test_hog_can_be_pulled_by_cannon():
    env = CRGodEnv(seed=3)
    blue = ['Hog Rider','Knight','Skeletons','Archers','Musketeer','Cannon','Fireball','Arrows']
    red = ['Cannon','Knight','Skeletons','Archers','Musketeer','Hog Rider','Fireball','Arrows']
    env.reset(deck_a=blue, deck_b=red)
    env.play('blue','Hog Rider',-3.0,-5.0)
    env.play('red','Cannon',-2.7,4.2)
    for _ in range(250): env.step()
    hogs = [e for e in env.board_state()['entities'] if e['name']=='Hog Rider' and e['owner']=='blue']
    # Hog may have died; if alive, target should be building/tower only.
    if hogs:
        hog = hogs[0]
        tid = hog['target_id']
        if tid is not None:
            target = next(e for e in env.board_state()['entities'] if e['id']==tid)
            assert target['kind'] in ('building','tower')
