"""
Shared configuration constants for APSCA scripts.

Only INPUT paths are centralized here. Each script maintains its own OUTPUT paths.
"""

from pathlib import Path

# Compute paths relative to lib/ location
SCRIPT_DIR = Path(__file__).parent.parent  # scripts/
ROOT_DIR = SCRIPT_DIR.parent               # repo root
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"
REPORTS_DIR = ROOT_DIR / "reports"

# Input data files (shared across all scripts)
DATA_FILES = {
    "releases": DATA_DIR / "releases.json",
    "requirements": DATA_DIR / "requirements.json",
    "features": DATA_DIR / "features.json",
    "epics": DATA_DIR / "epics.json",
    "stories": DATA_DIR / "stories.json",
    "artifacts": DATA_DIR / "artifacts.json",
}
