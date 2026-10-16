from config import load
def run(job):
    cfg = load({"retries": 5})
    return job, cfg["retries"]
