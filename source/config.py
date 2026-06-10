import datetime
import os

USER_NAME = "DireDoch"
PAT = os.environ["ACCESS_TOKEN"]
HEADERS = {"Authorization": "token " + PAT}
GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

BIRTHDATE = datetime.datetime(2005, 7, 23)

TOP_LANGUAGES_COUNT = 3
REPO_IGNORE_LIST: list[str] = []
