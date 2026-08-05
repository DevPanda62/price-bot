import hmac
import os

KEYS = None


def _load_keys():
    global KEYS
    keys = set()
    single = os.getenv("API_SECRET_KEY", "").strip()
    if single:
        keys.add(single)
    for k in os.getenv("API_KEYS", "").split(","):
        k = k.strip()
        if k:
            keys.add(k)
    KEYS = keys
    return keys


def valid_keys():
    if KEYS is None:
        return _load_keys()
    return KEYS


def api_key_valid(given):
    if not given:
        return False
    for k in valid_keys():
        if hmac.compare_digest(given.encode("utf-8"), k.encode("utf-8")):
            return True
    return False
