from pathlib import Path

from module.age import get_age
from module.commits import get_github_since, get_total_commits
from module.languages import get_top_languages
from module.stats import (
    get_contributed_repo_count,
    get_followers,
    get_total_stars,
    get_user_repo_count,
)
from module.svg_updater import update_svg

_SVG = Path(__file__).resolve().parent.parent / "resources" / "profile.svg"

_STEPS = (
    ("age_data",        "Calculating uptime",        get_age),
    ("commit_data",     "Fetching commits",           get_total_commits),
    ("github_since_data","Fetching account creation", get_github_since),
    ("repo_data",       "Fetching owned repos",       get_user_repo_count),
    ("contrib_data",    "Fetching contributed repos", get_contributed_repo_count),
    ("star_data",       "Fetching stars",             get_total_stars),
    ("follower_data",   "Fetching followers",         get_followers),
    ("top_langs",       "Fetching top languages",     get_top_languages),
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
    return flat


def main() -> None:
    print("=== Collecting stats ===")
    stats = build_stats()

    print("\n=== Results ===")
    for k, v in stats.items():
        print(f"  {k:<25} {v}")

    print("\n=== Updating SVG ===")
    flat = flatten_stats(stats)
    update_svg(str(_SVG), flat)
    print("Done.")


if __name__ == "__main__":
    main()
