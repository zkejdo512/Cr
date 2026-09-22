from crgod_sim import CRGodEnv

blue = ['Hog Rider','Knight','Skeletons','Archers','Musketeer','Cannon','Fireball','Arrows']
red = ['Cannon','Knight','Skeletons','Archers','Musketeer','Hog Rider','Fireball','Arrows']
env = CRGodEnv(seed=42)
obs = env.reset(deck_a=blue, deck_b=red)
print('Blue starting hand:', obs['players']['blue']['hand'])

env.step({'card':'Hog Rider','x':-2.8,'y':-5.0}, {'card':'Cannon','x':-2.7,'y':4.2}, ticks=1)

for _ in range(1200):
    obs, rewards, done, info = env.step(ticks=1)
    if done:
        break

print('time:', obs['time_s'], 'winner:', obs['winner'])
print('rewards(last step):', rewards)
print('alive entities:', len(obs['entities']))
for e in obs['entities']:
    if e['kind'] == 'tower':
        print(e['owner'], e['name'], (e['x'], e['y']), 'HP=', e['hp'])
