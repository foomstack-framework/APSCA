"""
Shared version utilities for APSCA scripts.
"""

from typing import Dict, List, Optional


def get_current_version(versions: List[Dict]) -> Optional[Dict]:
    """Get the current (non-superseded) version from a versions list."""
    if not versions:
        return None
    active_versions = [v for v in versions if v.get("status") != "superseded"]
    if active_versions:
        return max(active_versions, key=lambda v: v.get("version", 0))
    return max(versions, key=lambda v: v.get("version", 0))
