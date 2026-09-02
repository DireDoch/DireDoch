import datetime
import os

USER_NAME = "DireDoch"
PAT = os.environ.get("ACCESS_TOKEN", "").strip()
if not PAT:
    raise SystemExit("ACCESS_TOKEN is empty or unset (Actions: secrets.ACCESS_TOKEN).")
HEADERS = {"Authorization": "token " + PAT}

# A classic PAT defaults to a 30-day life: when it dies every call returns 401 Bad
# credentials. request_manager.check_token() warns before that happens.
TOKEN_HELP = (
    "ACCESS_TOKEN was rejected (401 Bad credentials) — the token is expired or revoked.\n"
    "Fix: generate a new PAT (scopes: repo, read:user) then update the secret at\n"
    f"https://github.com/{USER_NAME}/{USER_NAME}/settings/secrets/actions"
)
GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

BIRTHDATE = datetime.datetime(2005, 7, 23)

TOP_LANGUAGES_COUNT = 3
REPO_IGNORE_LIST: list[str] = []
