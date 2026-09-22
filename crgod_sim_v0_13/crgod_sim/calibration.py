from __future__ import annotations
import math
from collections import defaultdict


def snapshot(env) -> list[dict]:
    """Compact simulator snapshot for comparison with annotated real/native-engine tracks."""
    rows=[]
    for e in env.board_state()['entities']:
        rows.append({
            'time_s': env.time_s, 'owner': e['owner'], 'name': e['name'],
            'x': e['x'], 'y': e['y'], 'hp_fraction': e['hp_fraction'],
            'kind': e['kind'],
        })
    return rows


def compare_tracks(reference: list[dict], simulated: list[dict], time_tolerance: float = 0.075) -> dict:
    """Nearest-neighbour trajectory comparison by time/owner/name.

    Reference rows can come from manually checked video, perception, or a native-engine oracle.
    The function intentionally does not assume simulator entity IDs match real-game IDs.
    """
    sim_by_key=defaultdict(list)
    for r in simulated:
        sim_by_key[(r['owner'],r['name'])].append(r)
    for vals in sim_by_key.values(): vals.sort(key=lambda r:r['time_s'])
    pos_sq=[]; hp_abs=[]; missing=0; matched=0
    for r in reference:
        cand=sim_by_key.get((r['owner'],r['name']),[])
        near=[s for s in cand if abs(float(s['time_s'])-float(r['time_s'])) <= time_tolerance]
        if not near:
            missing += 1; continue
        # For duplicate troops, choose the spatially nearest candidate at the closest time.
        best=min(near,key=lambda s:(abs(float(s['time_s'])-float(r['time_s'])),
                                    (float(s['x'])-float(r['x']))**2+(float(s['y'])-float(r['y']))**2))
        pos_sq.append((float(best['x'])-float(r['x']))**2+(float(best['y'])-float(r['y']))**2)
        if 'hp_fraction' in r and r['hp_fraction'] is not None:
            hp_abs.append(abs(float(best['hp_fraction'])-float(r['hp_fraction'])))
        matched += 1
    return {
        'reference_rows': len(reference), 'matched_rows': matched, 'missing_rows': missing,
        'position_rmse_tiles': math.sqrt(sum(pos_sq)/len(pos_sq)) if pos_sq else None,
        'mean_abs_hp_fraction_error': sum(hp_abs)/len(hp_abs) if hp_abs else None,
    }
