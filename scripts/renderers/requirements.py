"""Render requirement pages."""

from typing import Dict, List, Optional

from lib.html_helpers import (
    build_artifact_rows,
    build_epic_rows,
    build_feature_rows,
    build_story_rows,
    e,
    html_page,
    render_connected_table,
    render_tabs,
    slugify,
    status_badge,
)
from lib.versions import get_current_version


def render_requirement(
    req: Dict,
    features: List[Dict],
    epics: List[Dict],
    stories: List[Dict],
    artifact_lookup: Optional[Dict[str, Dict]] = None,
) -> str:
    """Render a requirement as HTML."""
    html = f"""
<h1>{e(req['id'])}: {e(req.get('title', ''))}</h1>
<div class="meta">
    <strong>Status:</strong> {status_badge(req.get('status', 'unknown'))} &nbsp;
    <strong>Type:</strong> {e(req.get('type', 'unknown'))}
    {' &nbsp; <strong>Invariant:</strong> Yes' if req.get('invariant') else ''}
</div>
<div class="section">
    <h2>Statement</h2>
    <p>{e(req.get('statement', 'No statement'))}</p>
</div>
<div class="section">
    <h2>Rationale</h2>
    <p>{e(req.get('rationale', 'No rationale'))}</p>
</div>
"""
    if req.get('superseded_by'):
        html += f'<p><strong>Superseded By:</strong> <a href="{req["superseded_by"]}.html">{e(req["superseded_by"])}</a></p>'
    if req.get('notes'):
        html += f'<div class="section"><h2>Notes</h2><p>{e(req["notes"])}</p></div>'

    requirement_id = req.get("id")
    feature_rows = build_feature_rows(
        [feat for feat in features if requirement_id in (feat.get("requirement_refs") or [])],
        "../features/",
    )
    epic_rows = build_epic_rows(
        [
            epic
            for epic in epics
            if requirement_id in ((get_current_version(epic.get("versions", [])) or {}).get("requirement_refs", []))
        ],
        "../epics/",
        "../releases/",
    )
    story_rows = build_story_rows(
        [
            story
            for story in stories
            if requirement_id in ((get_current_version(story.get("versions", [])) or {}).get("requirement_refs", []))
        ],
        "../stories/",
        "../releases/",
    )
    artifact_rows = build_artifact_rows(
        req.get("artifact_refs", []),
        artifact_lookup or {},
        "../artifacts/",
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
            "id": slugify("Business Artifacts"),
            "label": "Business Artifacts",
            "content": render_connected_table(["Record", "Description", "Type"], artifact_rows, "Business Artifacts"),
        },
    ]
    html += f"""
<div class="section">
    <h2>Connected Records</h2>
    {render_tabs("requirement-connections", tabs)}
</div>
"""
    return html_page(f"{req['id']}: {req.get('title', '')}", html, "requirements", depth=1)
