from pathlib import Path

BASE_DIR = Path(r"A:\HCL Project")
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_FILE = DATA_DIR / "events.jsonl"
