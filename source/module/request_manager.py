import requests

from config import HEADERS, USER_NAME

_REST = "https://api.github.com"


def _get(path: str) -> dict | list:
    url = f"{_REST}{path}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"GET {path} failed: {response.status_code}")
    return response.json()


def get_user() -> dict:
    return _get(f"/users/{USER_NAME}")


def get_repos() -> list[dict]:
    repos = []
    page = 1
    while True:
        batch = _get(f"/users/{USER_NAME}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def get_repo_languages(repo_name: str) -> dict:
    return _get(f"/repos/{USER_NAME}/{repo_name}/languages")


def get_events() -> list[dict]:
    return _get(f"/users/{USER_NAME}/events/public?per_page=30")
