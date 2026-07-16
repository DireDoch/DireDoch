from pathlib import Path

from module.activity import get_recent_activity
from module.age import get_age
from module.commits import get_github_since, get_total_commits
from module.languages import get_top_languages
from module.snake_generator import build_and_save as build_snake
from module.stats import (
    get_contributed_repo_count,
    get_followers,
    get_total_stars,
    get_user_repo_count,
)
from module.svg_updater import update_svg

_ROOT  = Path(__file__).resolve().parent.parent
_SVG   = _ROOT / "resources" / "profile.svg"
_SNAKE = _ROOT / "assets" / "snake.svg"

_STEPS = (
    ("age_data",        "Calculating uptime",        get_age),
    ("commit_data",     "Fetching commits",           get_total_commits),
    ("github_since_data","Fetching account creation", get_github_since),
    ("repo_data",       "Fetching owned repos",       get_user_repo_count),
    ("contrib_data",    "Fetching contributed repos", get_contributed_repo_count),
    ("star_data",       "Fetching stars",             get_total_stars),
    ("follower_data",   "Fetching followers",         get_followers),
    ("top_langs",       "Fetching top languages",     get_top_languages),
    ("recent",          "Fetching recent activity",   get_recent_activity),
)


def build_stats() -> dict:
    stats = {}
    total = len(_STEPS)
    for i, (key, label, fn) in enumerate(_STEPS, 1):
        print(f"[{i}/{total}] {label}...")
        stats[key] = fn()
    return stats


def flatten_stats(stats: dict) -> dict:
    flat = dict(stats)
    langs = flat.pop("top_langs", [])
    flat["lang1_data"] = langs[0] if len(langs) > 0 else "—"
    flat["lang2_data"] = langs[1] if len(langs) > 1 else "—"
    flat["lang3_data"] = langs[2] if len(langs) > 2 else "—"
    acts = flat.pop("recent", [])
    for i in range(1, 4):
        flat[f"act{i}_data"] = acts[i - 1] if len(acts) >= i else "—"
    return flat


def main() -> None:
    print("=== Collecting stats ===")
    stats = build_stats()

    print("\n=== Results ===")
    for k, v in stats.items():
        print(f"  {k:<25} {v}")

    print("\n=== Updating profile SVG ===")
    flat = flatten_stats(stats)
    update_svg(str(_SVG), flat)

    print("\n=== Generating snake SVG ===")
    build_snake(str(_SNAKE))

    print("\nDone.")


if __name__ == "__main__":
    main()
