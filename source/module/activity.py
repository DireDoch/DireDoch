from config import USER_NAME
from module.request_manager import get_events

# ponytail: fixed set — the event types worth broadcasting on a profile
_ALLOWED = {
    "PushEvent", "PullRequestEvent", "IssuesEvent",
    "CreateEvent", "WatchEvent", "ForkEvent", "PullRequestReviewEvent",
}
_MAX_REPO = 22  # keep a line inside profile.svg's left column


def _repo(name: str) -> str:
    owner, _, short = name.partition("/")
    label = short if owner == USER_NAME else name
    return label if len(label) <= _MAX_REPO else label[: _MAX_REPO - 1] + "…"


def _line(ev: dict) -> str | None:
    t = ev["type"]
    repo = _repo(ev["repo"]["name"])
    p = ev.get("payload", {})
    if t == "PushEvent":
        return f"push   {p.get('size', 0)} → {repo}"
    if t == "PullRequestEvent":
        act = "merged" if p.get("pull_request", {}).get("merged") else p.get("action", "")
        return f"PR     #{p.get('number', '')} {act} → {repo}"
    if t == "IssuesEvent":
        return f"issue  #{p.get('issue', {}).get('number', '')} {p.get('action', '')} → {repo}"
    if t == "CreateEvent":
        return f"new    {p.get('ref_type', 'repo')} → {repo}"
    if t == "WatchEvent":
        return f"star   {repo}"
    if t == "ForkEvent":
        return f"fork   {repo}"
    if t == "PullRequestReviewEvent":
        return f"review #{p.get('pull_request', {}).get('number', '')} → {repo}"
    return None


def _collapse_pushes(events: list[dict]) -> list[dict]:
    # merge adjacent same-repo PushEvents into one, summing commit counts
    out: list[dict] = []
    for ev in events:
        ev = dict(ev, payload=dict(ev.get("payload", {})))
        if ev["type"] == "PushEvent":
            ev["payload"]["size"] = ev["payload"].get("size", len(ev["payload"].get("commits", [])))
        prev = out[-1] if out else None
        if (prev and prev["type"] == "PushEvent" == ev["type"]
                and prev["repo"]["name"] == ev["repo"]["name"]):
            prev["payload"]["size"] += ev["payload"]["size"]
        else:
            out.append(ev)
    return out


def get_recent_activity(limit: int = 3) -> list[str]:
    events = [e for e in get_events() if e["type"] in _ALLOWED]
    lines = [_line(e) for e in _collapse_pushes(events)]
    return [l for l in lines if l][:limit]
