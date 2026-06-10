import datetime
from datetime import timezone

from config import USER_NAME
from module.graphql import run_query

_ACCOUNT_QUERY = """
query($login: String!) {
    user(login: $login) {
        createdAt
    }
}
"""

_CONTRIB_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
    user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
            contributionCalendar {
                totalContributions
            }
        }
    }
}
"""


def _account_created_at() -> datetime.datetime:
    data = run_query(_ACCOUNT_QUERY, {"login": USER_NAME}, "commits.account_created_at")
    return datetime.datetime.fromisoformat(data["user"]["createdAt"].replace("Z", "+00:00"))


def _contributions_between(start: datetime.datetime, end: datetime.datetime) -> int:
    data = run_query(
        _CONTRIB_QUERY,
        {"login": USER_NAME, "from": start.isoformat(), "to": end.isoformat()},
        "commits.contributions",
    )
    return int(data["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"])


def get_total_commits() -> int:
    created_at = _account_created_at()
    now = datetime.datetime.now(timezone.utc)
    total = 0
    for year in range(created_at.year, now.year + 1):
        start = max(datetime.datetime(year, 1, 1, tzinfo=timezone.utc), created_at)
        end = min(datetime.datetime(year + 1, 1, 1, tzinfo=timezone.utc), now)
        if start < end:
            total += _contributions_between(start, end)
    return total


def get_github_since() -> str:
    created_at = _account_created_at()
    return created_at.strftime("%Y-%m-%d")
