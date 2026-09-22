"""CPU-only convergence gate using the actual CR-God simulator.

Task: observe whether an enemy Hog is in the left or right lane, then choose one of
2 Cannon placements. Correct-lane Cannon prevents Princess Tower damage in this
controlled scenario; wrong-lane Cannon allows damage. A tiny learned policy should
reach near-perfect accuracy quickly. This tests reward -> gradient -> action -> sim.
"""
from __future__ import annotations
import argparse, random
import torch
from torch import nn
from torch.distributions import Categorical
from crgod_sim import CRGodEnv, public_observation

DECK=['Hog Rider','Cannon','Knight','Skeletons','Archers','Musketeer','Fireball','Arrows']


def episode(policy, lane: int, sample: bool = True):
    env=CRGodEnv(seed=lane+17)
    env.reset(deck_a=DECK, deck_b=DECK)
    env.players['blue'].elixir=10; env.players['red'].elixir=10
    hx=-3.0 if lane==0 else 3.0
    env.play('blue','Hog Rider',hx,-2.0)
    obs=public_observation(env,'red')
    hog=next(e for e in obs['entities'] if e['name']=='Hog Rider' and e['owner']=='blue')
    x=torch.tensor([[hog['x']/3.0]], dtype=torch.float32)
    logits=policy(x).squeeze(0)
    dist=Categorical(logits=logits)
    action=dist.sample() if sample else torch.argmax(logits)
    cx=-5.0 if int(action)==0 else 5.0
    env.play('red','Cannon',cx,6.0)
    hp0=sum(e.hp for e in env.entities.values() if e.owner=='red' and e.is_princess)
    for _ in range(200):
        env.step()
        if env.done: break
    hp1=sum(e.hp for e in env.entities.values() if e.owner=='red' and e.is_princess and e.alive)
    damage=hp0-hp1
    reward=1.0 if damage < 1e-6 else 0.0
    return reward, dist.log_prob(action), int(action)


def evaluate(policy, n=4):
    ok=0; rewards=[]
    for i in range(n):
        lane=i%2
        r,_,a=episode(policy,lane,sample=False)
        rewards.append(r); ok += int(a==lane)
    return sum(rewards)/n, ok/n


def train(episodes=120, seed=123):
    random.seed(seed); torch.manual_seed(seed)
    policy=nn.Linear(1,2)
    # Deliberately start with equal logits = 50% accuracy.
    with torch.no_grad(): policy.weight.zero_(); policy.bias.zero_()
    opt=torch.optim.Adam(policy.parameters(),lr=0.08)
    initial=evaluate(policy,4)
    history=[]
    for ep in range(1,episodes+1):
        lane=random.randint(0,1)
        reward,logp,_=episode(policy,lane,sample=True)
        # Simple REINFORCE with fixed baseline for this binary sanity task.
        loss=-(reward-0.5)*logp
        opt.zero_grad(); loss.backward(); opt.step()
        if ep in (20,40,60,80,100,episodes):
            history.append((ep,*evaluate(policy,4)))
    final=evaluate(policy,4)
    return initial, history, final

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--episodes',type=int,default=60); ap.add_argument('--seed',type=int,default=123)
    args=ap.parse_args()
    initial,history,final=train(args.episodes,args.seed)
    print(f'initial mean_reward={initial[0]:.3f} success={initial[1]:.3f}')
    for ep,r,s in history: print(f'episode={ep:4d} mean_reward={r:.3f} success={s:.3f}')
    print(f'final mean_reward={final[0]:.3f} success={final[1]:.3f}')
    if final[1] < 0.95:
        raise SystemExit('FAIL: sanity policy did not converge')
    print('PASS: reward -> gradient -> policy -> simulator convergence gate')
