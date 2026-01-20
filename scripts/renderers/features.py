"""Render feature pages."""

from typing import Dict, List, Optional

from lib.html_helpers import (
    build_artifact_rows,
    build_epic_rows,
    build_requirement_rows,
    build_story_rows,
    e,
    html_page,
    render_connected_table,
    render_tabs,
    slugify,
    status_badge,
)


def render_feature(
    feat: Dict,
    epics: List[Dict],
    stories: List[Dict],
    requirement_lookup: Optional[Dict[str, Dict]] = None,
    artifact_lookup: Optional[Dict[str, Dict]] = None,
) -> str:
    """Render a feature as HTML."""
    html = f"""
<h1>{e(feat['id'])}: {e(feat.get('title', ''))}</h1>
<div class="meta">
    <strong>Status:</strong> {status_badge(feat.get('status', 'unknown'))}
</div>
<div class="section">
    <h2>Purpose</h2>
    <p>{e(feat.get('purpose', 'No purpose defined'))}</p>
</div>
<div class="section">
    <h2>Business Value</h2>
    <p>{e(feat.get('business_value', 'No business value defined'))}</p>
</div>
"""
    if feat.get('in_scope'):
        html += '<div class="section"><h2>In Scope</h2><ul>'
        for item in feat['in_scope']:
            html += f'<li>{e(item)}</li>'
        html += '</ul></div>'

    if feat.get('out_of_scope'):
        html += '<div class="section"><h2>Out of Scope</h2><ul>'
        for item in feat['out_of_scope']:
            html += f'<li>{e(item)}</li>'
        html += '</ul></div>'

    feature_epics = [epic for epic in epics if epic.get("feature_ref") == feat.get("id")]
    epic_rows = build_epic_rows(feature_epics, "../epics/", "../releases/")

    epic_ids = {epic.get("id") for epic in feature_epics if epic.get("id")}
    feature_stories = [story for story in stories if story.get("epic_ref") in epic_ids]
    story_rows = build_story_rows(feature_stories, "../stories/", "../releases/")

    requirement_rows = build_requirement_rows(
        feat.get("requirement_refs", []),
        requirement_lookup or {},
        "../requirements/",
    )

    artifact_rows = build_artifact_rows(
        feat.get("artifact_refs", []),
        artifact_lookup or {},
        "../artifacts/",
    )

    tabs = [
        {
            "id": slugify("Epics"),
            "label": "Epics",
            "content": render_connected_table(["Record", "Summary", "Release"], epic_rows, "Epics"),
        },
        {
            "id": slugify("Stories"),
            "label": "Stories",
            "content": render_connected_table(["Record", "Summary", "Release"], story_rows, "Stories"),
        },
        {
            "id": slugify("Requirements"),
            "label": "Requirements",
            "content": render_connected_table(["Record", "Statement"], requirement_rows, "Requirements"),
        },
        {
            "id": slugify("Business Artifacts"),
            "label": "Business Artifacts",
            "content": render_connected_table(["Record", "Description", "Type"], artifact_rows, "Business Artifacts"),
        },
    ]

    html += f"""
<div class="section">
    <h2>Connected Records</h2>
    {render_tabs("feature-connections", tabs)}
</div>
"""
    return html_page(f"{feat['id']}: {feat.get('title', '')}", html, "features", depth=1)
