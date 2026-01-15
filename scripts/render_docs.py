#!/usr/bin/env python3
"""
render_docs.py - Generate GitHub Pages documentation for APSCA requirements repository.

Generates Markdown files in docs/ from canonical JSON data.
Note: docs/domain/ contains authored content and is NOT overwritten.

Usage:
    python scripts/render_docs.py
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# Output directories (NOT domain/ - that's authored content)
OUTPUT_DIRS = {
    "releases": DOCS_DIR / "releases",
    "requirements": DOCS_DIR / "requirements",
    "features": DOCS_DIR / "features",
    "epics": DOCS_DIR / "epics",
    "stories": DOCS_DIR / "stories",
}


def load_json(file_path: Path) -> List[Dict]:
    """Load JSON array from file."""
    if not file_path.exists():
        return []
    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return json.loads(content)


def get_current_version(versions: List[Dict]) -> Optional[Dict]:
    """Get the current (non-superseded) version from a versions list."""
    if not versions:
        return None
    active_versions = [v for v in versions if v.get("status") != "superseded"]
    if active_versions:
        return max(active_versions, key=lambda v: v.get("version", 0))
    return max(versions, key=lambda v: v.get("version", 0))


def format_refs(refs: List[str], prefix: str = "") -> str:
    """Format a list of references as Markdown links."""
    if not refs:
        return "_None_"
    # Use Jekyll link syntax for internal references
    return ", ".join(f"[{ref}]({{% link {prefix}{ref}.md %}})" for ref in refs)


def format_status_badge(status: str) -> str:
    """Format status as a badge-style indicator."""
    badges = {
        "planned": "**[Planned]**",
        "released": "**[Released]**",
        "superseded": "~~[Superseded]~~",
        "active": "**[Active]**",
        "deprecated": "~~[Deprecated]~~",
        "draft": "_[Draft]_",
        "approved": "**[Approved]**",
        "ready_to_build": "**[Ready to Build]**",
        "in_build": "**[In Build]**",
        "built": "**[Built]**",
    }
    return badges.get(status, f"[{status}]")


# =============================================================================
# Render Functions
# =============================================================================

def render_release(release: Dict) -> str:
    """Render a release as Markdown."""
    lines = [
        "---",
        f"title: \"{release.get('title', release['id'])}\"",
        f"layout: default",
        f"parent: Releases",
        "---",
        "",
        f"# {release['id']}",
        "",
        f"**Status:** {format_status_badge(release.get('status', 'unknown'))}",
        "",
        f"**Release Date:** {release.get('release_date', 'TBD')}",
        "",
    ]

    if release.get('git_tag'):
        lines.append(f"**Git Tag:** `{release['git_tag']}`")
        lines.append("")

    lines.append("## Description")
    lines.append("")
    lines.append(release.get('description', '_No description_'))
    lines.append("")

    if release.get('notes'):
        lines.append("## Notes")
        lines.append("")
        lines.append(release['notes'])
        lines.append("")

    if release.get('tags'):
        lines.append(f"**Tags:** {', '.join(release['tags'])}")
        lines.append("")

    return "\n".join(lines)


def render_requirement(req: Dict) -> str:
    """Render a requirement as Markdown."""
    lines = [
        "---",
        f"title: \"{req.get('title', req['id'])}\"",
        f"layout: default",
        f"parent: Requirements",
        "---",
        "",
        f"# {req['id']}: {req.get('title', '')}",
        "",
        f"**Status:** {format_status_badge(req.get('status', 'unknown'))}",
        f"**Type:** {req.get('type', 'unknown')}",
    ]

    if req.get('invariant'):
        lines.append("**Invariant:** Yes (non-negotiable)")

    lines.extend(["", "## Statement", "", req.get('statement', '_No statement_'), ""])
    lines.extend(["## Rationale", "", req.get('rationale', '_No rationale_'), ""])

    if req.get('domain_refs'):
        lines.append("## Domain References")
        lines.append("")
        lines.append(format_refs(req['domain_refs'], "domain/"))
        lines.append("")

    if req.get('superseded_by'):
        lines.append(f"**Superseded By:** [{req['superseded_by']}]({{% link requirements/{req['superseded_by']}.md %}})")
        lines.append("")

    if req.get('notes'):
        lines.append("## Notes")
        lines.append("")
        lines.append(req['notes'])
        lines.append("")

    return "\n".join(lines)


def render_feature(feat: Dict) -> str:
    """Render a feature as Markdown."""
    lines = [
        "---",
        f"title: \"{feat.get('title', feat['id'])}\"",
        f"layout: default",
        f"parent: Features",
        "---",
        "",
        f"# {feat['id']}: {feat.get('title', '')}",
        "",
        f"**Status:** {format_status_badge(feat.get('status', 'unknown'))}",
        "",
        "## Purpose",
        "",
        feat.get('purpose', '_No purpose defined_'),
        "",
        "## Business Value",
        "",
        feat.get('business_value', '_No business value defined_'),
        "",
    ]

    if feat.get('in_scope'):
        lines.append("## In Scope")
        lines.append("")
        for item in feat['in_scope']:
            lines.append(f"- {item}")
        lines.append("")

    if feat.get('out_of_scope'):
        lines.append("## Out of Scope")
        lines.append("")
        for item in feat['out_of_scope']:
            lines.append(f"- {item}")
        lines.append("")

    if feat.get('requirement_refs'):
        lines.append("## Requirements")
        lines.append("")
        lines.append(format_refs(feat['requirement_refs'], "requirements/"))
        lines.append("")

    if feat.get('domain_refs'):
        lines.append("## Domain References")
        lines.append("")
        lines.append(format_refs(feat['domain_refs'], "domain/"))
        lines.append("")

    return "\n".join(lines)


def render_epic(epic: Dict) -> str:
    """Render an epic as Markdown."""
    current = get_current_version(epic.get('versions', []))

    lines = [
        "---",
        f"title: \"{epic.get('title', epic['id'])}\"",
        f"layout: default",
        f"parent: Epics",
        "---",
        "",
        f"# {epic['id']}: {epic.get('title', '')}",
        "",
    ]

    if current:
        lines.append(f"**Current Version:** {current.get('version')} {format_status_badge(current.get('status', 'unknown'))}")
        lines.append("")
        lines.append(f"**Release:** [{current.get('release_ref')}]({{% link releases/{current.get('release_ref')}.md %}})")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(current.get('summary', '_No summary_'))
        lines.append("")

        if current.get('assumptions'):
            lines.append("## Assumptions")
            lines.append("")
            for item in current['assumptions']:
                lines.append(f"- {item}")
            lines.append("")

        if current.get('constraints'):
            lines.append("## Constraints")
            lines.append("")
            for item in current['constraints']:
                lines.append(f"- {item}")
            lines.append("")

        if current.get('requirement_refs'):
            lines.append("## Requirements")
            lines.append("")
            lines.append(format_refs(current['requirement_refs'], "requirements/"))
            lines.append("")

        if current.get('domain_refs'):
            lines.append("## Domain References")
            lines.append("")
            lines.append(format_refs(current['domain_refs'], "domain/"))
            lines.append("")

    # Feature reference
    if epic.get('feature_ref'):
        lines.append("## Feature")
        lines.append("")
        lines.append(f"Part of [{epic['feature_ref']}]({{% link features/{epic['feature_ref']}.md %}})")
        lines.append("")

    # Version history
    versions = epic.get('versions', [])
    if len(versions) > 1:
        lines.append("## Version History")
        lines.append("")
        lines.append("| Version | Status | Release |")
        lines.append("|---------|--------|---------|")
        for v in sorted(versions, key=lambda x: x.get('version', 0), reverse=True):
            lines.append(f"| {v.get('version')} | {v.get('status')} | {v.get('release_ref')} |")
        lines.append("")

    return "\n".join(lines)


def render_story(story: Dict) -> str:
    """Render a story as Markdown."""
    current = get_current_version(story.get('versions', []))

    lines = [
        "---",
        f"title: \"{story.get('title', story['id'])}\"",
        f"layout: default",
        f"parent: Stories",
        "---",
        "",
        f"# {story['id']}: {story.get('title', '')}",
        "",
    ]

    if current:
        lines.append(f"**Current Version:** {current.get('version')} {format_status_badge(current.get('status', 'unknown'))}")
        lines.append("")
        lines.append(f"**Release:** [{current.get('release_ref')}]({{% link releases/{current.get('release_ref')}.md %}})")
        lines.append("")
        lines.append("## Description")
        lines.append("")
        lines.append(current.get('description', '_No description_'))
        lines.append("")

        # Acceptance Criteria
        ac = current.get('acceptance_criteria', [])
        if ac:
            lines.append("## Acceptance Criteria")
            lines.append("")
            for criterion in ac:
                lines.append(f"- **{criterion.get('id', 'AC')}:** {criterion.get('statement', '')}")
                if criterion.get('notes'):
                    lines.append(f"  - _Note: {criterion['notes']}_")
            lines.append("")

        # Test Intent
        ti = current.get('test_intent', {})
        if ti.get('failure_modes') or ti.get('guarantees'):
            lines.append("## Test Intent")
            lines.append("")
            if ti.get('failure_modes'):
                lines.append("### Failure Modes (must not happen)")
                lines.append("")
                for item in ti['failure_modes']:
                    lines.append(f"- {item}")
                lines.append("")
            if ti.get('guarantees'):
                lines.append("### Guarantees (must always be true)")
                lines.append("")
                for item in ti['guarantees']:
                    lines.append(f"- {item}")
                lines.append("")
            if ti.get('exclusions'):
                lines.append("### Exclusions (not tested)")
                lines.append("")
                for item in ti['exclusions']:
                    lines.append(f"- {item}")
                lines.append("")

        if current.get('requirement_refs'):
            lines.append("## Requirements")
            lines.append("")
            lines.append(format_refs(current['requirement_refs'], "requirements/"))
            lines.append("")

        if current.get('domain_refs'):
            lines.append("## Domain References")
            lines.append("")
            lines.append(format_refs(current['domain_refs'], "domain/"))
            lines.append("")

    # Epic reference
    if story.get('epic_ref'):
        lines.append("## Epic")
        lines.append("")
        lines.append(f"Part of [{story['epic_ref']}]({{% link epics/{story['epic_ref']}.md %}})")
        lines.append("")

    # Version history
    versions = story.get('versions', [])
    if len(versions) > 1:
        lines.append("## Version History")
        lines.append("")
        lines.append("| Version | Status | Release |")
        lines.append("|---------|--------|---------|")
        for v in sorted(versions, key=lambda x: x.get('version', 0), reverse=True):
            lines.append(f"| {v.get('version')} | {v.get('status')} | {v.get('release_ref')} |")
        lines.append("")

    return "\n".join(lines)


def render_index(artifact_type: str, items: List[Dict], title: str) -> str:
    """Render an index page for a collection."""
    lines = [
        "---",
        f"title: \"{title}\"",
        f"layout: default",
        "has_children: true",
        "nav_order: 2",
        "---",
        "",
        f"# {title}",
        "",
    ]

    if not items:
        lines.append("_No items yet._")
        return "\n".join(lines)

    # Group by status for better organization
    by_status: Dict[str, List[Dict]] = {}
    for item in items:
        status = item.get('status', 'unknown')
        # For versioned items, get current version status
        if 'versions' in item:
            current = get_current_version(item.get('versions', []))
            status = current.get('status', 'unknown') if current else 'unknown'
        by_status.setdefault(status, []).append(item)

    # Render table
    lines.append("| ID | Title | Status |")
    lines.append("|----|-------|--------|")

    for item in sorted(items, key=lambda x: x.get('id', '')):
        item_id = item['id']
        title = item.get('title', item_id)
        status = item.get('status', 'unknown')
        if 'versions' in item:
            current = get_current_version(item.get('versions', []))
            status = current.get('status', 'unknown') if current else 'unknown'

        folder = artifact_type.lower()
        lines.append(f"| [{item_id}]({{% link {folder}/{item_id}.md %}}) | {title} | {status} |")

    lines.append("")

    return "\n".join(lines)


def main():
    # Load all data
    releases = load_json(DATA_FILES["releases"])
    requirements = load_json(DATA_FILES["requirements"])
    features = load_json(DATA_FILES["features"])
    epics = load_json(DATA_FILES["epics"])
    stories = load_json(DATA_FILES["stories"])

    # Ensure output directories exist
    for output_dir in OUTPUT_DIRS.values():
        output_dir.mkdir(parents=True, exist_ok=True)

    counts = {"releases": 0, "requirements": 0, "features": 0, "epics": 0, "stories": 0}

    # Render releases
    for release in releases:
        content = render_release(release)
        (OUTPUT_DIRS["releases"] / f"{release['id']}.md").write_text(content, encoding="utf-8")
        counts["releases"] += 1

    # Render index for releases
    index_content = render_index("releases", releases, "Releases")
    (OUTPUT_DIRS["releases"] / "index.md").write_text(index_content, encoding="utf-8")

    # Render requirements
    for req in requirements:
        content = render_requirement(req)
        (OUTPUT_DIRS["requirements"] / f"{req['id']}.md").write_text(content, encoding="utf-8")
        counts["requirements"] += 1

    index_content = render_index("requirements", requirements, "Requirements")
    (OUTPUT_DIRS["requirements"] / "index.md").write_text(index_content, encoding="utf-8")

    # Render features
    for feat in features:
        content = render_feature(feat)
        (OUTPUT_DIRS["features"] / f"{feat['id']}.md").write_text(content, encoding="utf-8")
        counts["features"] += 1

    index_content = render_index("features", features, "Features")
    (OUTPUT_DIRS["features"] / "index.md").write_text(index_content, encoding="utf-8")

    # Render epics
    for epic in epics:
        content = render_epic(epic)
        (OUTPUT_DIRS["epics"] / f"{epic['id']}.md").write_text(content, encoding="utf-8")
        counts["epics"] += 1

    index_content = render_index("epics", epics, "Epics")
    (OUTPUT_DIRS["epics"] / "index.md").write_text(index_content, encoding="utf-8")

    # Render stories
    for story in stories:
        content = render_story(story)
        (OUTPUT_DIRS["stories"] / f"{story['id']}.md").write_text(content, encoding="utf-8")
        counts["stories"] += 1

    index_content = render_index("stories", stories, "Stories")
    (OUTPUT_DIRS["stories"] / "index.md").write_text(index_content, encoding="utf-8")

    print("Documentation generated:")
    for key, count in counts.items():
        print(f"  {key}: {count} files")


if __name__ == "__main__":
    main()
