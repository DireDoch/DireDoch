import requests

from config import GRAPHQL_ENDPOINT, HEADERS


def run_query(query: str, variables: dict, label: str) -> dict:
    response = requests.post(
        GRAPHQL_ENDPOINT,
        json={"query": query, "variables": variables},
        headers=HEADERS,
    )
    if response.status_code != 200:
        raise Exception(f"{label} failed: {response.status_code} {response.text}")
    payload = response.json()
    if "errors" in payload:
        raise Exception(f"{label} returned errors: {payload['errors']}")
    return payload["data"]
