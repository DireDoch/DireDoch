import os

os.environ.setdefault("ACCESS_TOKEN", "test")  # config.py reads this at import

from module.activity import _collapse_pushes, _line


def ev(t, repo, **payload):
    return {"type": t, "repo": {"name": repo}, "payload": payload}


# adjacent same-repo pushes merge and sum commit counts
merged = _collapse_pushes([
    ev("PushEvent", "DireDoch/foo", size=3),
    ev("PushEvent", "DireDoch/foo", size=2),
    ev("PushEvent", "DireDoch/bar", size=1),
])
assert len(merged) == 2, merged
assert merged[0]["payload"]["size"] == 5, merged
assert merged[1]["payload"]["size"] == 1, merged

# same repo but non-adjacent stays separate
two = _collapse_pushes([
    ev("PushEvent", "DireDoch/foo", size=1),
    ev("WatchEvent", "x/y"),
    ev("PushEvent", "DireDoch/foo", size=1),
])
assert len([e for e in two if e["type"] == "PushEvent"]) == 2, two

# size falls back to len(commits) when absent
grown = _collapse_pushes([ev("PushEvent", "DireDoch/foo", commits=[1, 2, 3])])
assert grown[0]["payload"]["size"] == 3, grown

# formatting per event type
assert _line(ev("PushEvent", "DireDoch/foo", size=5)) == "push   5 → foo"
assert _line(ev("ForkEvent", "DireDoch/bar")) == "fork   bar"
assert _line(ev("PullRequestEvent", "DireDoch/bar", number=12, action="opened",
               pull_request={"merged": False})) == "PR     #12 opened → bar"
assert _line(ev("PullRequestEvent", "DireDoch/bar", number=9,
               pull_request={"merged": True})) == "PR     #9 merged → bar"
# external repo keeps owner and truncates; own repo drops owner
star = _line(ev("WatchEvent", "anuraghazra/github-readme-stats"))
assert star.startswith("star   anuraghazra/") and star.endswith("…"), star
# unhandled types are dropped
assert _line({"type": "MemberEvent", "repo": {"name": "x/y"}, "payload": {}}) is None

print("ok")
