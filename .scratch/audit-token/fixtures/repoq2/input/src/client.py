import config
def fetch(url):
    return (url, config.load()["timeout_s"])
