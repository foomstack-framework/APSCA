#!/usr/bin/env python3
"""
render_docs.py - Generate static HTML documentation for APSCA requirements repository.

Generates HTML files in docs/ from canonical JSON data.
Note: docs/artifacts/ contains authored content and is NOT overwritten.

Usage:
    python scripts/render_docs.py
"""

import shutil
from pathlib import Path

from lib.config import DATA_FILES, DATA_DIR, DOCS_DIR, REPORTS_DIR, ROOT_DIR
from lib.io import load_json
from renderers.artifacts import render_artifact_entry
from renderers.epics import render_epic
from renderers.features import render_feature
from renderers.index_pages import render_artifacts_index, render_index, render_index_redirect
from renderers.releases import render_release
from renderers.requirements import render_requirement
from renderers.stories import render_story
from renderers.story_map import render_story_map

# Output directories (script-specific, NOT artifacts/ - that's authored content)
OUTPUT_DIRS = {
    "releases": DOCS_DIR / "releases",
    "requirements": DOCS_DIR / "requirements",
    "features": DOCS_DIR / "features",
    "epics": DOCS_DIR / "epics",
    "stories": DOCS_DIR / "stories",
}


# =============================================================================
# Main
# =============================================================================


def main():
    # Load all data
    releases = load_json(DATA_FILES["releases"])
    artifacts = load_json(DATA_FILES["artifacts"])
    requirements = load_json(DATA_FILES["requirements"])
    features = load_json(DATA_FILES["features"])
    epics = load_json(DATA_FILES["epics"])
    stories = load_json(DATA_FILES["stories"])

    # Build lookup tables
    artifact_lookup = {artifact['id']: artifact for artifact in artifacts}
    requirement_lookup = {r['id']: r for r in requirements}

    # Ensure output directories exist
    for output_dir in OUTPUT_DIRS.values():
        output_dir.mkdir(parents=True, exist_ok=True)

    counts = {"releases": 0, "artifacts": 0, "requirements": 0, "features": 0, "epics": 0, "stories": 0}

    # Render business artifacts and index
    artifacts_dir = DOCS_DIR / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for entry in artifacts:
        content = render_artifact_entry(
            entry,
            features,
            epics,
            stories,
            requirements,
            requirement_lookup=requirement_lookup,
        )
        (artifacts_dir / f"{entry['id']}.html").write_text(content, encoding="utf-8")
        counts["artifacts"] += 1
    artifacts_index = render_artifacts_index(artifacts)
    (artifacts_dir / "index.html").write_text(artifacts_index, encoding="utf-8")

    # Render releases
    releases_sorted = sorted(
        releases,
        key=lambda r: ((r.get("release_date") or ""), (r.get("id") or "")),
        reverse=True,
    )
    release_items = releases_sorted
    for release in release_items:
        content = render_release(release, epics, stories)
        (OUTPUT_DIRS["releases"] / f"{release['id']}.html").write_text(content, encoding="utf-8")
        counts["releases"] += 1

    index_content = render_index("releases", release_items, "Releases")
    (OUTPUT_DIRS["releases"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render requirements
    for req in requirements:
        content = render_requirement(
            req,
            features,
            epics,
            stories,
            artifact_lookup=artifact_lookup,
        )
        (OUTPUT_DIRS["requirements"] / f"{req['id']}.html").write_text(content, encoding="utf-8")
        counts["requirements"] += 1

    index_content = render_index("requirements", requirements, "Requirements", artifact_lookup=artifact_lookup)
    (OUTPUT_DIRS["requirements"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render features
    for feat in features:
        content = render_feature(
            feat,
            epics,
            stories,
            requirement_lookup=requirement_lookup,
            artifact_lookup=artifact_lookup,
        )
        (OUTPUT_DIRS["features"] / f"{feat['id']}.html").write_text(content, encoding="utf-8")
        counts["features"] += 1

    index_content = render_index("features", features, "Features")
    (OUTPUT_DIRS["features"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render epics
    for epic in epics:
        content = render_epic(
            epic,
            stories,
            requirement_lookup=requirement_lookup,
            artifact_lookup=artifact_lookup,
        )
        (OUTPUT_DIRS["epics"] / f"{epic['id']}.html").write_text(content, encoding="utf-8")
        counts["epics"] += 1

    index_content = render_index("epics", epics, "Epics")
    (OUTPUT_DIRS["epics"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render stories
    for story in stories:
        content = render_story(
            story,
            epics,
            features,
            requirement_lookup=requirement_lookup,
            artifact_lookup=artifact_lookup,
        )
        (OUTPUT_DIRS["stories"] / f"{story['id']}.html").write_text(content, encoding="utf-8")
        counts["stories"] += 1

    epic_lookup = {ep['id']: ep for ep in epics}
    index_content = render_index("stories", stories, "Stories", epic_lookup=epic_lookup)
    (OUTPUT_DIRS["stories"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render index.html as redirect to Story Map
    index_redirect = render_index_redirect()
    (DOCS_DIR / "index.html").write_text(index_redirect, encoding="utf-8")

    # Render story-map.html from template
    story_map_content = render_story_map()
    (DOCS_DIR / "story-map.html").write_text(story_map_content, encoding="utf-8")

    # Copy data and reports to docs for local testing and story map access
    docs_data = DOCS_DIR / "data"
    docs_reports = DOCS_DIR / "reports"
    docs_data.mkdir(exist_ok=True)
    docs_reports.mkdir(exist_ok=True)

    for json_file in DATA_DIR.glob("*.json"):
        shutil.copy(json_file, docs_data / json_file.name)

    for json_file in REPORTS_DIR.glob("*.json"):
        shutil.copy(json_file, docs_reports / json_file.name)

    images_dir = ROOT_DIR / "images"
    docs_images = DOCS_DIR / "images"
    if images_dir.exists():
        docs_images.mkdir(exist_ok=True)
        for image_file in images_dir.iterdir():
            if image_file.is_file():
                shutil.copy(image_file, docs_images / image_file.name)

    print("Documentation generated:")
    for key, count in counts.items():
        print(f"  {key}: {count} files")
    print(f"  Index redirect: index.html -> story-map.html")


if __name__ == "__main__":
    main()
