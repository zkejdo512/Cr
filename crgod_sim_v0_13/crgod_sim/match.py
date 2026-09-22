from __future__ import annotations
from .env import CRGodEnv
from .observation import public_observation, ObservationConfig


def run_match(deck_a, deck_b, agent_a, agent_b, seed: int = 0,
              decision_interval_ticks: int = 4, max_ticks: int = 6000,
              masked_observations: bool = True,
              observation_config: ObservationConfig | None = None):
    """Run two policy objects against each other and return final true state + trace.

    By default each agent receives only its own public observation, not the opponent's
    exact hand/queue/deck/elixir. Agents expose `act(state, side) -> action|None`.
    """
    env = CRGodEnv(seed=seed)
    env.reset(deck_a=deck_a, deck_b=deck_b, seed=seed)
    trace = []
    for _ in range(0, max_ticks, decision_interval_ticks):
        if masked_observations:
            obs_a = public_observation(env, 'blue', observation_config)
            obs_b = public_observation(env, 'red', observation_config)
        else:
            obs_a = obs_b = env.board_state()
        a = agent_a.act(obs_a, 'blue')
        b = agent_b.act(obs_b, 'red')
        state, reward, done, info = env.step(a, b, ticks=decision_interval_ticks)
        if a or b or info.get('action_errors'):
            trace.append({'tick': state['tick'], 'blue': a, 'red': b,
                          'reward': reward, 'errors': info.get('action_errors', {})})
        if done:
            break
    return env.board_state(), trace
