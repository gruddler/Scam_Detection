from pathlib import Path

# Repo root is one level above the app package.
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_FILE = DATA_DIR / "events.jsonl"
WEB_DIR = BASE_DIR / "web"
