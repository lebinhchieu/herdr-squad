from config import load
def fetch(url):
    cfg = load()
    return _get(url, cfg["timeout_s"])
def _get(url, t): return (url, t)
