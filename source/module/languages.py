from config import REPO_IGNORE_LIST, TOP_LANGUAGES_COUNT
from module.request_manager import get_repo_languages, get_repos


def get_top_languages() -> list[str]:
    lang_bytes: dict[str, int] = {}
    for repo in get_repos():
        if repo.get("fork") or repo["name"] in REPO_IGNORE_LIST:
            continue
        for lang, count in get_repo_languages(repo["name"]).items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + count
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)
    return [name for name, _ in sorted_langs[:TOP_LANGUAGES_COUNT]]
