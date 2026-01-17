"""Render epic pages."""

from typing import Dict, List, Optional

from lib.html_helpers import (
    build_artifact_rows,
    build_requirement_rows,
    build_story_rows,
    e,
    html_page,
    render_connected_table,
    render_tabs,
    slugify,
    status_badge,
)
from lib.versions import get_current_version


def render_epic(
    epic: Dict,
    stories: List[Dict],
    requirement_lookup: Optional[Dict[str, Dict]] = None,
    artifact_lookup: Optional[Dict[str, Dict]] = None,
) -> str:
    """Render an epic as HTML."""
    versions = epic.get('versions', [])
    doc_status = epic.get("status") or "unknown"
    html = f"""
<h1>{e(epic['id'])}: {e(epic.get('title', ''))}</h1>
"""
    if versions:
        current = get_current_version(versions)
        current_version = current.get("version") if current else None
        versions_sorted = sorted(versions, key=lambda x: x.get("version", 0), reverse=True)
        select_options = "\n".join(
            f'<option value="{e(v.get("version"))}"{" selected" if v.get("version") == current_version else ""}>'
            f'v{e(v.get("version"))} — {e(v.get("release_ref") or "Unassigned")}</option>'
            for v in versions_sorted
        )
        html += f"""
<div class="meta">
    <span><strong>Documentation Status:</strong> {status_badge(doc_status)}</span>
    <span><strong>Version:</strong>
        <select id="version-select" class="version-select">
            {select_options}
        </select>
    </span>
</div>
<div class="version-panels">
"""
        for v in versions_sorted:
            release_ref = v.get("release_ref")
            release_html = (
                f'<a href="../releases/{e(release_ref)}.html">{e(release_ref)}</a>'
                if release_ref
                else "Unassigned"
            )
            html += f"""
    <div class="version-panel" data-version="{e(v.get('version'))}">
        <div class="version-meta">
            <strong>Version:</strong> v{e(v.get('version'))} &nbsp;
            <strong>Release:</strong> {release_html}
        </div>
        <div class="section">
            <h2>Summary</h2>
            <p>{e(v.get('summary', 'No summary'))}</p>
        </div>
"""
            if v.get('assumptions'):
                html += '<div class="section"><h2>Assumptions</h2><ul>'
                for item in v['assumptions']:
                    html += f'<li>{e(item)}</li>'
                html += '</ul></div>'

            if v.get('constraints'):
                html += '<div class="section"><h2>Constraints</h2><ul>'
                for item in v['constraints']:
                    html += f'<li>{e(item)}</li>'
                html += '</ul></div>'

            html += "</div>"

        html += """
</div>
<script>
(() => {
    const select = document.getElementById('version-select');
    const panels = Array.from(document.querySelectorAll('.version-panel'));
    if (!select || panels.length === 0) return;
    const params = new URLSearchParams(window.location.search);
    const requestedVersion = params.get('version');
    if (requestedVersion) {
        const option = Array.from(select.options).find(opt => opt.value === requestedVersion);
        if (option) {
            select.value = requestedVersion;
        }
    }
    function show(version) {
        panels.forEach(panel => {
            panel.classList.toggle('active', panel.dataset.version === version);
        });
    }
    select.addEventListener('change', () => show(select.value));
    show(select.value);
})();
</script>
"""
    else:
        html += '<p><em>No versions recorded.</em></p>'

    current_version = get_current_version(versions) if versions else None
    requirement_rows = build_requirement_rows(
        (current_version or {}).get("requirement_refs", []),
        requirement_lookup or {},
        "../requirements/",
    )
    artifact_rows = build_artifact_rows(
        (current_version or {}).get("domain_refs", []),
        artifact_lookup or {},
        "../domain/",
    )
    epic_stories = [story for story in stories if story.get("epic_ref") == epic.get("id")]
    story_rows = build_story_rows(epic_stories, "../stories/", "../releases/")

    tabs = [
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
    connected_summary = ""
    if epic.get("feature_ref"):
        connected_summary = (
            f'<div class="connected-summary"><strong>Feature:</strong> '
            f'<a href="../features/{e(epic["feature_ref"])}.html">{e(epic["feature_ref"])}</a></div>'
        )
    html += f"""
<div class="section">
    <h2>Connected Records</h2>
    {connected_summary}
    {render_tabs("epic-connections", tabs)}
</div>
"""
    return html_page(f"{epic['id']}: {epic.get('title', '')}", html, "epics", depth=1)
