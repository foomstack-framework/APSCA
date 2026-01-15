#!/usr/bin/env python3
"""
validate.py - Schema and reference integrity validator for APSCA requirements repository.

Validates all canonical JSON files in data/ for:
- Schema conformance
- ID uniqueness
- Reference integrity
- Release constraints
- Version lineage
- Story completeness

Usage:
    python scripts/validate.py
    python scripts/validate.py --warnings  # Include optional warnings
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Root directory
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"

# Data files
DATA_FILES = {
    "releases": DATA_DIR / "releases.json",
    "domain": DATA_DIR / "domain.json",
    "requirements": DATA_DIR / "requirements.json",
    "features": DATA_DIR / "features.json",
    "epics": DATA_DIR / "epics.json",
    "stories": DATA_DIR / "stories.json",
}

# ID patterns
ID_PATTERNS = {
    "releases": re.compile(r"^REL-\d{4}-\d{2}-\d{2}(-[a-z])?$"),
    "domain": re.compile(r"^DOM-\d{3,}$"),
    "requirements": re.compile(r"^REQ-\d{3,}$"),
    "features": re.compile(r"^FEAT-\d{3,}$"),
    "epics": re.compile(r"^EPIC-\d{3,}$"),
    "stories": re.compile(r"^STORY-\d{3,}$"),
}


class ValidationResult:
    """Collects validation errors and warnings."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def is_valid(self) -> bool:
        return len(self.errors) == 0


def load_json(file_path: Path) -> List[Dict]:
    """Load JSON array from file."""
    if not file_path.exists():
        return []
    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return json.loads(content)


def build_id_set(data: List[Dict]) -> Set[str]:
    """Build set of all IDs in data."""
    return {record.get("id") for record in data if record.get("id")}


# =============================================================================
# Validation Functions
# =============================================================================

def validate_id_format(result: ValidationResult, family: str, data: List[Dict]) -> None:
    """Validate all IDs match expected format."""
    pattern = ID_PATTERNS[family]
    for record in data:
        record_id = record.get("id")
        if not record_id:
            result.error(f"[{family}] Record missing 'id' field")
        elif not pattern.match(record_id):
            result.error(f"[{family}] Invalid ID format: {record_id}")


def validate_id_uniqueness(result: ValidationResult, family: str, data: List[Dict]) -> None:
    """Validate all IDs are unique within family."""
    seen: Set[str] = set()
    for record in data:
        record_id = record.get("id")
        if record_id:
            if record_id in seen:
                result.error(f"[{family}] Duplicate ID: {record_id}")
            seen.add(record_id)


def validate_required_fields(result: ValidationResult, family: str, record: Dict, required: List[str]) -> None:
    """Validate record has all required fields."""
    record_id = record.get("id", "unknown")
    for field in required:
        if field not in record:
            result.error(f"[{family}] {record_id}: Missing required field '{field}'")


def validate_refs(result: ValidationResult, source_family: str, record: Dict,
                  ref_field: str, target_ids: Set[str], target_family: str) -> None:
    """Validate reference fields point to existing records."""
    record_id = record.get("id", "unknown")
    refs = record.get(ref_field, [])
    if isinstance(refs, list):
        for ref in refs:
            if ref not in target_ids:
                result.error(f"[{source_family}] {record_id}: Invalid {ref_field} '{ref}' (not found in {target_family})")
    elif refs and refs not in target_ids:
        result.error(f"[{source_family}] {record_id}: Invalid {ref_field} '{refs}' (not found in {target_family})")


def validate_status(result: ValidationResult, family: str, record: Dict, valid_statuses: List[str]) -> None:
    """Validate status field has valid value."""
    record_id = record.get("id", "unknown")
    status = record.get("status")
    if status and status not in valid_statuses:
        result.error(f"[{family}] {record_id}: Invalid status '{status}'. Must be one of {valid_statuses}")


# =============================================================================
# Family-Specific Validators
# =============================================================================

def validate_releases(result: ValidationResult, releases: List[Dict]) -> None:
    """Validate releases.json."""
    validate_id_format(result, "releases", releases)
    validate_id_uniqueness(result, "releases", releases)

    for release in releases:
        validate_required_fields(result, "releases", release, ["id", "status", "release_date", "description"])
        validate_status(result, "releases", release, ["planned", "released", "superseded"])


def validate_domain(result: ValidationResult, domain: List[Dict]) -> None:
    """Validate domain.json."""
    validate_id_format(result, "domain", domain)
    validate_id_uniqueness(result, "domain", domain)

    for entry in domain:
        validate_required_fields(result, "domain", entry, ["id", "title", "status", "type", "source", "doc_path"])
        validate_status(result, "domain", entry, ["active", "deprecated"])

        entry_type = entry.get("type")
        if entry_type and entry_type not in ["policy", "catalog", "classification", "rule"]:
            result.error(f"[domain] {entry.get('id')}: Invalid type '{entry_type}'")


def validate_domain_doc_paths(result: ValidationResult, domain: List[Dict]) -> None:
    """Warn if domain doc_path points to non-existent file."""
    for entry in domain:
        if entry.get("status") == "deprecated":
            continue
        doc_path = entry.get("doc_path")
        if doc_path:
            full_path = ROOT_DIR / doc_path
            if not full_path.exists():
                result.warning(f"[domain] {entry.get('id')}: doc_path '{doc_path}' does not exist")


def validate_requirements(result: ValidationResult, requirements: List[Dict], domain_ids: Set[str]) -> None:
    """Validate requirements.json."""
    validate_id_format(result, "requirements", requirements)
    validate_id_uniqueness(result, "requirements", requirements)

    req_ids = build_id_set(requirements)

    for req in requirements:
        validate_required_fields(result, "requirements", req, ["id", "title", "status", "type", "statement", "rationale"])
        validate_status(result, "requirements", req, ["active", "deprecated"])
        validate_refs(result, "requirements", req, "domain_refs", domain_ids, "domain")

        req_type = req.get("type")
        if req_type and req_type not in ["functional", "non-functional"]:
            result.error(f"[requirements] {req.get('id')}: Invalid type '{req_type}'")

        # Validate superseded_by reference
        superseded_by = req.get("superseded_by")
        if superseded_by and superseded_by not in req_ids:
            result.error(f"[requirements] {req.get('id')}: Invalid superseded_by '{superseded_by}'")


def validate_features(result: ValidationResult, features: List[Dict],
                      requirement_ids: Set[str], domain_ids: Set[str]) -> None:
    """Validate features.json."""
    validate_id_format(result, "features", features)
    validate_id_uniqueness(result, "features", features)

    for feat in features:
        validate_required_fields(result, "features", feat, ["id", "title", "status", "purpose", "business_value"])
        validate_status(result, "features", feat, ["active", "deprecated"])
        validate_refs(result, "features", feat, "requirement_refs", requirement_ids, "requirements")
        validate_refs(result, "features", feat, "domain_refs", domain_ids, "domain")


def validate_epics(result: ValidationResult, epics: List[Dict],
                   feature_ids: Set[str], release_ids: Set[str],
                   releases: List[Dict], requirement_ids: Set[str], domain_ids: Set[str]) -> None:
    """Validate epics.json."""
    validate_id_format(result, "epics", epics)
    validate_id_uniqueness(result, "epics", epics)

    # Build release status lookup
    release_status = {r.get("id"): r.get("status") for r in releases}

    for epic in epics:
        epic_id = epic.get("id", "unknown")
        validate_required_fields(result, "epics", epic, ["id", "title", "feature_ref", "versions"])

        # Validate feature_ref
        feature_ref = epic.get("feature_ref")
        if feature_ref and feature_ref not in feature_ids:
            result.error(f"[epics] {epic_id}: Invalid feature_ref '{feature_ref}'")

        # Validate versions
        versions = epic.get("versions", [])
        if not versions:
            result.error(f"[epics] {epic_id}: Must have at least one version")

        version_nums = []
        for version in versions:
            v_num = version.get("version")
            if v_num is None:
                result.error(f"[epics] {epic_id}: Version missing 'version' field")
            else:
                version_nums.append(v_num)

            # Validate version status
            v_status = version.get("status")
            if v_status and v_status not in ["draft", "approved", "superseded"]:
                result.error(f"[epics] {epic_id} v{v_num}: Invalid status '{v_status}'")

            # Validate release_ref
            release_ref = version.get("release_ref")
            if not release_ref:
                result.error(f"[epics] {epic_id} v{v_num}: Missing required release_ref")
            elif release_ref not in release_ids:
                result.error(f"[epics] {epic_id} v{v_num}: Invalid release_ref '{release_ref}'")

            # Validate refs
            validate_refs(result, f"epics/{epic_id}/v{v_num}", version, "requirement_refs", requirement_ids, "requirements")
            validate_refs(result, f"epics/{epic_id}/v{v_num}", version, "domain_refs", domain_ids, "domain")

            # Validate supersedes
            supersedes = version.get("supersedes")
            if supersedes is not None and supersedes not in version_nums and supersedes >= v_num:
                result.error(f"[epics] {epic_id} v{v_num}: Invalid supersedes '{supersedes}'")

        # Validate version lineage is monotonic
        if version_nums:
            for i, v in enumerate(sorted(version_nums)):
                if v != i + 1:
                    result.error(f"[epics] {epic_id}: Version numbers not monotonic (expected {i + 1}, found {v})")
                    break


def validate_stories(result: ValidationResult, stories: List[Dict],
                     epic_ids: Set[str], release_ids: Set[str],
                     releases: List[Dict], requirement_ids: Set[str], domain_ids: Set[str]) -> None:
    """Validate stories.json."""
    validate_id_format(result, "stories", stories)
    validate_id_uniqueness(result, "stories", stories)

    # Build release status lookup
    release_status = {r.get("id"): r.get("status") for r in releases}

    for story in stories:
        story_id = story.get("id", "unknown")
        validate_required_fields(result, "stories", story, ["id", "title", "epic_ref", "versions"])

        # Validate epic_ref
        epic_ref = story.get("epic_ref")
        if epic_ref and epic_ref not in epic_ids:
            result.error(f"[stories] {story_id}: Invalid epic_ref '{epic_ref}'")

        # Validate versions
        versions = story.get("versions", [])
        if not versions:
            result.error(f"[stories] {story_id}: Must have at least one version")

        version_nums = []
        for version in versions:
            v_num = version.get("version")
            if v_num is None:
                result.error(f"[stories] {story_id}: Version missing 'version' field")
            else:
                version_nums.append(v_num)

            # Validate version status
            v_status = version.get("status")
            valid_story_statuses = ["draft", "ready_to_build", "in_build", "built", "superseded"]
            if v_status and v_status not in valid_story_statuses:
                result.error(f"[stories] {story_id} v{v_num}: Invalid status '{v_status}'")

            # Validate release_ref
            release_ref = version.get("release_ref")
            if not release_ref:
                result.error(f"[stories] {story_id} v{v_num}: Missing required release_ref")
            elif release_ref not in release_ids:
                result.error(f"[stories] {story_id} v{v_num}: Invalid release_ref '{release_ref}'")

            # Validate refs
            validate_refs(result, f"stories/{story_id}/v{v_num}", version, "requirement_refs", requirement_ids, "requirements")
            validate_refs(result, f"stories/{story_id}/v{v_num}", version, "domain_refs", domain_ids, "domain")

            # Validate completeness for non-draft statuses
            if v_status in ("ready_to_build", "in_build", "built"):
                ac = version.get("acceptance_criteria", [])
                if not ac:
                    result.error(f"[stories] {story_id} v{v_num}: Status '{v_status}' requires acceptance_criteria")

                ti = version.get("test_intent", {})
                has_test_intent = ti.get("failure_modes") or ti.get("guarantees")
                if not has_test_intent:
                    result.error(f"[stories] {story_id} v{v_num}: Status '{v_status}' requires test_intent with failure_modes or guarantees")

            # Validate supersedes
            supersedes = version.get("supersedes")
            if supersedes is not None and supersedes not in version_nums and supersedes >= v_num:
                result.error(f"[stories] {story_id} v{v_num}: Invalid supersedes '{supersedes}'")

        # Validate version lineage is monotonic
        if version_nums:
            for i, v in enumerate(sorted(version_nums)):
                if v != i + 1:
                    result.error(f"[stories] {story_id}: Version numbers not monotonic (expected {i + 1}, found {v})")
                    break


def validate_deprecated_refs(result: ValidationResult, stories: List[Dict], epics: List[Dict],
                             features: List[Dict], requirements: List[Dict], domain: List[Dict]) -> None:
    """Warn if current versions reference deprecated upstream artifacts."""
    # Build deprecated ID sets
    deprecated_reqs = {r.get("id") for r in requirements if r.get("status") == "deprecated"}
    deprecated_domain = {d.get("id") for d in domain if d.get("status") == "deprecated"}
    deprecated_features = {f.get("id") for f in features if f.get("status") == "deprecated"}

    # Check epics
    for epic in epics:
        epic_id = epic.get("id")
        feature_ref = epic.get("feature_ref")
        if feature_ref in deprecated_features:
            result.warning(f"[epics] {epic_id}: References deprecated feature '{feature_ref}'")

        # Check latest version
        versions = epic.get("versions", [])
        if versions:
            latest = max(versions, key=lambda v: v.get("version", 0))
            if latest.get("status") != "superseded":
                for ref in latest.get("requirement_refs", []):
                    if ref in deprecated_reqs:
                        result.warning(f"[epics] {epic_id} v{latest.get('version')}: References deprecated requirement '{ref}'")
                for ref in latest.get("domain_refs", []):
                    if ref in deprecated_domain:
                        result.warning(f"[epics] {epic_id} v{latest.get('version')}: References deprecated domain '{ref}'")

    # Check stories
    for story in stories:
        story_id = story.get("id")
        versions = story.get("versions", [])
        if versions:
            latest = max(versions, key=lambda v: v.get("version", 0))
            if latest.get("status") != "superseded":
                for ref in latest.get("requirement_refs", []):
                    if ref in deprecated_reqs:
                        result.warning(f"[stories] {story_id} v{latest.get('version')}: References deprecated requirement '{ref}'")
                for ref in latest.get("domain_refs", []):
                    if ref in deprecated_domain:
                        result.warning(f"[stories] {story_id} v{latest.get('version')}: References deprecated domain '{ref}'")


# =============================================================================
# Main Validation
# =============================================================================

def run_validation(include_warnings: bool = False) -> ValidationResult:
    """Run all validations and return result."""
    result = ValidationResult()

    # Load all data
    try:
        releases = load_json(DATA_FILES["releases"])
        domain = load_json(DATA_FILES["domain"])
        requirements = load_json(DATA_FILES["requirements"])
        features = load_json(DATA_FILES["features"])
        epics = load_json(DATA_FILES["epics"])
        stories = load_json(DATA_FILES["stories"])
    except json.JSONDecodeError as e:
        result.error(f"JSON parse error: {e}")
        return result

    # Build ID sets for cross-reference validation
    release_ids = build_id_set(releases)
    domain_ids = build_id_set(domain)
    requirement_ids = build_id_set(requirements)
    feature_ids = build_id_set(features)
    epic_ids = build_id_set(epics)

    # Run validations
    validate_releases(result, releases)
    validate_domain(result, domain)
    validate_requirements(result, requirements, domain_ids)
    validate_features(result, features, requirement_ids, domain_ids)
    validate_epics(result, epics, feature_ids, release_ids, releases, requirement_ids, domain_ids)
    validate_stories(result, stories, epic_ids, release_ids, releases, requirement_ids, domain_ids)

    # Optional warnings
    if include_warnings:
        validate_domain_doc_paths(result, domain)
        validate_deprecated_refs(result, stories, epics, features, requirements, domain)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate APSCA canonical JSON files"
    )
    parser.add_argument(
        "--warnings", "-w",
        action="store_true",
        help="Include optional warnings (deprecated refs, missing doc files)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    result = run_validation(include_warnings=args.warnings)

    if args.json:
        output = {
            "valid": result.is_valid(),
            "errors": result.errors,
            "warnings": result.warnings if args.warnings else [],
            "error_count": len(result.errors),
            "warning_count": len(result.warnings) if args.warnings else 0,
        }
        print(json.dumps(output, indent=2))
    else:
        if result.errors:
            print("ERRORS:")
            for error in result.errors:
                print(f"  {error}")
            print()

        if args.warnings and result.warnings:
            print("WARNINGS:")
            for warning in result.warnings:
                print(f"  {warning}")
            print()

        if result.is_valid():
            print("Validation PASSED")
            if args.warnings and result.warnings:
                print(f"  ({len(result.warnings)} warning(s))")
        else:
            print(f"Validation FAILED ({len(result.errors)} error(s))")

    sys.exit(0 if result.is_valid() else 1)


if __name__ == "__main__":
    main()
