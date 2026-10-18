import json, os, threading
from pathlib import Path
from config.settings import settings

_lock = threading.Lock()

def _path(name: str) -> Path:
    d = Path(settings.DATA_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{name}.json"

def load(name: str, default):
    p = _path(name)
    if not p.exists():
        save(name, default)
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default

def save(name: str, data):
    p = _path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(p) + ".tmp"
    with _lock:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, p)

# Initial files ensure
for k, v in [
    ("events", {}),
    ("teams", {}),
    ("participants", {}),
    ("questions", {}),
    ("rounds", {}),
]:
    load(k, v)
