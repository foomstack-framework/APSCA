#!/usr/bin/env python3
"""
build_version.py - Generate version.json for cache invalidation detection.

Creates docs/version.json containing the git commit hash and build timestamp.
This file is used by pages to detect when a newer version has been deployed.

Usage:
    python scripts/build_version.py
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Output path
DOCS_DIR = Path(__file__).parent.parent / "docs"
VERSION_FILE = DOCS_DIR / "version.json"


def get_git_commit_hash() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback for environments without git
        return "unknown"


def get_git_commit_short() -> str:
    """Get the short git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main():
    """Generate version.json file."""
    commit_hash = get_git_commit_hash()
    commit_short = get_git_commit_short()
    build_time = datetime.now(timezone.utc).isoformat()

    version_data = {
        "commit": commit_hash,
        "commit_short": commit_short,
        "build_time": build_time,
    }

    # Ensure docs directory exists
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Write version.json
    VERSION_FILE.write_text(
        json.dumps(version_data, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Generated {VERSION_FILE}")
    print(f"  Commit: {commit_short} ({commit_hash[:12]}...)")
    print(f"  Build time: {build_time}")


if __name__ == "__main__":
    main()
