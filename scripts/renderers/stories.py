"""Render story pages."""

from typing import Dict, List, Optional

from lib.html_helpers import (
    build_artifact_rows,
    build_requirement_rows,
    e,
    html_page,
    render_connected_table,
    render_tabs,
    slugify,
    status_badge,
)
from lib.versions import get_current_version


def render_story(
    story: Dict,
    epics: List[Dict],
    features: List[Dict],
    requirement_lookup: Optional[Dict[str, Dict]] = None,
    artifact_lookup: Optional[Dict[str, Dict]] = None,
) -> str:
    """Render a story as HTML."""
    versions = story.get('versions', [])
    doc_status = story.get("status") or "unknown"
    html = f"""
<h1>{e(story['id'])}: {e(story.get('title', ''))}</h1>
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
            <h2>Description</h2>
            <p>{e(v.get('description', 'No description'))}</p>
        </div>
"""
            ac = v.get('acceptance_criteria', [])
            if ac:
                html += '<div class="section"><h2>Acceptance Criteria</h2><ul>'
                for criterion in ac:
                    html += f'<li><strong>{e(criterion.get("id", "AC"))}:</strong> {e(criterion.get("statement", ""))}'
                    if criterion.get('notes'):
                        html += f' <em>({e(criterion["notes"])})</em>'
                    html += '</li>'
                html += '</ul></div>'

            ti = v.get('test_intent', {})
            if ti.get('failure_modes') or ti.get('guarantees') or ti.get('exclusions'):
                html += '<div class="section"><h2>Test Intent</h2>'
                if ti.get('failure_modes'):
                    html += '<h3>Failure Modes (must not happen)</h3><ul>'
                    for item in ti['failure_modes']:
                        html += f'<li>{e(item)}</li>'
                    html += '</ul>'
                if ti.get('guarantees'):
                    html += '<h3>Guarantees (must always be true)</h3><ul>'
                    for item in ti['guarantees']:
                        html += f'<li>{e(item)}</li>'
                    html += '</ul>'
                if ti.get('exclusions'):
                    html += '<h3>Exclusions (not tested)</h3><ul>'
                    for item in ti['exclusions']:
                        html += f'<li>{e(item)}</li>'
                    html += '</ul>'
                html += '</div>'

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
    tabs = [
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
    connected_items = []
    epic_ref = story.get("epic_ref")
    if epic_ref:
        connected_items.append(
            f'<div class="connected-summary"><strong>Epic:</strong> '
            f'<a href="../epics/{e(epic_ref)}.html">{e(epic_ref)}</a></div>'
        )
        epic = next((item for item in epics if item.get("id") == epic_ref), None)
        feature_ref = epic.get("feature_ref") if epic else None
        if feature_ref:
            connected_items.append(
                f'<div class="connected-summary"><strong>Feature:</strong> '
                f'<a href="../features/{e(feature_ref)}.html">{e(feature_ref)}</a></div>'
            )
    html += f"""
<div class="section">
    <h2>Connected Records</h2>
    {''.join(connected_items)}
    {render_tabs("story-connections", tabs)}
</div>
"""
    return html_page(f"{story['id']}: {story.get('title', '')}", html, "stories", depth=1)
