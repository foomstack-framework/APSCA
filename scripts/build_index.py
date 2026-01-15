#!/usr/bin/env python3
"""
build_index.py - Generate lookup index for APSCA requirements repository.

Generates reports/index.json containing denormalized lookup tables
for fast search and display across all artifact types.

Usage:
    python scripts/build_index.py
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.config import DATA_FILES, REPORTS_DIR
from lib.io import load_json
from lib.versions import get_current_version

# Output file (script-specific)
INDEX_FILE = REPORTS_DIR / "index.json"


def build_index() -> Dict[str, Any]:
    """Build the complete lookup index."""
    # Load all data
    releases = load_json(DATA_FILES["releases"])
    domain = load_json(DATA_FILES["domain"])
    requirements = load_json(DATA_FILES["requirements"])
    features = load_json(DATA_FILES["features"])
    epics = load_json(DATA_FILES["epics"])
    stories = load_json(DATA_FILES["stories"])

    # Build indexes
    index = {
        "by_id": {},
        "by_type": {
            "release": [],
            "domain": [],
            "requirement": [],
            "feature": [],
            "epic": [],
            "story": [],
        },
        "by_status": {},
        "by_release": {},
        "summaries": {},
    }

    # ==========================================================================
    # Index Releases
    # ==========================================================================
    for release in releases:
        rid = release["id"]
        entry = {
            "id": rid,
            "type": "release",
            "title": release.get("title", rid),
            "status": release.get("status"),
            "release_date": release.get("release_date"),
        }
        index["by_id"][rid] = entry
        index["by_type"]["release"].append(rid)

        status = release.get("status")
        if status:
            index["by_status"].setdefault(status, []).append(rid)

        # Initialize release grouping
        index["by_release"][rid] = {"epics": [], "stories": []}

        # Summary for display
        index["summaries"][rid] = f"{rid}: {release.get('description', '')[:100]}"

    # ==========================================================================
    # Index Domain
    # ==========================================================================
    for entry in domain:
        did = entry["id"]
        indexed = {
            "id": did,
            "type": "domain",
            "title": entry.get("title"),
            "status": entry.get("status"),
            "domain_type": entry.get("type"),
            "doc_path": entry.get("doc_path"),
        }
        index["by_id"][did] = indexed
        index["by_type"]["domain"].append(did)

        status = entry.get("status")
        if status:
            index["by_status"].setdefault(status, []).append(did)

        index["summaries"][did] = f"{did}: {entry.get('title', '')}"

    # ==========================================================================
    # Index Requirements
    # ==========================================================================
    for req in requirements:
        rid = req["id"]
        entry = {
            "id": rid,
            "type": "requirement",
            "title": req.get("title"),
            "status": req.get("status"),
            "req_type": req.get("type"),
            "invariant": req.get("invariant", False),
            "domain_refs": req.get("domain_refs", []),
            "superseded_by": req.get("superseded_by"),
        }
        index["by_id"][rid] = entry
        index["by_type"]["requirement"].append(rid)

        status = req.get("status")
        if status:
            index["by_status"].setdefault(status, []).append(rid)

        index["summaries"][rid] = f"{rid}: {req.get('title', '')}"

    # ==========================================================================
    # Index Features
    # ==========================================================================
    for feat in features:
        fid = feat["id"]
        entry = {
            "id": fid,
            "type": "feature",
            "title": feat.get("title"),
            "status": feat.get("status"),
            "requirement_refs": feat.get("requirement_refs", []),
            "domain_refs": feat.get("domain_refs", []),
        }
        index["by_id"][fid] = entry
        index["by_type"]["feature"].append(fid)

        status = feat.get("status")
        if status:
            index["by_status"].setdefault(status, []).append(fid)

        index["summaries"][fid] = f"{fid}: {feat.get('title', '')}"

    # ==========================================================================
    # Index Epics
    # ==========================================================================
    for epic in epics:
        eid = epic["id"]
        current_version = get_current_version(epic.get("versions", []))

        entry = {
            "id": eid,
            "type": "epic",
            "title": epic.get("title"),
            "feature_ref": epic.get("feature_ref"),
            "version_count": len(epic.get("versions", [])),
            "current_version": current_version.get("version") if current_version else None,
            "current_status": current_version.get("status") if current_version else None,
            "current_release_ref": current_version.get("release_ref") if current_version else None,
        }
        index["by_id"][eid] = entry
        index["by_type"]["epic"].append(eid)

        # Add to release grouping
        if current_version and current_version.get("release_ref"):
            release_ref = current_version["release_ref"]
            if release_ref in index["by_release"]:
                index["by_release"][release_ref]["epics"].append(eid)

        status = current_version.get("status") if current_version else None
        if status:
            index["by_status"].setdefault(status, []).append(eid)

        summary = current_version.get("summary", "") if current_version else ""
        index["summaries"][eid] = f"{eid}: {epic.get('title', '')} - {summary[:50]}"

    # ==========================================================================
    # Index Stories
    # ==========================================================================
    for story in stories:
        sid = story["id"]
        current_version = get_current_version(story.get("versions", []))

        entry = {
            "id": sid,
            "type": "story",
            "title": story.get("title"),
            "epic_ref": story.get("epic_ref"),
            "version_count": len(story.get("versions", [])),
            "current_version": current_version.get("version") if current_version else None,
            "current_status": current_version.get("status") if current_version else None,
            "current_release_ref": current_version.get("release_ref") if current_version else None,
            "has_acceptance_criteria": bool(current_version.get("acceptance_criteria")) if current_version else False,
            "has_test_intent": bool(
                current_version.get("test_intent", {}).get("failure_modes") or
                current_version.get("test_intent", {}).get("guarantees")
            ) if current_version else False,
        }
        index["by_id"][sid] = entry
        index["by_type"]["story"].append(sid)

        # Add to release grouping
        if current_version and current_version.get("release_ref"):
            release_ref = current_version["release_ref"]
            if release_ref in index["by_release"]:
                index["by_release"][release_ref]["stories"].append(sid)

        status = current_version.get("status") if current_version else None
        if status:
            index["by_status"].setdefault(status, []).append(sid)

        desc = current_version.get("description", "") if current_version else ""
        index["summaries"][sid] = f"{sid}: {story.get('title', '')} - {desc[:50]}"

    # ==========================================================================
    # Add Metadata
    # ==========================================================================
    index["metadata"] = {
        "total_count": len(index["by_id"]),
        "counts_by_type": {k: len(v) for k, v in index["by_type"].items()},
        "counts_by_status": {k: len(v) for k, v in index["by_status"].items()},
    }

    return index


def main():
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Build and save index
    index = build_index()

    INDEX_FILE.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"Index generated: {INDEX_FILE}")
    print(f"  Total entries: {index['metadata']['total_count']}")
    print(f"  By type: {index['metadata']['counts_by_type']}")
    print(f"  By status: {index['metadata']['counts_by_status']}")


if __name__ == "__main__":
    main()
