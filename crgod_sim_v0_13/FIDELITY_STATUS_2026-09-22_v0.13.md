# CR-God Simulator v0.13 fidelity hardening

Verified/fixed in this pass:
- Rune Giant level-16 HP 4253, base damage 192, enchant bonus 351 every third attack.
- Little Prince ramp thresholds corrected to shots 1-2 / 3-4 / 5+, with current 1.2 / 0.8 / 0.4 timing baseline.
- August 2026 champion rule: abilities are single-use per deployed unit (Boss Bandit exception is not in these decks).
- Little Prince 0.3 s movement conservation now measures consecutive movement instead of accumulating separated movement fragments.
- Exact-overlap collision deadlock fixed and collision correction clamped to arena bounds.
- Executioner returning axe homes back toward the moving Executioner rather than following a frozen reverse ray.
- Regression tests updated to reject the previously incorrect LP 3/6-shot thresholds.

Still not claimed as server-identical: Supercell does not publish full navmesh, push/mass constants, sub-tick animation/event ordering, or all hidden projectile/collision constants. Those require real-game trajectory calibration.
