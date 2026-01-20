"""Render artifact pages."""

from typing import Dict, List, Optional

from lib.html_helpers import (
    build_epic_rows,
    build_feature_rows,
    build_requirement_rows,
    build_story_rows,
    e,
    format_status_label,
    html_page,
    render_connected_table,
    render_tabs,
    slugify,
    status_badge,
)
from lib.versions import get_current_version


def render_artifact_entry(
    entry: Dict,
    features: List[Dict],
    epics: List[Dict],
    stories: List[Dict],
    requirements: List[Dict],
    requirement_lookup: Optional[Dict[str, Dict]] = None,
) -> str:
    """Render a single business artifact entry as HTML."""
    artifact_type = entry.get("type", "unknown")
    if isinstance(artifact_type, list):
        artifact_type = artifact_type[0] if artifact_type else "unknown"
    type_colors = {
        "policy": "#3b82f6",
        "catalog": "#10b981",
        "classification": "#8b5cf6",
        "rule": "#f59e0b",
    }
    type_color = type_colors.get(artifact_type, "#6b7280")

    html = f"""
<h1>{e(entry['id'])}: {e(entry.get('title', ''))}</h1>
<div class="meta">
    <strong>Type:</strong> <span class="status-badge" style="background-color: {type_color}">{e(format_status_label(artifact_type))}</span> &nbsp;
    {status_badge(entry.get('status', 'unknown'))} &nbsp;
    <strong>Source:</strong> {e(entry.get('source', 'unknown'))}
    {f' &nbsp; <strong>Effective:</strong> {e(entry.get("effective_date"))}' if entry.get('effective_date') else ''}
</div>
<div class="section">
    <h2>Description</h2>
    <p>{e(entry.get('description', 'No description provided.'))}</p>
</div>
"""
    if entry.get("anchors"):
        html += '<div class="section"><h2>Anchors</h2><ul>'
        for anchor in entry["anchors"]:
            html += f"<li>{e(anchor)}</li>"
        html += "</ul></div>"

    if entry.get("notes"):
        html += f'<div class="section"><h2>Notes</h2><p>{e(entry["notes"])}</p></div>'

    if entry.get("tags"):
        html += f'<p><strong>Tags:</strong> {", ".join(e(t) for t in entry["tags"])}</p>'

    artifact_id = entry.get("id")
    feature_rows = build_feature_rows(
        [feat for feat in features if artifact_id in (feat.get("artifact_refs") or [])],
        "../features/",
    )
    epic_rows = build_epic_rows(
        [
            epic
            for epic in epics
            if artifact_id in ((get_current_version(epic.get("versions", [])) or {}).get("artifact_refs", []))
        ],
        "../epics/",
        "../releases/",
    )
    story_rows = build_story_rows(
        [
            story
            for story in stories
            if artifact_id in ((get_current_version(story.get("versions", [])) or {}).get("artifact_refs", []))
        ],
        "../stories/",
        "../releases/",
    )
    requirement_rows = build_requirement_rows(
        [req.get("id") for req in requirements if artifact_id in (req.get("artifact_refs") or [])],
        requirement_lookup or {},
        "../requirements/",
    )
    tabs = [
        {
            "id": slugify("Features"),
            "label": "Features",
            "content": render_connected_table(["Record", "Summary", "Status"], feature_rows, "Features"),
        },
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
    ]
    html += f"""
<div class="section">
    <h2>Connected Records</h2>
    {render_tabs("artifact-connections", tabs)}
</div>
"""
    return html_page(f"{entry['id']}: {entry.get('title', '')}", html, "artifacts", depth=1)
