import datetime
import os

import requests
from dateutil import parser

from config import HEADERS, TOKEN_HELP, USER_NAME

_REST = "https://api.github.com"
_EXPIRY_WARN_DAYS = 7


def _get(path: str) -> dict | list:
    url = f"{_REST}{path}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 401:
        raise SystemExit(TOKEN_HELP)
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


def _expiry_warning(header: str | None, now: datetime.datetime) -> str | None:
    """Message when the PAT expires within _EXPIRY_WARN_DAYS, else None."""
    if not header:  # fine-grained tokens without expiry, or GITHUB_TOKEN
        return None
    expires = parser.parse(header)  # "2026-08-19 21:39:33 UTC" / "... -0800"
    days = (expires - now).days
    if days > _EXPIRY_WARN_DAYS:
        return None
    return f"ACCESS_TOKEN expires in {days} day(s) ({header}) — rotate the secret now."


def check_token() -> None:
    """Fail fast on a dead token, warn before it dies. Called first by main.py and by CI."""
    response = requests.get(f"{_REST}/user", headers=HEADERS)
    if response.status_code == 401:
        raise SystemExit(TOKEN_HELP)
    if response.status_code != 200:
        raise Exception(f"token check failed: {response.status_code} {response.text}")
    warning = _expiry_warning(
        response.headers.get("github-authentication-token-expiration"),
        datetime.datetime.now(datetime.timezone.utc),
    )
    if warning:
        print(f"::warning::{warning}" if os.environ.get("GITHUB_ACTIONS") else warning)
    print(f"token ok for {response.json()['login']}")
