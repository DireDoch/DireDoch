"""
Custom contribution snake SVG generator.

Fetches the current year's contribution calendar, builds a serpentine snake
path through the grid, and produces an animated SVG where:
  - Each grid cell animates through: initial → snake-head → snake-body → eaten
  - A commit counter overlay updates every time the snake eats a non-zero day
"""

import datetime
from pathlib import Path

from config import USER_NAME
from module.graphql import run_query

# ── Layout constants ──────────────────────────────────────────────────────────
CELL      = 11          # px, cell side
GAP       = 2           # px, gap between cells
STEP      = CELL + GAP  # 13 px per grid unit
GRID_X    = 16          # left padding for grid
GRID_Y    = 58          # top of grid (below title bar + counter)
SVG_W     = 720
SVG_H     = 170

# ── Animation constants ───────────────────────────────────────────────────────
STEP_DUR   = 0.04       # seconds per snake step
SNAKE_LEN  = 6          # cells in visible snake body (head + body)

# ── Colour palette (bistre / ocre) ────────────────────────────────────────────
BG           = "#2F1B12"
TITLEBAR_BG  = "#1A0D07"
BORDER       = "#3D2010"

CONTRIB_COLORS = {
    0: "#2F1B12",
    1: "#5C3318",
    2: "#8B5020",
    3: "#C47030",
    4: "#D28A44",
}
SNAKE_HEAD_COLOR = "#F0C080"
SNAKE_BODY_COLOR = "#E8B86D"
EATEN_COLOR      = "#2F1B12"

# ── GraphQL query ─────────────────────────────────────────────────────────────
_CALENDAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def _contrib_color(count: int) -> str:
    if count == 0:
        return CONTRIB_COLORS[0]
    if count <= 3:
        return CONTRIB_COLORS[1]
    if count <= 6:
        return CONTRIB_COLORS[2]
    if count <= 9:
        return CONTRIB_COLORS[3]
    return CONTRIB_COLORS[4]


def fetch_contributions() -> tuple[list[list[dict]], int]:
    """Returns (weeks, total) for the current calendar year."""
    year = datetime.datetime.now().year
    from_dt = f"{year}-01-01T00:00:00Z"
    to_dt   = f"{year}-12-31T23:59:59Z"
    data = run_query(
        _CALENDAR_QUERY,
        {"login": USER_NAME, "from": from_dt, "to": to_dt},
        "snake.contributions",
    )
    cal   = data["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[{"date": d["date"], "count": d["contributionCount"]}
              for d in w["contributionDays"]]
             for w in cal["weeks"]]
    total = cal["totalContributions"]
    return weeks, total


def _build_path(weeks: list[list[dict]]) -> list[tuple[int, int, int]]:
    """Serpentine traversal: column 0 top→bottom, column 1 bottom→top, …"""
    path = []
    for wi, week in enumerate(weeks):
        days_with_idx = list(enumerate(week))
        if wi % 2 == 1:
            days_with_idx = list(reversed(days_with_idx))
        for di, day in days_with_idx:
            path.append((wi, di, day["count"]))
    return path


def _cell_animation(i: int, n: int, count: int) -> str:
    """One <animate> element that takes a cell through its color lifecycle."""
    init  = _contrib_color(count)
    t_head  = i / n
    t_body  = (i + 1) / n
    t_eaten = min((i + SNAKE_LEN) / n, 1.0)

    # Build unique time points and corresponding color values
    raw = [
        (0.0,    init),
        (t_head, SNAKE_HEAD_COLOR),
        (t_body, SNAKE_BODY_COLOR),
        (t_eaten, EATEN_COLOR),
        (1.0,    EATEN_COLOR),
    ]

    # Deduplicate identical adjacent times (keep last value for that time)
    deduped: list[tuple[float, str]] = []
    for t, v in raw:
        if deduped and abs(t - deduped[-1][0]) < 1e-6:
            deduped[-1] = (t, v)
        else:
            deduped.append((t, v))

    kt = ";".join(f"{t:.5f}" for t, _ in deduped)
    va = ";".join(v           for _, v in deduped)
    return (
        f'<animate attributeName="fill" '
        f'values="{va}" keyTimes="{kt}" '
        f'calcMode="discrete" dur="{{DUR}}s" '
        f'repeatCount="indefinite"/>'
    )


def _counter_css_and_elements(
    path: list[tuple[int, int, int]],
    n: int,
    total_dur: float,
) -> tuple[str, str]:
    """
    Build CSS @keyframes + <text> elements for the commit counter overlay.
    A new text element is created only when the cumulative count changes.
    """
    changes: list[tuple[float, int]] = []   # (time_fraction, cumulative_value)
    cumulative = 0

    for i, (_, _, count) in enumerate(path):
        if count > 0:
            cumulative += count
            changes.append((i / n, cumulative))

    if not changes or changes[0][0] > 0.0:
        changes.insert(0, (0.0, 0))

    css_rules: list[str] = []
    text_els:  list[str] = []

    for j, (t_start, value) in enumerate(changes):
        t_end = changes[j + 1][0] if j + 1 < len(changes) else 1.0
        pct_s = t_start * 100
        pct_e = t_end   * 100
        cls   = f"cnt{j}"

        # CSS: visible only during [t_start, t_end)
        if pct_s < 0.001:
            kf = (
                f"@keyframes {cls} {{\n"
                f"  0%,{pct_e - 0.001:.4f}% {{ opacity:1 }}\n"
                f"  {pct_e:.4f}%,100%       {{ opacity:0 }}\n"
                f"}}"
            )
        else:
            kf = (
                f"@keyframes {cls} {{\n"
                f"  0%,{pct_s - 0.001:.4f}%  {{ opacity:0 }}\n"
                f"  {pct_s:.4f}%              {{ opacity:1 }}\n"
                f"  {pct_e - 0.001:.4f}%      {{ opacity:1 }}\n"
                f"  {pct_e:.4f}%,100%         {{ opacity:0 }}\n"
                f"}}"
            )
        css_rules.append(
            kf + f"\n.{cls}{{animation:{cls} {total_dur:.3f}s steps(1) 0s infinite;}}"
        )

        text_els.append(
            f'<text class="{cls}" x="680" y="22" text-anchor="end" '
            f'font-size="11px" fill="#E8B86D" opacity="0">'
            f'COMMITS: {value}</text>'
        )

    return "\n".join(css_rules), "\n".join(text_els)


def generate_snake_svg(weeks: list[list[dict]], year: int) -> str:
    path      = _build_path(weeks)
    n         = len(path)
    total_dur = n * STEP_DUR

    counter_css, counter_texts = _counter_css_and_elements(path, n, total_dur)

    # ── Cell rects ────────────────────────────────────────────────────────────
    cell_rects = []
    for i, (wi, di, count) in enumerate(path):
        x    = GRID_X + wi * STEP
        y    = GRID_Y + di * STEP
        init = _contrib_color(count)
        anim = _cell_animation(i, n, count).replace("{DUR}", f"{total_dur:.3f}")
        cell_rects.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
            f'fill="{init}">{anim}</rect>'
        )

    cells_svg   = "\n".join(cell_rects)
    year_label  = str(year)

    svg = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg"
     font-family="'Courier New',Courier,monospace"
     width="100%" viewBox="0 0 {SVG_W} {SVG_H}" font-size="14px">
<style>
  text, tspan {{ white-space: pre; }}
  {counter_css}
</style>

<!-- Background -->
<rect width="{SVG_W}" height="{SVG_H}" fill="{BG}" rx="10"/>

<!-- Title bar -->
<rect width="{SVG_W}" height="30" fill="{TITLEBAR_BG}" rx="10"/>
<rect y="15" width="{SVG_W}" height="15" fill="{TITLEBAR_BG}"/>
<circle cx="16" cy="15" r="5" fill="#3D1F0F"/>
<circle cx="32" cy="15" r="5" fill="#4A2510"/>
<circle cx="48" cy="15" r="5" fill="#3D1F0F"/>
<line x1="0" y1="30" x2="{SVG_W}" y2="30" stroke="{BORDER}" stroke-width="1"/>

<!-- Title -->
<text x="300" y="21" text-anchor="middle" fill="#7A4520" font-size="12px">CONTRIBUTION.SNAKE · {year_label}</text>

<!-- Live commit counter -->
{counter_texts}

<!-- Contribution grid -->
{cells_svg}

<!-- Scanlines -->
<rect width="{SVG_W}" height="{SVG_H}" fill="url(#scanlines)" rx="10"/>
<defs>
  <pattern id="scanlines" width="{SVG_W}" height="4" patternUnits="userSpaceOnUse">
    <rect width="{SVG_W}" height="1" y="0" fill="#000000" opacity="0.10"/>
  </pattern>
</defs>
</svg>"""
    return svg


def build_and_save(output_path: str) -> None:
    weeks, total = fetch_contributions()
    year = datetime.datetime.now().year
    print(f"  Contributions fetched: {total} total for {year}")
    svg = generate_snake_svg(weeks, year)
    Path(output_path).write_text(svg, encoding="utf-8")
    print(f"  Snake SVG written → {output_path}")
