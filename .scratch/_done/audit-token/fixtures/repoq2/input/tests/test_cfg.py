from config import load
def test_load(): assert load()["timeout_s"] == 45
