# CR-God v0.2 action schema

Normal deployment:

```python
{"type": "play", "card": "Hog Rider", "x": -3.0, "y": -5.0}
```

`type` may be omitted for normal deployments.

Hero / Champion ability:

```python
{"type": "ability", "card": "Hero Ice Golem"}
{"type": "ability", "card": "Little Prince"}
```

`step(action_a, action_b, ticks=N)` accepts one action for each side and then advances the fixed-tick world.

## BoardState additions in v0.2

Each player now exposes evolution progress/readiness. Entities expose transport (`ground`/`air`), whether the deployment is evolved, temporary status effects, and special-mechanic state such as sniper ammo or ability cooldown.
