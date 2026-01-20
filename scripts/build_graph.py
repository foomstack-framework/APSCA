#!/usr/bin/env python3
"""
build_graph.py - Generate relationship graph for APSCA requirements repository.

Generates reports/graph.json containing nodes and edges representing
all artifacts and their relationships for impact analysis and traversal.

Usage:
    python scripts/build_graph.py
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

from lib.config import DATA_FILES, REPORTS_DIR
from lib.io import load_json

# Output file (script-specific)
GRAPH_FILE = REPORTS_DIR / "graph.json"


def build_graph() -> Dict[str, Any]:
    """Build the complete relationship graph."""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    # Load all data
    releases = load_json(DATA_FILES["releases"])
    artifacts = load_json(DATA_FILES["artifacts"])
    requirements = load_json(DATA_FILES["requirements"])
    features = load_json(DATA_FILES["features"])
    epics = load_json(DATA_FILES["epics"])
    stories = load_json(DATA_FILES["stories"])

    # ==========================================================================
    # Build Nodes
    # ==========================================================================

    # Release nodes
    for release in releases:
        nodes.append({
            "id": release["id"],
            "type": "release",
            "title": release.get("title", release["id"]),
            "status": release.get("status"),
            "release_date": release.get("release_date"),
        })

    # Artifact nodes
    for entry in artifacts:
        nodes.append({
            "id": entry["id"],
            "type": "artifact",
            "title": entry.get("title"),
            "status": entry.get("status"),
            "artifact_type": entry.get("type"),
        })

    # Requirement nodes
    for req in requirements:
        nodes.append({
            "id": req["id"],
            "type": "requirement",
            "title": req.get("title"),
            "status": req.get("status"),
            "req_type": req.get("type"),
            "invariant": req.get("invariant", False),
        })

    # Feature nodes
    for feat in features:
        nodes.append({
            "id": feat["id"],
            "type": "feature",
            "title": feat.get("title"),
            "status": feat.get("status"),
        })

    # Epic nodes (both epic-level and version-level)
    for epic in epics:
        epic_id = epic["id"]

        # Epic-level node
        nodes.append({
            "id": epic_id,
            "type": "epic",
            "title": epic.get("title"),
            "feature_ref": epic.get("feature_ref"),
        })

        # Version-level nodes
        for version in epic.get("versions", []):
            v_num = version.get("version")
            version_id = f"{epic_id}:v{v_num}"
            nodes.append({
                "id": version_id,
                "type": "epic_version",
                "epic_id": epic_id,
                "version": v_num,
                "status": version.get("status"),
                "release_ref": version.get("release_ref"),
                "summary": version.get("summary"),
            })

    # Story nodes (both story-level and version-level)
    for story in stories:
        story_id = story["id"]

        # Story-level node
        nodes.append({
            "id": story_id,
            "type": "story",
            "title": story.get("title"),
            "epic_ref": story.get("epic_ref"),
        })

        # Version-level nodes
        for version in story.get("versions", []):
            v_num = version.get("version")
            version_id = f"{story_id}:v{v_num}"
            nodes.append({
                "id": version_id,
                "type": "story_version",
                "story_id": story_id,
                "version": v_num,
                "status": version.get("status"),
                "release_ref": version.get("release_ref"),
                "description": version.get("description"),
            })

    # ==========================================================================
    # Build Edges
    # ==========================================================================

    # Requirements -> Artifacts (references_artifact)
    for req in requirements:
        for artifact_ref in req.get("artifact_refs", []):
            edges.append({
                "source": req["id"],
                "target": artifact_ref,
                "type": "references_artifact",
            })

        # Requirement supersedes
        superseded_by = req.get("superseded_by")
        if superseded_by:
            edges.append({
                "source": superseded_by,
                "target": req["id"],
                "type": "supersedes",
            })

    # Features -> Requirements (satisfies)
    for feat in features:
        for req_ref in feat.get("requirement_refs", []):
            edges.append({
                "source": feat["id"],
                "target": req_ref,
                "type": "satisfies",
            })

        for artifact_ref in feat.get("artifact_refs", []):
            edges.append({
                "source": feat["id"],
                "target": artifact_ref,
                "type": "references_artifact",
            })

    # Epics -> Features (scoped_by)
    for epic in epics:
        epic_id = epic["id"]
        feature_ref = epic.get("feature_ref")
        if feature_ref:
            edges.append({
                "source": epic_id,
                "target": feature_ref,
                "type": "scoped_by",
            })

        # Epic versions
        for version in epic.get("versions", []):
            v_num = version.get("version")
            version_id = f"{epic_id}:v{v_num}"

            # Version -> Epic (version_of)
            edges.append({
                "source": version_id,
                "target": epic_id,
                "type": "version_of",
            })

            # Version -> Release (assigned_to_release)
            release_ref = version.get("release_ref")
            if release_ref:
                edges.append({
                    "source": version_id,
                    "target": release_ref,
                    "type": "assigned_to_release",
                })

            # Version -> Requirements (satisfies)
            for req_ref in version.get("requirement_refs", []):
                edges.append({
                    "source": version_id,
                    "target": req_ref,
                    "type": "satisfies",
                })

            # Version -> Artifacts (references_artifact)
            for artifact_ref in version.get("artifact_refs", []):
                edges.append({
                    "source": version_id,
                    "target": artifact_ref,
                    "type": "references_artifact",
                })

            # Version supersedes previous version
            supersedes = version.get("supersedes")
            if supersedes:
                prev_version_id = f"{epic_id}:v{supersedes}"
                edges.append({
                    "source": version_id,
                    "target": prev_version_id,
                    "type": "supersedes",
                })

    # Stories -> Epics (belongs_to)
    for story in stories:
        story_id = story["id"]
        epic_ref = story.get("epic_ref")
        if epic_ref:
            edges.append({
                "source": story_id,
                "target": epic_ref,
                "type": "belongs_to",
            })

        # Story versions
        for version in story.get("versions", []):
            v_num = version.get("version")
            version_id = f"{story_id}:v{v_num}"

            # Version -> Story (version_of)
            edges.append({
                "source": version_id,
                "target": story_id,
                "type": "version_of",
            })

            # Version -> Release (assigned_to_release)
            release_ref = version.get("release_ref")
            if release_ref:
                edges.append({
                    "source": version_id,
                    "target": release_ref,
                    "type": "assigned_to_release",
                })

            # Version -> Requirements (satisfies)
            for req_ref in version.get("requirement_refs", []):
                edges.append({
                    "source": version_id,
                    "target": req_ref,
                    "type": "satisfies",
                })

            # Version -> Artifacts (references_artifact)
            for artifact_ref in version.get("artifact_refs", []):
                edges.append({
                    "source": version_id,
                    "target": artifact_ref,
                    "type": "references_artifact",
                })

            # Version supersedes previous version
            supersedes = version.get("supersedes")
            if supersedes:
                prev_version_id = f"{story_id}:v{supersedes}"
                edges.append({
                    "source": version_id,
                    "target": prev_version_id,
                    "type": "supersedes",
                })

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": list(set(n["type"] for n in nodes)),
            "edge_types": list(set(e["type"] for e in edges)),
        }
    }


def main():
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Build and save graph
    graph = build_graph()

    GRAPH_FILE.write_text(
        json.dumps(graph, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"Graph generated: {GRAPH_FILE}")
    print(f"  Nodes: {graph['metadata']['node_count']}")
    print(f"  Edges: {graph['metadata']['edge_count']}")
    print(f"  Node types: {', '.join(graph['metadata']['node_types'])}")
    print(f"  Edge types: {', '.join(graph['metadata']['edge_types'])}")


if __name__ == "__main__":
    main()
