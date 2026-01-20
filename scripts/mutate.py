#!/usr/bin/env python3
"""
mutate.py - Canonical JSON mutation tool for APSCA requirements repository.

All modifications to data/*.json files MUST go through this script.
Never edit canonical JSON directly.

Usage:
    python scripts/mutate.py <operation> --payload '<json>'
    python scripts/mutate.py <operation> --payload-file <path>
"""

import argparse
import json
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.config import DATA_FILES, DATA_DIR
from lib.io import load_json, save_json

# ID prefixes
ID_PREFIXES = {
    "releases": "REL",
    "artifacts": "ART",
    "requirements": "REQ",
    "features": "FEAT",
    "epics": "EPIC",
    "stories": "STORY",
}


# =============================================================================
# Core Helper Functions
# =============================================================================

def now_iso() -> str:
    """Return current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_id(family: str, data: List[Dict]) -> str:
    """Generate next sequential ID for an artifact family."""
    if family == "releases":
        raise ValueError("Release IDs must be provided explicitly (REL-YYYY-MM-DD format)")

    prefix = ID_PREFIXES[family]
    max_num = 0
    pattern = re.compile(rf"^{prefix}-(\d+)$")

    for record in data:
        match = pattern.match(record.get("id", ""))
        if match:
            max_num = max(max_num, int(match.group(1)))

    return f"{prefix}-{max_num + 1:03d}"


def validate_id_format(record_id: str, family: str) -> bool:
    """Validate ID matches expected format for its family."""
    prefix = ID_PREFIXES[family]
    if family == "releases":
        # REL-YYYY-MM-DD or REL-YYYY-MM-DD-a (suffix for same-day releases)
        return bool(re.match(r"^REL-\d{4}-\d{2}-\d{2}(-[a-z])?$", record_id))
    else:
        return bool(re.match(rf"^{prefix}-\d{{3,}}$", record_id))


def id_exists(record_id: str, data: List[Dict]) -> bool:
    """Check if an ID already exists in the data array."""
    return any(record.get("id") == record_id for record in data)


def find_record_by_id(record_id: str, data: List[Dict]) -> Optional[Dict]:
    """Find and return a record by ID, or None if not found."""
    for record in data:
        if record.get("id") == record_id:
            return record
    return None


def validate_refs(refs: List[str], target_data: List[Dict], ref_type: str) -> Optional[str]:
    """Validate that all refs exist in target data. Returns error message or None."""
    for ref_id in refs:
        if not find_record_by_id(ref_id, target_data):
            return f"{ref_type} '{ref_id}' not found"
    return None


def validate_release_ref(release_ref: str, releases: List[Dict]) -> Optional[str]:
    """Validate release exists and is open for new versions."""
    release = find_record_by_id(release_ref, releases)
    if not release:
        return f"Release '{release_ref}' not found"
    if release.get("status") in ("released", "superseded"):
        return f"Cannot add versions to {release.get('status')} release '{release_ref}'"
    return None


def success_response(message: str, data: Optional[Dict] = None) -> Dict:
    """Build a success response object."""
    response = {"status": "success", "message": message}
    if data:
        response["data"] = data
    return response


def error_response(message: str, details: Optional[Dict] = None) -> Dict:
    """Build an error response object."""
    response = {"status": "error", "message": message}
    if details:
        response["details"] = details
    return response


def output_result(result: Dict) -> None:
    """Print result as JSON to stdout and exit with appropriate code."""
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "success" else 1)


# =============================================================================
# Release Operations
# =============================================================================

def create_release(payload: Dict) -> Dict:
    """Create a new release with status: planned."""
    releases = load_json(DATA_FILES["releases"])

    # Validate required fields
    required = ["id", "release_date", "description"]
    for field in required:
        if field not in payload:
            return error_response(f"Missing required field: {field}")

    release_id = payload["id"]

    # Validate ID format
    if not validate_id_format(release_id, "releases"):
        return error_response(f"Invalid release ID format: {release_id}. Expected REL-YYYY-MM-DD")

    # Check for duplicate
    if id_exists(release_id, releases):
        return error_response(f"Release {release_id} already exists")

    # Build record
    timestamp = now_iso()
    record = {
        "id": release_id,
        "title": payload.get("title", release_id),
        "status": "planned",
        "release_date": payload["release_date"],
        "description": payload["description"],
        "git_tag": payload.get("git_tag"),
        "tags": payload.get("tags", []),
        "owner": payload.get("owner", ""),
        "notes": payload.get("notes", ""),
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    releases.append(record)
    save_json(DATA_FILES["releases"], releases)

    return success_response(f"Release {release_id} created successfully", {"id": release_id})


def set_release_status(payload: Dict) -> Dict:
    """Transition release status (planned -> released)."""
    releases = load_json(DATA_FILES["releases"])

    if "id" not in payload or "status" not in payload:
        return error_response("Missing required fields: id, status")

    release_id = payload["id"]
    new_status = payload["status"]

    if new_status != "released":
        return error_response(f"Invalid target status: {new_status}. Must be 'released'")

    release = find_record_by_id(release_id, releases)
    if not release:
        return error_response(f"Release {release_id} not found")

    if release["status"] != "planned":
        return error_response(f"Cannot transition from '{release['status']}' to '{new_status}'. Only 'planned' releases can be transitioned.")

    release["status"] = new_status
    release["updated_at"] = now_iso()

    save_json(DATA_FILES["releases"], releases)

    return success_response(f"Release {release_id} status set to {new_status}", {"id": release_id, "status": new_status})


# =============================================================================
# Artifact Operations
# =============================================================================

def add_domain_entry(payload: Dict) -> Dict:
    """Add a new artifact registry entry."""
    artifacts = load_json(DATA_FILES["artifacts"])

    required = ["title", "type", "source", "doc_path"]
    for field in required:
        if field not in payload:
            return error_response(f"Missing required field: {field}")

    valid_types = ["policy", "catalog", "classification", "rule"]
    # Accept type as array or string for backwards compatibility
    entry_type = payload["type"]
    if isinstance(entry_type, str):
        entry_type = [entry_type]
    if not isinstance(entry_type, list):
        return error_response(f"Invalid type: must be an array or string")
    for t in entry_type:
        if t not in valid_types:
            return error_response(f"Invalid type '{t}'. Must be one of {valid_types}")

    dom_id = payload.get("id") or generate_id("artifacts", artifacts)
    if not validate_id_format(dom_id, "artifacts"):
        return error_response(f"Invalid artifact ID format: {dom_id}")
    if id_exists(dom_id, artifacts):
        return error_response(f"Business artifact {dom_id} already exists")

    timestamp = now_iso()
    record = {
        "id": dom_id,
        "title": payload["title"],
        "status": payload.get("status", "draft"),  # Default to draft
        "type": entry_type,  # Always store as array
        "source": payload["source"],
        "effective_date": payload.get("effective_date"),
        "doc_path": payload["doc_path"],
        "description": payload.get("description", ""),
        "anchors": payload.get("anchors", []),
        "tags": payload.get("tags", []),
        "owner": payload.get("owner", ""),
        "notes": payload.get("notes", ""),
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    artifacts.append(record)
    save_json(DATA_FILES["artifacts"], artifacts)

    return success_response(f"Business artifact {dom_id} created successfully", {"id": dom_id})


def update_domain_entry(payload: Dict) -> Dict:
    """Update metadata for existing business artifact."""
    artifacts = load_json(DATA_FILES["artifacts"])

    if "id" not in payload:
        return error_response("Missing required field: id")

    dom_id = payload["id"]
    record = find_record_by_id(dom_id, artifacts)
    if not record:
        return error_response(f"Business artifact {dom_id} not found")

    if record["status"] == "deprecated":
        return error_response(f"Cannot update deprecated business artifact {dom_id}")

    updatable = ["title", "type", "source", "effective_date", "doc_path", "anchors", "tags", "owner", "notes"]
    for field in updatable:
        if field in payload:
            record[field] = payload[field]

    record["updated_at"] = now_iso()
    save_json(DATA_FILES["artifacts"], artifacts)

    return success_response(f"Business artifact {dom_id} updated successfully", {"id": dom_id})


def deprecate_domain_entry(payload: Dict) -> Dict:
    """Set business artifact status to deprecated."""
    artifacts = load_json(DATA_FILES["artifacts"])

    if "id" not in payload:
        return error_response("Missing required field: id")

    dom_id = payload["id"]
    record = find_record_by_id(dom_id, artifacts)
    if not record:
        return error_response(f"Domain entry {dom_id} not found")

    record["status"] = "deprecated"
    record["updated_at"] = now_iso()
    save_json(DATA_FILES["artifacts"], artifacts)

    return success_response(f"Domain entry {dom_id} deprecated", {"id": dom_id})


# =============================================================================
# Requirement Operations
# =============================================================================

def add_requirement(payload: Dict) -> Dict:
    """Add a new requirement."""
    requirements = load_json(DATA_FILES["requirements"])
    artifacts = load_json(DATA_FILES["artifacts"])

    required = ["title", "type", "statement", "rationale"]
    for field in required:
        if field not in payload:
            return error_response(f"Missing required field: {field}")

    if payload["type"] not in ("functional", "non-functional"):
        return error_response(f"Invalid type: {payload['type']}. Must be 'functional' or 'non-functional'")

    req_id = payload.get("id") or generate_id("requirements", requirements)
    if not validate_id_format(req_id, "requirements"):
        return error_response(f"Invalid requirement ID format: {req_id}")
    if id_exists(req_id, requirements):
        return error_response(f"Requirement {req_id} already exists")

    artifact_refs = payload.get("artifact_refs", [])
    if artifact_refs:
        err = validate_refs(artifact_refs, artifacts, "Artifact reference")
        if err:
            return error_response(err)

    timestamp = now_iso()
    record = {
        "id": req_id,
        "title": payload["title"],
        "status": "active",
        "type": payload["type"],
        "invariant": payload.get("invariant", False),
        "statement": payload["statement"],
        "rationale": payload["rationale"],
        "artifact_refs": artifact_refs,
        "superseded_by": None,
        "tags": payload.get("tags", []),
        "owner": payload.get("owner", ""),
        "notes": payload.get("notes", ""),
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    requirements.append(record)
    save_json(DATA_FILES["requirements"], requirements)

    return success_response(f"Requirement {req_id} created successfully", {"id": req_id})


def update_requirement(payload: Dict) -> Dict:
    """Update requirement fields (minor fixes only)."""
    requirements = load_json(DATA_FILES["requirements"])
    artifacts = load_json(DATA_FILES["artifacts"])

    if "id" not in payload:
        return error_response("Missing required field: id")

    req_id = payload["id"]
    record = find_record_by_id(req_id, requirements)
    if not record:
        return error_response(f"Requirement {req_id} not found")

    if record["status"] == "deprecated":
        return error_response(f"Cannot update deprecated requirement {req_id}")

    if "artifact_refs" in payload:
        err = validate_refs(payload["artifact_refs"], artifacts, "Artifact reference")
        if err:
            return error_response(err)

    updatable = ["title", "invariant", "statement", "rationale", "artifact_refs", "tags", "owner", "notes"]
    for field in updatable:
        if field in payload:
            record[field] = payload[field]

    record["updated_at"] = now_iso()
    save_json(DATA_FILES["requirements"], requirements)

    return success_response(f"Requirement {req_id} updated successfully", {"id": req_id})


def deprecate_requirement(payload: Dict) -> Dict:
    """Set requirement status to deprecated."""
    requirements = load_json(DATA_FILES["requirements"])

    if "id" not in payload:
        return error_response("Missing required field: id")

    req_id = payload["id"]
    record = find_record_by_id(req_id, requirements)
    if not record:
        return error_response(f"Requirement {req_id} not found")

    record["status"] = "deprecated"
    record["updated_at"] = now_iso()
    save_json(DATA_FILES["requirements"], requirements)

    return success_response(f"Requirement {req_id} deprecated", {"id": req_id})


def supersede_requirement(payload: Dict) -> Dict:
    """Create new requirement that supersedes an existing one."""
    requirements = load_json(DATA_FILES["requirements"])
    artifacts = load_json(DATA_FILES["artifacts"])

    if "old_id" not in payload or "new_requirement" not in payload:
        return error_response("Missing required fields: old_id, new_requirement")

    old_id = payload["old_id"]
    old_record = find_record_by_id(old_id, requirements)
    if not old_record:
        return error_response(f"Requirement {old_id} not found")

    if old_record["status"] == "deprecated":
        return error_response(f"Requirement {old_id} is already deprecated")

    new_payload = payload["new_requirement"]

    required = ["title", "type", "statement", "rationale"]
    for field in required:
        if field not in new_payload:
            return error_response(f"New requirement missing required field: {field}")

    new_id = new_payload.get("id") or generate_id("requirements", requirements)
    if not validate_id_format(new_id, "requirements"):
        return error_response(f"Invalid requirement ID format: {new_id}")
    if id_exists(new_id, requirements):
        return error_response(f"Requirement {new_id} already exists")

    artifact_refs = new_payload.get("artifact_refs", [])
    if artifact_refs:
        err = validate_refs(artifact_refs, artifacts, "Artifact reference")
        if err:
            return error_response(err)

    timestamp = now_iso()

    new_record = {
        "id": new_id,
        "title": new_payload["title"],
        "status": "active",
        "type": new_payload["type"],
        "invariant": new_payload.get("invariant", False),
        "statement": new_payload["statement"],
        "rationale": new_payload["rationale"],
        "artifact_refs": artifact_refs,
        "superseded_by": None,
        "tags": new_payload.get("tags", []),
        "owner": new_payload.get("owner", ""),
        "notes": new_payload.get("notes", ""),
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    requirements.append(new_record)

    old_record["status"] = "deprecated"
    old_record["superseded_by"] = new_id
    old_record["updated_at"] = timestamp

    save_json(DATA_FILES["requirements"], requirements)

    return success_response(
        f"Requirement {old_id} superseded by {new_id}",
        {"old_id": old_id, "new_id": new_id}
    )


# =============================================================================
# Feature Operations
# =============================================================================

def add_feature(payload: Dict) -> Dict:
    """Add a new feature."""
    features = load_json(DATA_FILES["features"])
    requirements = load_json(DATA_FILES["requirements"])
    artifacts = load_json(DATA_FILES["artifacts"])

    required = ["title", "purpose", "business_value"]
    for field in required:
        if field not in payload:
            return error_response(f"Missing required field: {field}")

    feat_id = payload.get("id") or generate_id("features", features)
    if not validate_id_format(feat_id, "features"):
        return error_response(f"Invalid feature ID format: {feat_id}")
    if id_exists(feat_id, features):
        return error_response(f"Feature {feat_id} already exists")

    requirement_refs = payload.get("requirement_refs", [])
    if requirement_refs:
        err = validate_refs(requirement_refs, requirements, "Requirement reference")
        if err:
            return error_response(err)

    artifact_refs = payload.get("artifact_refs", [])
    if artifact_refs:
        err = validate_refs(artifact_refs, artifacts, "Artifact reference")
        if err:
            return error_response(err)

    timestamp = now_iso()
    record = {
        "id": feat_id,
        "title": payload["title"],
        "status": "active",
        "purpose": payload["purpose"],
        "business_value": payload["business_value"],
        "in_scope": payload.get("in_scope", []),
        "out_of_scope": payload.get("out_of_scope", []),
        "requirement_refs": requirement_refs,
        "artifact_refs": artifact_refs,
        "tags": payload.get("tags", []),
        "owner": payload.get("owner", ""),
        "notes": payload.get("notes", ""),
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    features.append(record)
    save_json(DATA_FILES["features"], features)

    return success_response(f"Feature {feat_id} created successfully", {"id": feat_id})


def update_feature(payload: Dict) -> Dict:
    """Update feature fields."""
    features = load_json(DATA_FILES["features"])
    requirements = load_json(DATA_FILES["requirements"])
    artifacts = load_json(DATA_FILES["artifacts"])

    if "id" not in payload:
        return error_response("Missing required field: id")

    feat_id = payload["id"]
    record = find_record_by_id(feat_id, features)
    if not record:
        return error_response(f"Feature {feat_id} not found")

    if record["status"] == "deprecated":
        return error_response(f"Cannot update deprecated feature {feat_id}")

    if "requirement_refs" in payload:
        err = validate_refs(payload["requirement_refs"], requirements, "Requirement reference")
        if err:
            return error_response(err)

    if "artifact_refs" in payload:
        err = validate_refs(payload["artifact_refs"], artifacts, "Artifact reference")
        if err:
            return error_response(err)

    updatable = ["title", "purpose", "business_value", "in_scope", "out_of_scope",
                 "requirement_refs", "artifact_refs", "tags", "owner", "notes"]
    for field in updatable:
        if field in payload:
            record[field] = payload[field]

    record["updated_at"] = now_iso()
    save_json(DATA_FILES["features"], features)

    return success_response(f"Feature {feat_id} updated successfully", {"id": feat_id})


def deprecate_feature(payload: Dict) -> Dict:
    """Set feature status to deprecated."""
    features = load_json(DATA_FILES["features"])

    if "id" not in payload:
        return error_response("Missing required field: id")

    feat_id = payload["id"]
    record = find_record_by_id(feat_id, features)
    if not record:
        return error_response(f"Feature {feat_id} not found")

    record["status"] = "deprecated"
    record["updated_at"] = now_iso()
    save_json(DATA_FILES["features"], features)

    return success_response(f"Feature {feat_id} deprecated", {"id": feat_id})


# =============================================================================
# Epic Operations (Versioned)
# =============================================================================

def add_epic(payload: Dict) -> Dict:
    """Add a new epic with initial version."""
    epics = load_json(DATA_FILES["epics"])
    features = load_json(DATA_FILES["features"])
    releases = load_json(DATA_FILES["releases"])
    requirements = load_json(DATA_FILES["requirements"])
    artifacts = load_json(DATA_FILES["artifacts"])

    required = ["title", "feature_ref", "release_ref", "summary"]
    for field in required:
        if field not in payload:
            return error_response(f"Missing required field: {field}")

    if not find_record_by_id(payload["feature_ref"], features):
        return error_response(f"Feature {payload['feature_ref']} not found")

    err = validate_release_ref(payload["release_ref"], releases)
    if err:
        return error_response(err)

    requirement_refs = payload.get("requirement_refs", [])
    if requirement_refs:
        err = validate_refs(requirement_refs, requirements, "Requirement reference")
        if err:
            return error_response(err)

    artifact_refs = payload.get("artifact_refs", [])
    if artifact_refs:
        err = validate_refs(artifact_refs, artifacts, "Artifact reference")
        if err:
            return error_response(err)

    epic_id = payload.get("id") or generate_id("epics", epics)
    if not validate_id_format(epic_id, "epics"):
        return error_response(f"Invalid epic ID format: {epic_id}")
    if id_exists(epic_id, epics):
        return error_response(f"Epic {epic_id} already exists")

    timestamp = now_iso()

    version = {
        "version": 1,
        "status": "backlog",
        "approved": False,
        "release_ref": payload["release_ref"],
        "summary": payload["summary"],
        "assumptions": payload.get("assumptions", []),
        "constraints": payload.get("constraints", []),
        "requirement_refs": requirement_refs,
        "artifact_refs": artifact_refs,
        "supersedes": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "owner": payload.get("owner", ""),
        "notes": payload.get("notes", ""),
    }

    record = {
        "id": epic_id,
        "title": payload["title"],
        "status": "active",
        "feature_ref": payload["feature_ref"],
        "tags": payload.get("tags", []),
        "owner": payload.get("owner", ""),
        "created_at": timestamp,
        "versions": [version],
    }

    epics.append(record)
    save_json(DATA_FILES["epics"], epics)

    return success_response(
        f"Epic {epic_id} created with version 1",
        {"id": epic_id, "version": 1}
    )


def create_epic_version(payload: Dict) -> Dict:
    """Add new version to existing epic. Auto-supersedes previous version."""
    epics = load_json(DATA_FILES["epics"])
    releases = load_json(DATA_FILES["releases"])
    requirements = load_json(DATA_FILES["requirements"])
    artifacts = load_json(DATA_FILES["artifacts"])

    if "epic_id" not in payload or "release_ref" not in payload or "summary" not in payload:
        return error_response("Missing required fields: epic_id, release_ref, summary")

    epic_id = payload["epic_id"]
    epic = find_record_by_id(epic_id, epics)
    if not epic:
        return error_response(f"Epic {epic_id} not found")

    err = validate_release_ref(payload["release_ref"], releases)
    if err:
        return error_response(err)

    requirement_refs = payload.get("requirement_refs", [])
    if requirement_refs:
        err = validate_refs(requirement_refs, requirements, "Requirement reference")
        if err:
            return error_response(err)

    artifact_refs = payload.get("artifact_refs", [])
    if artifact_refs:
        err = validate_refs(artifact_refs, artifacts, "Artifact reference")
        if err:
            return error_response(err)

    # Find the backlog version (active work version)
    backlog_versions = [v for v in epic["versions"] if v.get("status") == "backlog"]
    if not backlog_versions:
        return error_response(f"Epic {epic_id} has no backlog version to supersede")

    current_version = backlog_versions[0]
    current_version_num = current_version["version"]

    timestamp = now_iso()
    new_version_num = max(v["version"] for v in epic["versions"]) + 1

    # Set previous version status based on approval
    if current_version.get("approved"):
        current_version["status"] = "released"
    else:
        current_version["status"] = "discarded"
    current_version["updated_at"] = timestamp

    new_version = {
        "version": new_version_num,
        "status": "backlog",
        "approved": False,
        "release_ref": payload["release_ref"],
        "summary": payload["summary"],
        "assumptions": payload.get("assumptions", current_version.get("assumptions", [])),
        "constraints": payload.get("constraints", current_version.get("constraints", [])),
        "requirement_refs": requirement_refs or current_version.get("requirement_refs", []),
        "artifact_refs": artifact_refs or current_version.get("artifact_refs", []),
        "supersedes": current_version_num,
        "created_at": timestamp,
        "updated_at": timestamp,
        "owner": payload.get("owner", ""),
        "notes": payload.get("notes", ""),
    }

    epic["versions"].append(new_version)
    save_json(DATA_FILES["epics"], epics)

    return success_response(
        f"Epic {epic_id} version {new_version_num} created",
        {"id": epic_id, "version": new_version_num, "superseded_version": current_version_num}
    )


def set_epic_version_status(payload: Dict) -> Dict:
    """Change status of epic version (backlog | released | discarded)."""
    epics = load_json(DATA_FILES["epics"])

    if "epic_id" not in payload or "status" not in payload:
        return error_response("Missing required fields: epic_id, status")

    epic_id = payload["epic_id"]
    new_status = payload["status"]

    valid_statuses = ("backlog", "released", "discarded")
    if new_status not in valid_statuses:
        return error_response(f"Invalid status: {new_status}. Must be one of {valid_statuses}")

    epic = find_record_by_id(epic_id, epics)
    if not epic:
        return error_response(f"Epic {epic_id} not found")

    version_num = payload.get("version")
    if version_num:
        version = next((v for v in epic["versions"] if v["version"] == version_num), None)
        if not version:
            return error_response(f"Epic {epic_id} version {version_num} not found")
    else:
        # Find backlog version by default
        backlog_versions = [v for v in epic["versions"] if v.get("status") == "backlog"]
        if backlog_versions:
            version = backlog_versions[0]
            version_num = version["version"]
        else:
            version_num = max(v["version"] for v in epic["versions"])
            version = next(v for v in epic["versions"] if v["version"] == version_num)

    # Can't modify released or discarded versions
    if version["status"] in ("released", "discarded"):
        return error_response(f"Cannot modify {version['status']} version {version_num}")

    # Enforce single-backlog rule
    if new_status == "backlog":
        existing_backlog = [v for v in epic["versions"] if v.get("status") == "backlog" and v["version"] != version_num]
        if existing_backlog:
            return error_response(f"Cannot set to backlog: version {existing_backlog[0]['version']} is already in backlog")

    version["status"] = new_status
    version["updated_at"] = now_iso()
    save_json(DATA_FILES["epics"], epics)

    return success_response(
        f"Epic {epic_id} version {version_num} status set to {new_status}",
        {"id": epic_id, "version": version_num, "status": new_status}
    )


# =============================================================================
# Story Operations (Versioned)
# =============================================================================

def add_story(payload: Dict) -> Dict:
    """Add a new story with initial version."""
    stories = load_json(DATA_FILES["stories"])
    epics = load_json(DATA_FILES["epics"])
    releases = load_json(DATA_FILES["releases"])
    requirements = load_json(DATA_FILES["requirements"])
    artifacts = load_json(DATA_FILES["artifacts"])

    required = ["title", "epic_ref", "release_ref", "description"]
    for field in required:
        if field not in payload:
            return error_response(f"Missing required field: {field}")

    if not find_record_by_id(payload["epic_ref"], epics):
        return error_response(f"Epic {payload['epic_ref']} not found")

    err = validate_release_ref(payload["release_ref"], releases)
    if err:
        return error_response(err)

    requirement_refs = payload.get("requirement_refs", [])
    if requirement_refs:
        err = validate_refs(requirement_refs, requirements, "Requirement reference")
        if err:
            return error_response(err)

    artifact_refs = payload.get("artifact_refs", [])
    if artifact_refs:
        err = validate_refs(artifact_refs, artifacts, "Artifact reference")
        if err:
            return error_response(err)

    story_id = payload.get("id") or generate_id("stories", stories)
    if not validate_id_format(story_id, "stories"):
        return error_response(f"Invalid story ID format: {story_id}")
    if id_exists(story_id, stories):
        return error_response(f"Story {story_id} already exists")

    timestamp = now_iso()

    test_intent = payload.get("test_intent", {
        "failure_modes": [],
        "guarantees": [],
        "exclusions": []
    })

    version = {
        "version": 1,
        "status": "backlog",
        "approved": False,
        "release_ref": payload["release_ref"],
        "description": payload["description"],
        "requirement_refs": requirement_refs,
        "artifact_refs": artifact_refs,
        "acceptance_criteria": payload.get("acceptance_criteria", []),
        "test_intent": test_intent,
        "supersedes": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "owner": payload.get("owner", ""),
        "notes": payload.get("notes", ""),
    }

    record = {
        "id": story_id,
        "title": payload["title"],
        "status": "active",
        "epic_ref": payload["epic_ref"],
        "tags": payload.get("tags", []),
        "owner": payload.get("owner", ""),
        "created_at": timestamp,
        "versions": [version],
    }

    stories.append(record)
    save_json(DATA_FILES["stories"], stories)

    return success_response(
        f"Story {story_id} created with version 1",
        {"id": story_id, "version": 1}
    )


def create_story_version(payload: Dict) -> Dict:
    """Add new version to existing story. Auto-supersedes previous version."""
    stories = load_json(DATA_FILES["stories"])
    releases = load_json(DATA_FILES["releases"])
    requirements = load_json(DATA_FILES["requirements"])
    artifacts = load_json(DATA_FILES["artifacts"])

    if "story_id" not in payload or "release_ref" not in payload or "description" not in payload:
        return error_response("Missing required fields: story_id, release_ref, description")

    story_id = payload["story_id"]
    story = find_record_by_id(story_id, stories)
    if not story:
        return error_response(f"Story {story_id} not found")

    err = validate_release_ref(payload["release_ref"], releases)
    if err:
        return error_response(err)

    requirement_refs = payload.get("requirement_refs", [])
    if requirement_refs:
        err = validate_refs(requirement_refs, requirements, "Requirement reference")
        if err:
            return error_response(err)

    artifact_refs = payload.get("artifact_refs", [])
    if artifact_refs:
        err = validate_refs(artifact_refs, artifacts, "Artifact reference")
        if err:
            return error_response(err)

    # Find the backlog version (active work version)
    backlog_versions = [v for v in story["versions"] if v.get("status") == "backlog"]
    if not backlog_versions:
        return error_response(f"Story {story_id} has no backlog version to supersede")

    current_version = backlog_versions[0]
    current_version_num = current_version["version"]

    timestamp = now_iso()
    new_version_num = max(v["version"] for v in story["versions"]) + 1

    # Set previous version status based on approval
    if current_version.get("approved"):
        current_version["status"] = "released"
    else:
        current_version["status"] = "discarded"
    current_version["updated_at"] = timestamp

    new_version = {
        "version": new_version_num,
        "status": "backlog",
        "approved": False,
        "release_ref": payload["release_ref"],
        "description": payload["description"],
        "requirement_refs": requirement_refs or current_version.get("requirement_refs", []),
        "artifact_refs": artifact_refs or current_version.get("artifact_refs", []),
        "acceptance_criteria": payload.get("acceptance_criteria", current_version.get("acceptance_criteria", [])),
        "test_intent": payload.get("test_intent", current_version.get("test_intent", {})),
        "supersedes": current_version_num,
        "created_at": timestamp,
        "updated_at": timestamp,
        "owner": payload.get("owner", ""),
        "notes": payload.get("notes", ""),
    }

    story["versions"].append(new_version)
    save_json(DATA_FILES["stories"], stories)

    return success_response(
        f"Story {story_id} version {new_version_num} created",
        {"id": story_id, "version": new_version_num, "superseded_version": current_version_num}
    )


def set_story_status(payload: Dict) -> Dict:
    """Change status of story version (backlog | released | discarded)."""
    stories = load_json(DATA_FILES["stories"])

    if "story_id" not in payload or "status" not in payload:
        return error_response("Missing required fields: story_id, status")

    story_id = payload["story_id"]
    new_status = payload["status"]

    valid_statuses = ("backlog", "released", "discarded")
    if new_status not in valid_statuses:
        return error_response(f"Invalid status: {new_status}. Must be one of {valid_statuses}")

    story = find_record_by_id(story_id, stories)
    if not story:
        return error_response(f"Story {story_id} not found")

    version_num = payload.get("version")
    if version_num:
        version = next((v for v in story["versions"] if v["version"] == version_num), None)
        if not version:
            return error_response(f"Story {story_id} version {version_num} not found")
    else:
        # Find backlog version by default
        backlog_versions = [v for v in story["versions"] if v.get("status") == "backlog"]
        if backlog_versions:
            version = backlog_versions[0]
            version_num = version["version"]
        else:
            version_num = max(v["version"] for v in story["versions"])
            version = next(v for v in story["versions"] if v["version"] == version_num)

    # Can't modify released or discarded versions
    if version["status"] in ("released", "discarded"):
        return error_response(f"Cannot modify {version['status']} version {version_num}")

    # Enforce single-backlog rule
    if new_status == "backlog":
        existing_backlog = [v for v in story["versions"] if v.get("status") == "backlog" and v["version"] != version_num]
        if existing_backlog:
            return error_response(f"Cannot set to backlog: version {existing_backlog[0]['version']} is already in backlog")

    version["status"] = new_status
    version["updated_at"] = now_iso()
    save_json(DATA_FILES["stories"], stories)

    return success_response(
        f"Story {story_id} version {version_num} status set to {new_status}",
        {"id": story_id, "version": version_num, "status": new_status}
    )


def activate_domain_entry(payload: Dict) -> Dict:
    """Transition business artifact status from draft to active."""
    artifacts = load_json(DATA_FILES["artifacts"])

    if "id" not in payload:
        return error_response("Missing required field: id")

    dom_id = payload["id"]
    entry = find_record_by_id(dom_id, artifacts)
    if not entry:
        return error_response(f"Business artifact {dom_id} not found")

    if entry.get("status") != "draft":
        return error_response(f"Business artifact {dom_id} is not in draft status (current: {entry.get('status')})")

    entry["status"] = "active"
    entry["updated_at"] = now_iso()
    save_json(DATA_FILES["artifacts"], artifacts)

    return success_response(f"Business artifact {dom_id} activated", {"id": dom_id})


def set_epic_approved(payload: Dict) -> Dict:
    """Set approved boolean on epic version."""
    epics = load_json(DATA_FILES["epics"])

    if "epic_id" not in payload or "approved" not in payload:
        return error_response("Missing required fields: epic_id, approved")

    epic_id = payload["epic_id"]
    approved = payload["approved"]

    if not isinstance(approved, bool):
        return error_response("'approved' must be a boolean")

    epic = find_record_by_id(epic_id, epics)
    if not epic:
        return error_response(f"Epic {epic_id} not found")

    version_num = payload.get("version")
    if version_num:
        version = next((v for v in epic["versions"] if v["version"] == version_num), None)
        if not version:
            return error_response(f"Epic {epic_id} version {version_num} not found")
    else:
        # Find backlog version by default
        backlog_versions = [v for v in epic["versions"] if v.get("status") == "backlog"]
        if backlog_versions:
            version = backlog_versions[0]
            version_num = version["version"]
        else:
            return error_response(f"Epic {epic_id} has no backlog version")

    # Can only modify backlog versions
    if version["status"] != "backlog":
        return error_response(f"Cannot modify approved on {version['status']} version {version_num}")

    version["approved"] = approved
    version["updated_at"] = now_iso()
    save_json(DATA_FILES["epics"], epics)

    return success_response(
        f"Epic {epic_id} version {version_num} approved set to {approved}",
        {"id": epic_id, "version": version_num, "approved": approved}
    )


def set_story_approved(payload: Dict) -> Dict:
    """Set approved boolean on story version."""
    stories = load_json(DATA_FILES["stories"])

    if "story_id" not in payload or "approved" not in payload:
        return error_response("Missing required fields: story_id, approved")

    story_id = payload["story_id"]
    approved = payload["approved"]

    if not isinstance(approved, bool):
        return error_response("'approved' must be a boolean")

    story = find_record_by_id(story_id, stories)
    if not story:
        return error_response(f"Story {story_id} not found")

    version_num = payload.get("version")
    if version_num:
        version = next((v for v in story["versions"] if v["version"] == version_num), None)
        if not version:
            return error_response(f"Story {story_id} version {version_num} not found")
    else:
        # Find backlog version by default
        backlog_versions = [v for v in story["versions"] if v.get("status") == "backlog"]
        if backlog_versions:
            version = backlog_versions[0]
            version_num = version["version"]
        else:
            return error_response(f"Story {story_id} has no backlog version")

    # Can only modify backlog versions
    if version["status"] != "backlog":
        return error_response(f"Cannot modify approved on {version['status']} version {version_num}")

    # Validate completeness if setting approved to true
    if approved:
        ac = version.get("acceptance_criteria", [])
        ti = version.get("test_intent", {})

        if not ac:
            return error_response("Cannot approve: missing acceptance_criteria")

        has_test_intent = ti.get("failure_modes") or ti.get("guarantees")
        if not has_test_intent:
            return error_response("Cannot approve: test_intent must have at least one failure_mode or guarantee")

    version["approved"] = approved
    version["updated_at"] = now_iso()
    save_json(DATA_FILES["stories"], stories)

    return success_response(
        f"Story {story_id} version {version_num} approved set to {approved}",
        {"id": story_id, "version": version_num, "approved": approved}
    )


def deprecate_epic(payload: Dict) -> Dict:
    """Deprecate an epic. Sets artifact status to deprecated and discards any backlog version."""
    epics = load_json(DATA_FILES["epics"])

    if "epic_id" not in payload:
        return error_response("Missing required field: epic_id")

    epic_id = payload["epic_id"]
    epic = find_record_by_id(epic_id, epics)
    if not epic:
        return error_response(f"Epic {epic_id} not found")

    if epic.get("status") == "deprecated":
        return error_response(f"Epic {epic_id} is already deprecated")

    timestamp = now_iso()

    # Discard any backlog version
    for version in epic.get("versions", []):
        if version.get("status") == "backlog":
            version["status"] = "discarded"
            version["updated_at"] = timestamp

    epic["status"] = "deprecated"
    save_json(DATA_FILES["epics"], epics)

    return success_response(f"Epic {epic_id} deprecated", {"id": epic_id})


def deprecate_story(payload: Dict) -> Dict:
    """Deprecate a story. Sets artifact status to deprecated and discards any backlog version."""
    stories = load_json(DATA_FILES["stories"])

    if "story_id" not in payload:
        return error_response("Missing required field: story_id")

    story_id = payload["story_id"]
    story = find_record_by_id(story_id, stories)
    if not story:
        return error_response(f"Story {story_id} not found")

    if story.get("status") == "deprecated":
        return error_response(f"Story {story_id} is already deprecated")

    timestamp = now_iso()

    # Discard any backlog version
    for version in story.get("versions", []):
        if version.get("status") == "backlog":
            version["status"] = "discarded"
            version["updated_at"] = timestamp

    story["status"] = "deprecated"
    save_json(DATA_FILES["stories"], stories)

    return success_response(f"Story {story_id} deprecated", {"id": story_id})


# =============================================================================
# CLI Entry Point
# =============================================================================

OPERATIONS = {
    "create_release": create_release,
    "set_release_status": set_release_status,
    "add_domain_entry": add_domain_entry,
    "update_domain_entry": update_domain_entry,
    "activate_domain_entry": activate_domain_entry,
    "deprecate_domain_entry": deprecate_domain_entry,
    "add_requirement": add_requirement,
    "update_requirement": update_requirement,
    "deprecate_requirement": deprecate_requirement,
    "supersede_requirement": supersede_requirement,
    "add_feature": add_feature,
    "update_feature": update_feature,
    "deprecate_feature": deprecate_feature,
    "add_epic": add_epic,
    "create_epic_version": create_epic_version,
    "set_epic_version_status": set_epic_version_status,
    "set_epic_approved": set_epic_approved,
    "deprecate_epic": deprecate_epic,
    "add_story": add_story,
    "create_story_version": create_story_version,
    "set_story_status": set_story_status,
    "set_story_approved": set_story_approved,
    "deprecate_story": deprecate_story,
}


def main():
    parser = argparse.ArgumentParser(
        description="Mutation tool for APSCA canonical JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available operations: {', '.join(sorted(OPERATIONS.keys()))}"
    )
    parser.add_argument(
        "operation",
        choices=sorted(OPERATIONS.keys()),
        help="Mutation operation to perform"
    )
    parser.add_argument(
        "--payload",
        type=str,
        help="JSON payload string"
    )
    parser.add_argument(
        "--payload-file",
        type=str,
        help="Path to JSON payload file"
    )

    args = parser.parse_args()

    if args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as e:
            output_result(error_response(f"Invalid JSON payload: {e}"))
    elif args.payload_file:
        payload_path = Path(args.payload_file)
        if not payload_path.exists():
            output_result(error_response(f"Payload file not found: {args.payload_file}"))
        try:
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            output_result(error_response(f"Invalid JSON in payload file: {e}"))
    else:
        output_result(error_response("Either --payload or --payload-file is required"))

    operation_fn = OPERATIONS[args.operation]
    try:
        result = operation_fn(payload)
        output_result(result)
    except Exception as e:
        output_result(error_response(f"Operation failed: {e}"))


if __name__ == "__main__":
    main()
