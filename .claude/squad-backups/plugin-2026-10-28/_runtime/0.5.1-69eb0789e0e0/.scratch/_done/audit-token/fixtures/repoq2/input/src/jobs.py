from config import load as read_settings
def run(job):
    return job, read_settings({"retries": 5})["retries"]
