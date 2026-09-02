import datetime
import os

os.environ.setdefault("ACCESS_TOKEN", "test")  # config.py reads this at import

from module.request_manager import _expiry_warning

NOW = datetime.datetime(2026, 8, 12, 12, 0, tzinfo=datetime.timezone.utc)

# the bug that broke the daily run: a 30-day PAT dying unannounced
assert _expiry_warning("2026-08-19 21:39:33 UTC", NOW) is not None
assert "7 day" in _expiry_warning("2026-08-19 21:39:33 UTC", NOW)
# already dead -> still warns (negative days)
assert "-1 day" in _expiry_warning("2026-08-11 12:00:00 UTC", NOW)
# plenty of time left, or no expiry at all -> silence
assert _expiry_warning("2026-12-01 00:00:00 UTC", NOW) is None
assert _expiry_warning(None, NOW) is None
# non-UTC offset format GitHub also sends
assert _expiry_warning("2026-08-13 04:00:00 -0800", NOW) is not None

print("ok")
