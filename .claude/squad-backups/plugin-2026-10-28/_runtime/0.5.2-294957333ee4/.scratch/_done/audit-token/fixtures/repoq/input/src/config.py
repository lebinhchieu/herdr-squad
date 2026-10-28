DEFAULTS = {"retries": 3, "timeout_s": 45, "region": "eu"}
def load(overrides=None):
    d = dict(DEFAULTS); d.update(overrides or {}); return d
