"""
Shared version utilities for APSCA scripts.
"""

from typing import Dict, List, Optional


def get_current_version(versions: List[Dict]) -> Optional[Dict]:
    """Get the current version from a versions list.

    Returns the version with status 'backlog' (the active work version),
    or the highest version number if none is in backlog.
    """
    if not versions:
        return None
    # Look for the active backlog version first
    backlog_versions = [v for v in versions if v.get("status") == "backlog"]
    if backlog_versions:
        return max(backlog_versions, key=lambda v: v.get("version", 0))
    # Fall back to highest version number
    return max(versions, key=lambda v: v.get("version", 0))
