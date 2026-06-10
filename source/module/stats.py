from config import USER_NAME
from module.graphql import run_query
from module.request_manager import get_repos, get_user

_CONTRIB_REPO_QUERY = """
query($login: String!) {
    user(login: $login) {
        repositoriesContributedTo(
            first: 1
            contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]
        ) {
            totalCount
        }
    }
}
"""


def get_user_repo_count() -> int:
    return len(get_repos())


def get_contributed_repo_count() -> int:
    data = run_query(_CONTRIB_REPO_QUERY, {"login": USER_NAME}, "stats.contributed_repos")
    return int(data["user"]["repositoriesContributedTo"]["totalCount"])


def get_total_stars() -> int:
    return sum(r.get("stargazers_count", 0) for r in get_repos())


def get_followers() -> int:
    return get_user().get("followers", 0)
