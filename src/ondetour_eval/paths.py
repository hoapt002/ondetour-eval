from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = ROOT / "prompts"
SCHEMAS_DIR = ROOT / "schemas"
DATASETS_DIR = ROOT / "datasets"
DATA_DIR = ROOT / "data"
RUNS_DIR = ROOT / "runs"
CACHE_DIR = RUNS_DIR / "cache"
