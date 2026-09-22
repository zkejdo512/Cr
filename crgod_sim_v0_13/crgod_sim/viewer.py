from __future__ import annotations
from html import escape


def render_svg(state: dict, path: str, width: int = 540, height: int = 900) -> str:
    """Render a BoardState to a dependency-free SVG debug view."""
    margin = 30
    arena_w, arena_h = width - 2 * margin, height - 2 * margin

    def xy(x, y):
        sx = margin + (x + 9.0) / 18.0 * arena_w
        sy = margin + (16.0 - y) / 32.0 * arena_h
        return sx, sy

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<rect x="{margin}" y="{margin}" width="{arena_w}" height="{arena_h}" fill="#f7f7f7" stroke="black" stroke-width="2"/>',
    ]
    # River
    _, ry1 = xy(0, 1.25); _, ry2 = xy(0, -1.25)
    lines.append(f'<rect x="{margin}" y="{min(ry1, ry2)}" width="{arena_w}" height="{abs(ry2-ry1)}" fill="#dcefff"/>')
    for bx in (-3.0, 3.0):
        sx, sy = xy(bx, 0)
        lines.append(f'<rect x="{sx-22}" y="{sy-7}" width="44" height="14" fill="#d8c2a2" stroke="#555"/>')

    for e in state['entities']:
        sx, sy = xy(e['x'], e['y'])
        owner = e['owner']
        fill = '#5d8bd9' if owner == 'blue' else '#d95d5d'
        if e.get('transport') == 'air':
            shape = f'<ellipse cx="{sx:.1f}" cy="{sy:.1f}" rx="10" ry="7" fill="{fill}" stroke="black"/>'
        elif e['kind'] == 'tower':
            shape = f'<rect x="{sx-11:.1f}" y="{sy-11:.1f}" width="22" height="22" fill="{fill}" stroke="black"/>'
        elif e['kind'] == 'building':
            shape = f'<polygon points="{sx:.1f},{sy-12:.1f} {sx-12:.1f},{sy+10:.1f} {sx+12:.1f},{sy+10:.1f}" fill="{fill}" stroke="black"/>'
        else:
            shape = f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="9" fill="{fill}" stroke="black"/>'
        lines.append(shape)
        name = escape(e['name'])
        evo = ' EVO' if e.get('is_evolved') else ''
        hp = int(round(100 * e.get('hp_fraction', 0)))
        lines.append(f'<text x="{sx+12:.1f}" y="{sy-2:.1f}" font-size="10">{name}{evo}</text>')
        lines.append(f'<text x="{sx+12:.1f}" y="{sy+10:.1f}" font-size="9">HP {hp}%</text>')

    for p in state['projectiles']:
        sx, sy = xy(p['x'], p['y'])
        lines.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3" fill="black"/>')

    lines.append(f'<text x="{margin}" y="20" font-size="14">CR-God v0.2  t={state["time_s"]:.2f}s  tick={state["tick"]}</text>')
    lines.append('</svg>')
    text = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path
