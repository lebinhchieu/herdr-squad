DEFAULTS = {"retries": 3, "timeout_s": 45, "region": "eu"}
OVERRIDES_FILE = "overrides.json"
def load(overrides=None):
    d = dict(DEFAULTS); d.update(overrides or {}); return d
def reload():
    return load()
