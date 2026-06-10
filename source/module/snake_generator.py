"""
Custom contribution snake SVG generator.

Fetches the last 52 weeks of contributions (GitHub rolling-year view),
builds a randomised Hamiltonian path via Warnsdorff's heuristic so the
snake moves organically rather than in a mechanical serpentine, and
produces an animated SVG with a per-day commit counter overlay.
"""

import datetime
import random
from pathlib import Path

from config import USER_NAME
from module.graphql import run_query

# ── Layout ────────────────────────────────────────────────────────────────────
CELL   = 11
GAP    = 2
STEP   = CELL + GAP   # 13 px per grid unit
GRID_X = 16
GRID_Y = 58
SVG_W  = 720
SVG_H  = 170

# ── Animation ─────────────────────────────────────────────────────────────────
STEP_DUR  = 0.04   # seconds per snake step
SNAKE_LEN = 6      # visible snake length (head + body cells)

# ── Palette (bistre / ocre) ───────────────────────────────────────────────────
BG          = "#2F1B12"
TITLEBAR_BG = "#1A0D07"
BORDER      = "#3D2010"

CONTRIB_COLORS = {
    0: "#2F1B12",
    1: "#5C3318",
    2: "#8B5020",
    3: "#C47030",
    4: "#D28A44",
}
HEAD_COLOR  = "#F0C080"
BODY_COLOR  = "#E8B86D"
EATEN_COLOR = "#2F1B12"

# ── GraphQL ───────────────────────────────────────────────────────────────────
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


# ── Data fetching ─────────────────────────────────────────────────────────────

def fetch_contributions() -> tuple[list[list[dict]], int, int]:
    """
    Returns (weeks, total_commits, current_year).
    Queries the last 365 days to match GitHub's rolling-year contribution view.
    """
    now     = datetime.datetime.now(datetime.timezone.utc)
    from_dt = (now - datetime.timedelta(days=365)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    data = run_query(
        _CALENDAR_QUERY,
        {"login": USER_NAME, "from": from_dt.isoformat(), "to": now.isoformat()},
        "snake.contributions",
    )
    cal   = data["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [
        [{"date": d["date"], "count": d["contributionCount"]}
         for d in w["contributionDays"]]
        for w in cal["weeks"]
    ]
    return weeks, cal["totalContributions"], now.year


# ── Path finding (Warnsdorff's heuristic) ────────────────────────────────────

def _neighbours(wi: int, di: int, valid: set) -> list[tuple[int, int]]:
    return [(wi + dw, di + dd)
            for dw, dd in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if (wi + dw, di + dd) in valid]


def _degree(pos: tuple, visited: set, valid: set) -> int:
    """Number of unvisited neighbours of pos."""
    return sum(1 for n in _neighbours(*pos, valid) if n not in visited)


def _warnsdorff_path(
    valid_cells: dict,          # {(wi, di): count}
    seed: int | None = None,
) -> list[tuple[int, int, int]]:
    """
    Randomised Warnsdorff's heuristic.
    Always moves to the neighbour with the fewest onward moves;
    ties broken randomly → path looks organic, not serpentine.
    Falls back to serpentine if no complete path is found.
    """
    rng   = random.Random(seed)
    valid = set(valid_cells.keys())

    # Candidate starting corners (cells at grid boundaries tend to work best)
    cols  = sorted({w for w, _ in valid})
    max_w = cols[-1] if cols else 0
    max_d = max(d for _, d in valid)
    corners = [(0, 0), (0, max_d), (max_w, 0), (max_w, max_d)]
    rng.shuffle(corners)

    for start in corners:
        if start not in valid:
            continue

        path:    list[tuple[int, int]] = [start]
        visited: set[tuple[int, int]] = {start}

        while len(path) < len(valid):
            wi, di   = path[-1]
            cands    = [n for n in _neighbours(wi, di, valid) if n not in visited]
            if not cands:
                break  # stuck — try next starting corner

            min_deg  = min(_degree(n, visited, valid) for n in cands)
            best     = [n for n in cands if _degree(n, visited, valid) == min_deg]
            rng.shuffle(best)
            nxt = best[0]
            path.append(nxt)
            visited.add(nxt)

        if len(path) == len(valid):
            return [(wi, di, valid_cells[(wi, di)]) for wi, di in path]

    # ── Fallback: serpentine ──────────────────────────────────────────────────
    result = []
    weeks_grouped: dict[int, list[tuple[int, int]]] = {}
    for wi, di in valid:
        weeks_grouped.setdefault(wi, []).append(di)
    for wi in sorted(weeks_grouped):
        days = sorted(weeks_grouped[wi])
        if wi % 2 == 1:
            days = list(reversed(days))
        for di in days:
            result.append((wi, di, valid_cells[(wi, di)]))
    return result


# ── SVG building ──────────────────────────────────────────────────────────────

def _contrib_color(count: int) -> str:
    if count == 0:  return CONTRIB_COLORS[0]
    if count <= 3:  return CONTRIB_COLORS[1]
    if count <= 6:  return CONTRIB_COLORS[2]
    if count <= 9:  return CONTRIB_COLORS[3]
    return CONTRIB_COLORS[4]


def _cell_animate(i: int, n: int, count: int, total_dur: float) -> str:
    """Single <animate> taking a cell through: initial → head → body → eaten."""
    init    = _contrib_color(count)
    t_head  = i / n
    t_body  = (i + 1) / n
    t_eaten = min((i + SNAKE_LEN) / n, 1.0)

    raw = [(0.0, init), (t_head, HEAD_COLOR), (t_body, BODY_COLOR),
           (t_eaten, EATEN_COLOR), (1.0, EATEN_COLOR)]

    # Deduplicate adjacent identical times
    deduped: list[tuple[float, str]] = []
    for t, v in raw:
        if deduped and abs(t - deduped[-1][0]) < 1e-6:
            deduped[-1] = (t, v)
        else:
            deduped.append((t, v))

    kt = ";".join(f"{t:.5f}" for t, _ in deduped)
    va = ";".join(v           for _, v in deduped)
    return (
        f'<animate attributeName="fill" values="{va}" keyTimes="{kt}" '
        f'calcMode="discrete" dur="{total_dur:.3f}s" repeatCount="indefinite"/>'
    )


def _counter_css_and_els(
    path: list[tuple[int, int, int]],
    n: int,
    total_dur: float,
) -> tuple[str, str]:
    """
    CSS @keyframes + <text> elements for the commit counter.
    One text element per unique cumulative-count value.
    """
    changes: list[tuple[float, int]] = []
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
        ps    = t_start * 100
        pe    = t_end   * 100
        cls   = f"cnt{j}"

        if ps < 0.001:
            kf = (
                f"@keyframes {cls}{{"
                f"0%,{pe - 0.001:.4f}%{{opacity:1}}"
                f"{pe:.4f}%,100%{{opacity:0}}}}"
            )
        else:
            kf = (
                f"@keyframes {cls}{{"
                f"0%,{ps - 0.001:.4f}%{{opacity:0}}"
                f"{ps:.4f}%{{opacity:1}}"
                f"{pe - 0.001:.4f}%{{opacity:1}}"
                f"{pe:.4f}%,100%{{opacity:0}}}}"
            )
        css_rules.append(
            kf + f".{cls}{{animation:{cls} {total_dur:.3f}s steps(1) 0s infinite;}}"
        )
        text_els.append(
            f'<text class="{cls}" x="704" y="22" text-anchor="end" '
            f'font-size="11px" fill="#E8B86D" opacity="0">'
            f'COMMITS: {value}</text>'
        )

    return "\n".join(css_rules), "\n".join(text_els)


def generate_snake_svg(weeks: list[list[dict]], year: int) -> str:
    # Build valid-cell map: {(wi, di): count}
    valid_cells: dict[tuple[int, int], int] = {}
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            valid_cells[(wi, di)] = day["count"]

    # Use a daily seed so the path varies each day but is stable within a day
    seed      = int(datetime.datetime.now().strftime("%Y%m%d"))
    path      = _warnsdorff_path(valid_cells, seed=seed)
    n         = len(path)
    total_dur = n * STEP_DUR

    counter_css, counter_texts = _counter_css_and_els(path, n, total_dur)

    # Cell rects
    cell_rects = []
    for i, (wi, di, count) in enumerate(path):
        x    = GRID_X + wi * STEP
        y    = GRID_Y + di * STEP
        init = _contrib_color(count)
        anim = _cell_animate(i, n, count, total_dur)
        cell_rects.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{init}">{anim}</rect>'
        )

    cells_svg = "\n".join(cell_rects)

    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg"
     font-family="'Courier New',Courier,monospace"
     width="100%" viewBox="0 0 {SVG_W} {SVG_H}" font-size="14px">
<style>
  text,tspan{{white-space:pre;}}
  {counter_css}
</style>

<rect width="{SVG_W}" height="{SVG_H}" fill="{BG}" rx="10"/>

<rect width="{SVG_W}" height="30" fill="{TITLEBAR_BG}" rx="10"/>
<rect y="15" width="{SVG_W}" height="15" fill="{TITLEBAR_BG}"/>
<circle cx="16" cy="15" r="5" fill="#3D1F0F"/>
<circle cx="32" cy="15" r="5" fill="#4A2510"/>
<circle cx="48" cy="15" r="5" fill="#3D1F0F"/>
<line x1="0" y1="30" x2="{SVG_W}" y2="30" stroke="{BORDER}" stroke-width="1"/>

<text x="300" y="21" text-anchor="middle" fill="#7A4520" font-size="12px">CONTRIBUTION.SNAKE · {year}</text>

{counter_texts}

{cells_svg}

<defs>
  <pattern id="sc" width="{SVG_W}" height="4" patternUnits="userSpaceOnUse">
    <rect width="{SVG_W}" height="1" fill="#000" opacity="0.10"/>
  </pattern>
</defs>
<rect width="{SVG_W}" height="{SVG_H}" fill="url(#sc)" rx="10"/>
</svg>"""


def build_and_save(output_path: str) -> None:
    weeks, total, year = fetch_contributions()
    total_cells = sum(len(w) for w in weeks)
    print(f"  Weeks: {len(weeks)}, cells: {total_cells}, commits: {total} ({year})")
    svg = generate_snake_svg(weeks, year)
    Path(output_path).write_text(svg, encoding="utf-8")
    print(f"  Snake SVG written → {output_path}")
