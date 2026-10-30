#!/usr/bin/env python3
"""Render GitHub's public contribution calendar as an isometric SVG landscape."""
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import sys

USER = 'Xyrcil'
URL = f'https://github.com/users/{USER}/contributions'
OUT = Path(__file__).resolve().parents[1] / 'assets' / 'voxel-contributions.svg'

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'td' and 'data-date' in attrs and 'data-level' in attrs:
            day = date.fromisoformat(attrs['data-date'])
            level = int(attrs['data-level'])
            if level not in range(5) or day in self.days:
                raise ValueError('Invalid or duplicate calendar day')
            self.days[day] = level

def polygon(points, fill):
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polygon points="{coords}" fill="{fill}" stroke="#d5dfd6" stroke-width=".45" stroke-linejoin="round"/>'

def render(days):
    ordered = sorted(days)
    if not 360 <= len(ordered) <= 371 or any(b - a != timedelta(days=1) for a, b in zip(ordered, ordered[1:])):
        raise ValueError('Public calendar is incomplete; keeping the previous SVG')
    start = ordered[0] - timedelta(days=(ordered[0].weekday() + 1) % 7)
    tops = ['#e7eee8', '#c8dfbb', '#8ebf91', '#589a79', '#287963']
    lefts = ['#d3dfd6', '#a8c9a2', '#70a77d', '#3e805f', '#205f50']
    rights = ['#c2d1c8', '#94b996', '#599269', '#306c53', '#194f43']
    heights = [2, 7, 14, 24, 36]
    blocks = []
    for day in ordered:
        offset = (day - start).days
        week, weekday = divmod(offset, 7)
        x = 255 + (week - weekday) * 11
        y = 110 + (week + weekday) * 3.8
        level = days[day]
        h = heights[level]
        top = [(x, y-h), (x+11, y+3.8-h), (x, y+7.6-h), (x-11, y+3.8-h)]
        blocks.append((week + weekday, week, [
            polygon([top[3], top[2], (x,y+7.6), (x-11,y+3.8)], lefts[level]),
            polygon([top[2], top[1], (x+11,y+3.8), (x,y+7.6)], rights[level]),
            polygon(top, tops[level]),
        ]))
    tiles = '\n'.join(piece for _, _, pieces in sorted(blocks) for piece in pieces)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 410" role="img" aria-labelledby="title desc">
<title id="title">Xyrcil's contribution landscape</title>
<desc id="desc">An isometric voxel landscape showing GitHub's public daily contribution levels from {ordered[0]} to {ordered[-1]}. Taller, darker blocks indicate higher activity.</desc>
<rect width="1000" height="410" rx="18" fill="#f5f8f2"/>
<path d="M0 300 Q280 225 520 315 T1000 265 V410 H0Z" fill="#edf4e9"/>
<path d="M0 340 Q320 270 590 362 T1000 300 V410 H0Z" fill="#e5efe5"/>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">
<text x="42" y="53" fill="#487b6a" font-size="11" font-weight="700" letter-spacing="3">XYRCIL / CONTRIBUTION LANDSCAPE</text>
<text x="42" y="88" fill="#254b40" font-size="26" font-weight="700">A little world, built day by day.</text>
<text x="958" y="53" text-anchor="end" fill="#66877a" font-size="12">{ordered[0]} — {ordered[-1]}</text>
</g>
<g>{tiles}</g>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" fill="#638276" font-size="11">
<text x="42" y="385">PUBLIC CONTRIBUTIONS · EACH BLOCK IS ONE DAY</text>
<text x="810" y="385">LESS</text>
<rect x="850" y="376" width="8" height="8" fill="#e7eee8" stroke="#c2d1c8"/>
<rect x="862" y="376" width="8" height="8" fill="#c8dfbb"/>
<rect x="874" y="376" width="8" height="8" fill="#8ebf91"/>
<rect x="886" y="376" width="8" height="8" fill="#589a79"/>
<rect x="898" y="376" width="8" height="8" fill="#287963"/>
<text x="918" y="385">MORE</text>
</g>
</svg>'''

def main():
    request = Request(URL, headers={'User-Agent': 'Xyrcil-profile-calendar/1.0', 'Accept': 'text/html'})
    with urlopen(request, timeout=30) as response:
        page = response.read().decode('utf-8')
    parser = Calendar()
    parser.feed(page)
    svg = render(parser.days)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding='utf-8')
    print(f'Rendered {len(parser.days)} public days to {OUT}')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Calendar update failed: {error}', file=sys.stderr)
        sys.exit(1)
