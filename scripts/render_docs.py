#!/usr/bin/env python3
"""
render_docs.py - Generate static HTML documentation for APSCA requirements repository.

Generates HTML files in docs/ from canonical JSON data.
Note: docs/domain/ contains authored content and is NOT overwritten.

Usage:
    python scripts/render_docs.py
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from html import escape

from lib.config import DATA_FILES, DATA_DIR, DOCS_DIR, REPORTS_DIR, ROOT_DIR
from lib.io import load_json
from lib.versions import get_current_version

# Output directories (script-specific, NOT domain/ - that's authored content)
OUTPUT_DIRS = {
    "releases": DOCS_DIR / "releases",
    "requirements": DOCS_DIR / "requirements",
    "features": DOCS_DIR / "features",
    "epics": DOCS_DIR / "epics",
    "stories": DOCS_DIR / "stories",
}


# =============================================================================
# HTML Helpers
# =============================================================================

def e(text: str) -> str:
    """Escape HTML entities."""
    return escape(str(text)) if text else ""


def format_status_label(status: str) -> str:
    """Format a status string for display."""
    if not status:
        return "Unknown"
    return status.replace("_", " ").title()


def status_badge(status: str) -> str:
    """Generate status badge HTML."""
    colors = {
        "planned": "#64748b",
        "released": "#16a34a",
        "superseded": "#9ca3af",
        "active": "#16a34a",
        "proposed": "#64748b",
        "confirmed": "#2563eb",
        "deprecated": "#dc2626",
        "draft": "#94a3b8",
        "approved": "#2563eb",
        "ready_to_build": "#8b5cf6",
        "in_build": "#ec4899",
        "built": "#16a34a",
    }
    color = colors.get(status, "#6b7280")
    label = format_status_label(status)
    return f'<span class="status-badge" style="background-color: {color}">{e(label)}</span>'


def format_refs_html(refs: List[str], prefix: str = "") -> str:
    """Format a list of references as HTML links."""
    if not refs:
        return "<em>None</em>"
    links = [f'<a href="{prefix}{ref}.html">{e(ref)}</a>' for ref in refs]
    return ", ".join(links)


def render_requirements_table(
    requirement_refs: List[str],
    requirement_lookup: Optional[Dict[str, Dict]],
    prefix: str,
) -> str:
    """Render requirement references as a compact table."""
    if not requirement_refs:
        return "<em>None</em>"
    rows = []
    for ref in requirement_refs:
        req = requirement_lookup.get(ref, {}) if requirement_lookup else {}
        title = req.get("title", "")
        title_display = title if title else "—"
        rows.append(
            f"<tr><td><a href=\"{prefix}{e(ref)}.html\">{e(ref)}</a></td>"
            f"<td>{e(title_display)}</td></tr>"
        )
    return (
        "<table>"
        "<thead><tr><th>Requirement</th><th>Title</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


# =============================================================================
# HTML Layout
# =============================================================================

CSS = """
:root {
    --bg-primary: #f3f4f6;
    --bg-secondary: #ffffff;
    --bg-muted: #eef2f6;
    --text-primary: #111827;
    --text-secondary: #4b5563;
    --text-muted: #9aa4b2;
    --border-color: #d7dee8;
    --accent-color: #2563eb;
    --accent-soft: rgba(37, 99, 235, 0.12);
    --success-color: #16a34a;
    --warning-color: #d97706;
    --danger-color: #dc2626;
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
    --shadow-sm: 0 2px 6px rgba(15, 23, 42, 0.06);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.45;
    font-size: 14px;
}

a {
    color: var(--accent-color);
    text-decoration: none;
}

a:hover {
    text-decoration: none;
}

.topbar {
    position: sticky;
    top: 0;
    z-index: 20;
    background: rgba(255, 255, 255, 0.96);
    border-bottom: 1px solid var(--border-color);
    padding: 0.5rem 1.25rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}

.brand {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: 0.02em;
    text-decoration: none;
}

.brand-logo {
    width: 28px;
    height: 28px;
    object-fit: contain;
}

.brand-name {
    font-size: 0.95rem;
}

.topbar-nav {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.35rem;
}

.topbar-nav a {
    padding: 0.35rem 0.55rem;
    border-radius: var(--radius-sm);
    font-size: 0.82rem;
    color: var(--text-secondary);
    border: 1px solid transparent;
    transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
}

.topbar-nav a:hover,
.topbar-nav a.active {
    background: var(--accent-soft);
    color: var(--accent-color);
    border-color: rgba(37, 99, 235, 0.18);
}

main {
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem 1.5rem 2rem;
}

h1 {
    font-size: 1.5rem;
    margin-bottom: 0.4rem;
    color: var(--text-primary);
    letter-spacing: -0.01em;
}

h2 {
    font-size: 1.1rem;
    margin: 1rem 0 0.5rem;
    color: var(--text-primary);
}

h3 {
    font-size: 0.95rem;
    margin: 0.75rem 0 0.4rem;
    color: var(--text-secondary);
    font-weight: 600;
}

p,
ul,
ol {
    margin-bottom: 0.6rem;
}

ul,
ol {
    padding-left: 1.2rem;
}

.muted {
    color: var(--text-secondary);
}

.meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem 0.9rem;
    color: var(--text-secondary);
    font-size: 0.82rem;
    margin-bottom: 0.8rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 0.5rem 0.75rem;
    box-shadow: var(--shadow-xs);
}

.meta strong {
    color: var(--text-secondary);
    font-weight: 600;
}

.status-badge {
    display: inline-block;
    padding: 0.18rem 0.45rem;
    border-radius: 9999px;
    color: white;
    font-size: 0.62rem;
    font-weight: 600;
    text-transform: none;
    letter-spacing: 0.02em;
    box-shadow: none;
}

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
}

.eyebrow {
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.2rem;
}

.page-subtitle {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-bottom: 0;
}

.page-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
}

.button {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.65rem;
    border-radius: var(--radius-sm);
    font-size: 0.82rem;
    border: 1px solid var(--border-color);
    background: var(--bg-secondary);
    color: var(--text-primary);
    text-decoration: none;
    box-shadow: var(--shadow-xs);
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.button.primary {
    background: var(--accent-color);
    color: white;
    border-color: transparent;
}

.button:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
}

.card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 0.75rem 0.9rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-xs);
}

.card-link {
    text-decoration: none;
    color: inherit;
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.card-link:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
    border-color: rgba(37, 99, 235, 0.2);
}

.quick-links {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.65rem;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.65rem;
}

.stat-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 0.75rem;
    box-shadow: var(--shadow-xs);
}

.stat-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}

.stat-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
}

.index-toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: flex-end;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 0.6rem 0.75rem;
    margin: 0.75rem 0 1rem;
    box-shadow: var(--shadow-xs);
}

.toolbar-field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 160px;
    flex: 1 1 200px;
}

.toolbar-field label {
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
}

.toolbar-field input,
.toolbar-field select {
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 0.4rem 0.6rem;
    font-size: 0.82rem;
    background: #ffffff;
    color: var(--text-primary);
}

.toolbar-meta {
    margin-left: auto;
    padding: 0.3rem 0.6rem;
    border-radius: 999px;
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    font-size: 0.78rem;
    color: var(--text-secondary);
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.75rem 0;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: var(--shadow-xs);
    border: 1px solid var(--border-color);
}

th,
td {
    text-align: left;
    padding: 0.55rem 0.7rem;
    border-bottom: 1px solid var(--border-color);
}

th {
    background: var(--bg-primary);
    font-weight: 600;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-secondary);
}

tbody tr:nth-child(even) {
    background: rgba(248, 250, 252, 0.6);
}

tbody tr:hover {
    background: rgba(226, 232, 240, 0.6);
}

td a {
    font-weight: 600;
}

tr:last-child td {
    border-bottom: none;
}

.section {
    margin: 1rem 0;
}

code {
    background: var(--bg-primary);
    padding: 0.15rem 0.35rem;
    border-radius: var(--radius-sm);
    font-size: 0.85em;
}

.version-select {
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 0.3rem 0.55rem;
    font-size: 0.82rem;
    background: #ffffff;
    color: var(--text-primary);
}

.version-panel {
    display: none;
}

.version-panel.active {
    display: block;
}

.version-meta {
    font-size: 0.78rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
}

@media (max-width: 960px) {
    .topbar {
        padding: 0.5rem 0.75rem;
    }

    main {
        padding: 0.75rem 1rem 1.5rem;
    }
}
"""


def generate_navbar(active_section: str = "", depth: int = 1) -> str:
    """Generate standardized navbar HTML."""
    prefix = "../" * depth

    nav_items = [
        ("", "Story Map", "story-map.html"),
        ("features", "Features", "features/index.html"),
        ("epics", "Epics", "epics/index.html"),
        ("stories", "Stories", "stories/index.html"),
        ("requirements", "Requirements", "requirements/index.html"),
        ("domain", "Domain", "domain/index.html"),
        ("releases", "Releases", "releases/index.html"),
    ]

    nav_links = []
    for section, label, href in nav_items:
        active_class = ' class="active"' if section == active_section else ""
        nav_links.append(f'<a href="{prefix}{href}"{active_class}>{label}</a>')
    
    return f"""
<header class="topbar">
    <a class="brand" href="{prefix}story-map.html">
        <img class="brand-logo" src="{prefix}images/apsca_logo_primary.jpg" alt="APSCA" />
        <span class="brand-name">APSCA</span>
    </a>
    <nav class="topbar-nav" aria-label="Primary">
        {' '.join(nav_links)}
    </nav>
</header>
"""


def html_page(title: str, content: str, active_section: str = "", depth: int = 1) -> str:
    """Wrap content in full HTML page with navigation."""
    nav_html = generate_navbar(active_section, depth)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{e(title)} - APSCA</title>
    <style>{CSS}</style>
</head>
<body>
    {nav_html}
    <main>
        {content}
    </main>
</body>
</html>
"""


# =============================================================================
# Render Functions
# =============================================================================

def render_release(release: Dict, epics: List[Dict], stories: List[Dict]) -> str:
    """Render a release as HTML."""
    release_id = release["id"]
    is_unreleased = release_id == "UNRELEASED" or release.get("is_unreleased")
    html = f"""
<h1>{e(release['id'])}</h1>
<div class="meta">
    <strong>Status:</strong> {status_badge(release.get('status', 'unknown'))} &nbsp;
    <strong>Release Date:</strong> {e(release.get('release_date', 'TBD'))}
    {f' &nbsp; <strong>Git Tag:</strong> <code>{e(release.get("git_tag"))}</code>' if release.get('git_tag') else ''}
</div>
<div class="section">
    <h2>Description</h2>
    <p>{e(release.get('description', 'No description'))}</p>
</div>
"""
    if release.get('notes'):
        html += f"""
<div class="section">
    <h2>Notes</h2>
    <p>{e(release['notes'])}</p>
</div>
"""
    if release.get('tags'):
        html += f'<p><strong>Tags:</strong> {", ".join(e(t) for t in release["tags"])}</p>'

    epic_versions = []
    for epic in epics:
        for version in epic.get("versions", []):
            release_ref = version.get("release_ref")
            if (is_unreleased and not release_ref) or (not is_unreleased and release_ref == release_id):
                epic_versions.append(
                    {
                        "id": epic.get("id"),
                        "title": epic.get("title", ""),
                        "version": version.get("version"),
                        "summary": version.get("summary", ""),
                    }
                )
    epic_versions = sorted(epic_versions, key=lambda x: (x.get("id") or "", x.get("version") or 0))

    story_versions = []
    for story in stories:
        for version in story.get("versions", []):
            release_ref = version.get("release_ref")
            if (is_unreleased and not release_ref) or (not is_unreleased and release_ref == release_id):
                story_versions.append(
                    {
                        "id": story.get("id"),
                        "title": story.get("title", ""),
                        "version": version.get("version"),
                        "description": version.get("description", ""),
                    }
                )
    story_versions = sorted(story_versions, key=lambda x: (x.get("id") or "", x.get("version") or 0))

    html += """
<div class="section">
    <h2>Epic Versions</h2>
"""
    if epic_versions:
        html += "<table><thead><tr><th>Epic</th><th>Version</th><th>Summary</th></tr></thead><tbody>"
        for item in epic_versions:
            epic_id = item.get("id", "")
            title = item.get("title", "")
            version_number = item.get("version", "")
            summary = item.get("summary", "No summary")
            html += (
                f"<tr><td><a href=\"../epics/{e(epic_id)}.html\">{e(epic_id)}</a>"
                f"<div class=\"muted\">{e(title)}</div></td>"
                f"<td>v{e(version_number)}</td>"
                f"<td>{e(summary)}</td></tr>"
            )
        html += "</tbody></table>"
    else:
        html += "<p><em>No epic versions tied to this release.</em></p>"
    html += "</div>"

    html += """
<div class="section">
    <h2>Story Versions</h2>
"""
    if story_versions:
        html += "<table><thead><tr><th>Story</th><th>Version</th><th>Description</th></tr></thead><tbody>"
        for item in story_versions:
            story_id = item.get("id", "")
            title = item.get("title", "")
            version_number = item.get("version", "")
            description = item.get("description", "No description")
            html += (
                f"<tr><td><a href=\"../stories/{e(story_id)}.html\">{e(story_id)}</a>"
                f"<div class=\"muted\">{e(title)}</div></td>"
                f"<td>v{e(version_number)}</td>"
                f"<td>{e(description)}</td></tr>"
            )
        html += "</tbody></table>"
    else:
        html += "<p><em>No story versions tied to this release.</em></p>"
    html += "</div>"

    return html_page(release['id'], html, "releases", depth=1)


def render_requirement(req: Dict) -> str:
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
    if req.get('domain_refs'):
        html += f"""
<div class="section">
    <h2>Domain References</h2>
    <p>{format_refs_html(req['domain_refs'], '../domain/')}</p>
</div>
"""
    if req.get('superseded_by'):
        html += f'<p><strong>Superseded By:</strong> <a href="{req["superseded_by"]}.html">{e(req["superseded_by"])}</a></p>'
    if req.get('notes'):
        html += f'<div class="section"><h2>Notes</h2><p>{e(req["notes"])}</p></div>'

    return html_page(f"{req['id']}: {req.get('title', '')}", html, "requirements", depth=1)


def render_feature(feat: Dict, requirement_lookup: Optional[Dict[str, Dict]] = None) -> str:
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

    if feat.get('requirement_refs'):
        html += f"""
<div class="section">
    <h2>Requirements</h2>
    {render_requirements_table(feat['requirement_refs'], requirement_lookup, '../requirements/')}
</div>
"""
    return html_page(f"{feat['id']}: {feat.get('title', '')}", html, "features", depth=1)


def render_epic(epic: Dict, requirement_lookup: Optional[Dict[str, Dict]] = None) -> str:
    """Render an epic as HTML."""
    versions = epic.get('versions', [])
    doc_status = epic.get("status") or "unknown"
    html = f"""
<h1>{e(epic['id'])}: {e(epic.get('title', ''))}</h1>
"""
    if epic.get('feature_ref'):
        html += f"""
<div class="section">
    <h2>Feature</h2>
    <p>Part of <a href="../features/{epic['feature_ref']}.html">{e(epic['feature_ref'])}</a></p>
</div>
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

            if v.get('domain_refs'):
                html += f"""
<div class="section">
    <h2>Domain References</h2>
    <p>{format_refs_html(v['domain_refs'], '../domain/')}</p>
</div>
"""
            if v.get('requirement_refs'):
                html += f"""
<div class="section">
    <h2>Requirements</h2>
    {render_requirements_table(v['requirement_refs'], requirement_lookup, '../requirements/')}
</div>
"""
            html += "</div>"

        html += """
</div>
<script>
(() => {
    const select = document.getElementById('version-select');
    const panels = Array.from(document.querySelectorAll('.version-panel'));
    if (!select || panels.length === 0) return;
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

    return html_page(f"{epic['id']}: {epic.get('title', '')}", html, "epics", depth=1)


def render_story(story: Dict, requirement_lookup: Optional[Dict[str, Dict]] = None) -> str:
    """Render a story as HTML."""
    versions = story.get('versions', [])
    doc_status = story.get("status") or "unknown"
    html = f"""
<h1>{e(story['id'])}: {e(story.get('title', ''))}</h1>
"""
    if story.get('epic_ref'):
        html += f"""
<div class="section">
    <h2>Epic</h2>
    <p>Part of <a href="../epics/{story['epic_ref']}.html">{e(story['epic_ref'])}</a></p>
</div>
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

            if v.get('domain_refs'):
                html += f"""
<div class="section">
    <h2>Domain References</h2>
    <p>{format_refs_html(v['domain_refs'], '../domain/')}</p>
</div>
"""
            if v.get('requirement_refs'):
                html += f"""
<div class="section">
    <h2>Requirements</h2>
    {render_requirements_table(v['requirement_refs'], requirement_lookup, '../requirements/')}
</div>
"""
            html += "</div>"

        html += """
</div>
<script>
(() => {
    const select = document.getElementById('version-select');
    const panels = Array.from(document.querySelectorAll('.version-panel'));
    if (!select || panels.length === 0) return;
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

    return html_page(f"{story['id']}: {story.get('title', '')}", html, "stories", depth=1)


def render_index(artifact_type: str, items: List[Dict], title: str, domain_lookup: Dict[str, Dict] = None) -> str:
    """Render an index page for a collection."""
    html = f'<h1>{e(title)}</h1>\n'
    subtitle_map = {
        "releases": "Release snapshots that bind versions to dates.",
        "requirements": "Non-negotiable rules and obligations for the system.",
        "features": "Top-level capability boundaries that organize epics.",
        "epics": "Stable user intent groupings that organize stories.",
        "stories": "Atomic user capabilities with supporting criteria.",
        "domain": "Reference policies, rules, and domain documentation.",
    }
    subtitle = subtitle_map.get(artifact_type.lower())
    if subtitle:
        html += f'<p class="page-subtitle">{e(subtitle)}</p>\n'

    if not items:
        html += '<p><em>No items yet.</em></p>'
        return html_page(title, html, artifact_type.lower(), depth=1)

    def get_item_status(item: Dict) -> str:
        return item.get("status") or "unknown"

    status_values = sorted({get_item_status(item) for item in items})
    status_options = "\n".join(
        f'<option value="{e(status)}">{e(format_status_label(status))}</option>' for status in status_values
    )
    html += f"""
<div class="index-toolbar">
    <div class="toolbar-field">
        <label for="search-input">Search</label>
        <input type="search" id="search-input" placeholder="Search by ID, title, status, release..." />
    </div>
    <div class="toolbar-field">
        <label for="status-filter">Status</label>
        <select id="status-filter">
            <option value="all">All statuses</option>
            {status_options}
        </select>
    </div>
    <div class="toolbar-meta" id="results-count"></div>
</div>
"""

    # Requirements get a specialized card-based view
    if artifact_type.lower() == "requirements":
        for item in sorted(items, key=lambda x: x.get('id', '')):
            req_type = item.get('type', 'unknown')
            type_color = "#3b82f6" if req_type == "functional" else "#8b5cf6"
            status = item.get("status") or "unknown"
            search_text = " ".join(
                part
                for part in [
                    item.get("id"),
                    item.get("title"),
                    status,
                    req_type,
                    item.get("statement"),
                ]
                if part
            ).lower()

            html += f'''
<div class="card" data-filter-item="true" data-status="{e(status)}" data-search-text="{e(search_text)}" style="margin-bottom: 0.75rem;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
        <div>
            <a href="{item['id']}.html" style="font-weight: 600; font-size: 0.95rem;">{e(item['id'])}: {e(item.get('title', ''))}</a>
        </div>
        <div style="display: flex; gap: 0.5rem;">
            <span class="status-badge" style="background-color: {type_color}">{e(format_status_label(req_type))}</span>
            {status_badge(item.get('status', 'unknown'))}
        </div>
    </div>
    <p style="margin-bottom: 0.5rem; color: var(--text-primary); font-size: 0.85rem;">{e(item.get('statement', 'No statement'))}</p>
'''
            # Domain references
            domain_refs = item.get('domain_refs', [])
            if domain_refs and domain_lookup:
                domain_links = []
                for ref in domain_refs:
                    dom = domain_lookup.get(ref, {})
                    dom_title = dom.get('title', ref)
                    domain_links.append(f'<a href="../domain/{ref}.html">{e(ref)}: {e(dom_title)}</a>')
                html += f'<p style="margin: 0; font-size: 0.78rem; color: var(--text-secondary);"><strong>Domain:</strong> {", ".join(domain_links)}</p>'
            elif domain_refs:
                html += f'<p style="margin: 0; font-size: 0.78rem; color: var(--text-secondary);"><strong>Domain:</strong> {", ".join(domain_refs)}</p>'

            html += '</div>'

        html += """
<script>
(() => {
    const searchInput = document.getElementById('search-input');
    const statusFilter = document.getElementById('status-filter');
    const items = Array.from(document.querySelectorAll('[data-filter-item]'));
    const countEl = document.getElementById('results-count');
    if (!searchInput || !statusFilter || !countEl) return;

    function applyFilters() {
        const term = searchInput.value.trim().toLowerCase();
        const status = statusFilter.value.toLowerCase();
        let visible = 0;
        items.forEach((item) => {
            const text = (item.dataset.searchText || '').toLowerCase();
            const itemStatus = (item.dataset.status || '').toLowerCase();
            const matchesTerm = !term || text.includes(term);
            const matchesStatus = status === 'all' || itemStatus === status;
            const show = matchesTerm && matchesStatus;
            item.style.display = show ? '' : 'none';
            if (show) visible += 1;
        });
        countEl.textContent = `${visible} of ${items.length} shown`;
    }

    searchInput.addEventListener('input', applyFilters);
    statusFilter.addEventListener('change', applyFilters);
    applyFilters();
})();
</script>
"""
        return html_page(title, html, artifact_type.lower(), depth=1)

    # Default table view for other types
    html += '<table><thead><tr><th>ID</th><th>Title</th><th>Status</th></tr></thead><tbody>'

    ordered_items = items
    if artifact_type.lower() != "releases":
        ordered_items = sorted(items, key=lambda x: x.get('id', ''))
    for item in ordered_items:
        item_id = item['id']
        item_title = item.get('title', item_id)
        status = item.get('status') or 'unknown'
        release_ref = None
        if 'versions' in item:
            current = get_current_version(item.get('versions', []))
            release_ref = current.get('release_ref') if current else None

        search_text = " ".join(
            part
            for part in [item_id, item_title, status, release_ref, item.get("owner")]
            if part
        ).lower()
        html += f'<tr data-filter-item="true" data-status="{e(status)}" data-search-text="{e(search_text)}"><td><a href="{item_id}.html">{e(item_id)}</a></td><td>{e(item_title)}</td><td>{status_badge(status)}</td></tr>'

    html += '</tbody></table>'

    html += """
<script>
(() => {
    const searchInput = document.getElementById('search-input');
    const statusFilter = document.getElementById('status-filter');
    const items = Array.from(document.querySelectorAll('[data-filter-item]'));
    const countEl = document.getElementById('results-count');
    if (!searchInput || !statusFilter || !countEl) return;

    function applyFilters() {
        const term = searchInput.value.trim().toLowerCase();
        const status = statusFilter.value.toLowerCase();
        let visible = 0;
        items.forEach((item) => {
            const text = (item.dataset.searchText || '').toLowerCase();
            const itemStatus = (item.dataset.status || '').toLowerCase();
            const matchesTerm = !term || text.includes(term);
            const matchesStatus = status === 'all' || itemStatus === status;
            const show = matchesTerm && matchesStatus;
            item.style.display = show ? '' : 'none';
            if (show) visible += 1;
        });
        countEl.textContent = `${visible} of ${items.length} shown`;
    }

    searchInput.addEventListener('input', applyFilters);
    statusFilter.addEventListener('change', applyFilters);
    applyFilters();
})();
</script>
"""

    return html_page(title, html, artifact_type.lower(), depth=1)


def render_domain_entry(entry: Dict) -> str:
    """Render a single domain entry as HTML."""
    dom_type = entry.get('type', 'unknown')
    type_colors = {
        "policy": "#3b82f6",
        "catalog": "#10b981",
        "classification": "#8b5cf6",
        "rule": "#f59e0b",
    }
    type_color = type_colors.get(dom_type, "#6b7280")

    html = f"""
<h1>{e(entry['id'])}: {e(entry.get('title', ''))}</h1>
<div class="meta">
    <strong>Type:</strong> <span class="status-badge" style="background-color: {type_color}">{e(format_status_label(dom_type))}</span> &nbsp;
    {status_badge(entry.get('status', 'unknown'))} &nbsp;
    <strong>Source:</strong> {e(entry.get('source', 'unknown'))}
    {f' &nbsp; <strong>Effective:</strong> {e(entry.get("effective_date"))}' if entry.get('effective_date') else ''}
</div>
<div class="section">
    <h2>Description</h2>
    <p>{e(entry.get('description', 'No description provided.'))}</p>
</div>
"""
    if entry.get('anchors'):
        html += '<div class="section"><h2>Anchors</h2><ul>'
        for anchor in entry['anchors']:
            html += f'<li>{e(anchor)}</li>'
        html += '</ul></div>'

    if entry.get('notes'):
        html += f'<div class="section"><h2>Notes</h2><p>{e(entry["notes"])}</p></div>'

    if entry.get('tags'):
        html += f'<p><strong>Tags:</strong> {", ".join(e(t) for t in entry["tags"])}</p>'

    return html_page(f"{entry['id']}: {entry.get('title', '')}", html, "domain", depth=1)


def render_domain_index(domain_entries: List[Dict]) -> str:
    """Render a domain index page listing all domain entries."""
    html = '<h1>Domain Reference</h1>\n'
    html += '<p>Business rules, policies, and reference documentation for the system.</p>\n'

    if not domain_entries:
        html += '<p><em>No domain entries yet.</em></p>'
        return html_page("Domain", html, "domain", depth=1)

    status_values = sorted({(entry.get("status") or "unknown") for entry in domain_entries})
    status_options = "\n".join(
        f'<option value="{e(status)}">{e(format_status_label(status))}</option>' for status in status_values
    )
    html += f"""
<div class="index-toolbar">
    <div class="toolbar-field">
        <label for="search-input">Search</label>
        <input type="search" id="search-input" placeholder="Search by ID, title, type, status..." />
    </div>
    <div class="toolbar-field">
        <label for="status-filter">Status</label>
        <select id="status-filter">
            <option value="all">All statuses</option>
            {status_options}
        </select>
    </div>
    <div class="toolbar-meta" id="results-count"></div>
</div>
"""

    for item in sorted(domain_entries, key=lambda x: x.get('id', '')):
        dom_type = item.get('type', 'unknown')
        type_colors = {
            "policy": "#3b82f6",
            "catalog": "#10b981",
            "classification": "#8b5cf6",
            "rule": "#f59e0b",
        }
        type_color = type_colors.get(dom_type, "#6b7280")

        status = item.get("status") or "unknown"
        search_text = " ".join(
            part
            for part in [
                item.get("id"),
                item.get("title"),
                item.get("description"),
                dom_type,
                status,
                item.get("source"),
            ]
            if part
        ).lower()

        html += f'''
<div class="card" data-filter-item="true" data-status="{e(status)}" data-search-text="{e(search_text)}" style="margin-bottom: 0.75rem;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
        <div>
            <a href="{item['id']}.html" style="font-weight: 600; font-size: 0.95rem;">{e(item['id'])}: {e(item.get('title', ''))}</a>
        </div>
        <div style="display: flex; gap: 0.5rem;">
            <span class="status-badge" style="background-color: {type_color}">{e(format_status_label(dom_type))}</span>
            {status_badge(item.get('status', 'unknown'))}
        </div>
    </div>
    <p style="margin-bottom: 0.4rem; color: var(--text-primary); font-size: 0.85rem;">{e(item.get('description', 'No description') if item.get('description') else 'Domain reference document')}</p>
    <p style="margin: 0; font-size: 0.78rem; color: var(--text-secondary);">
        <strong>Source:</strong> {e(item.get('source', 'unknown'))}
        {f' &nbsp; <strong>Effective:</strong> {e(item.get("effective_date"))}' if item.get('effective_date') else ''}
    </p>
</div>
'''

    html += """
<script>
(() => {
    const searchInput = document.getElementById('search-input');
    const statusFilter = document.getElementById('status-filter');
    const items = Array.from(document.querySelectorAll('[data-filter-item]'));
    const countEl = document.getElementById('results-count');
    if (!searchInput || !statusFilter || !countEl) return;

    function applyFilters() {
        const term = searchInput.value.trim().toLowerCase();
        const status = statusFilter.value.toLowerCase();
        let visible = 0;
        items.forEach((item) => {
            const text = (item.dataset.searchText || '').toLowerCase();
            const itemStatus = (item.dataset.status || '').toLowerCase();
            const matchesTerm = !term || text.includes(term);
            const matchesStatus = status === 'all' || itemStatus === status;
            const show = matchesTerm && matchesStatus;
            item.style.display = show ? '' : 'none';
            if (show) visible += 1;
        });
        countEl.textContent = `${visible} of ${items.length} shown`;
    }

    searchInput.addEventListener('input', applyFilters);
    statusFilter.addEventListener('change', applyFilters);
    applyFilters();
})();
</script>
"""

    return html_page("Domain", html, "domain", depth=1)


def render_index_redirect() -> str:
    """Render a simple redirect page that sends users to the Story Map."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=story-map.html">
    <title>Redirecting to Story Map...</title>
    <script>window.location.href = "story-map.html";</script>
</head>
<body>
    <p>Redirecting to <a href="story-map.html">Story Map</a>...</p>
</body>
</html>"""


def main():
    # Load all data
    releases = load_json(DATA_FILES["releases"])
    domain = load_json(DATA_FILES["domain"])
    requirements = load_json(DATA_FILES["requirements"])
    features = load_json(DATA_FILES["features"])
    epics = load_json(DATA_FILES["epics"])
    stories = load_json(DATA_FILES["stories"])

    # Build lookup tables
    domain_lookup = {d['id']: d for d in domain}
    requirement_lookup = {r['id']: r for r in requirements}

    # Ensure output directories exist
    for output_dir in OUTPUT_DIRS.values():
        output_dir.mkdir(parents=True, exist_ok=True)

    counts = {"releases": 0, "domain": 0, "requirements": 0, "features": 0, "epics": 0, "stories": 0}

    # Render domain entries and index
    domain_dir = DOCS_DIR / "domain"
    domain_dir.mkdir(parents=True, exist_ok=True)
    for entry in domain:
        content = render_domain_entry(entry)
        (domain_dir / f"{entry['id']}.html").write_text(content, encoding="utf-8")
        counts["domain"] += 1
    domain_index = render_domain_index(domain)
    (domain_dir / "index.html").write_text(domain_index, encoding="utf-8")

    # Render releases
    unreleased_release = {
        "id": "UNRELEASED",
        "title": "Unreleased",
        "status": "active",
        "release_date": "Unreleased",
        "description": "Versions not yet tied to a release.",
        "git_tag": None,
        "tags": [],
        "owner": "",
        "notes": "",
        "created_at": "",
        "updated_at": "",
        "is_unreleased": True,
    }
    releases_sorted = sorted(
        releases,
        key=lambda r: ((r.get("release_date") or ""), (r.get("id") or "")),
        reverse=True,
    )
    release_items = [unreleased_release] + releases_sorted
    for release in release_items:
        content = render_release(release, epics, stories)
        (OUTPUT_DIRS["releases"] / f"{release['id']}.html").write_text(content, encoding="utf-8")
        counts["releases"] += 1

    index_content = render_index("releases", release_items, "Releases")
    (OUTPUT_DIRS["releases"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render requirements
    for req in requirements:
        content = render_requirement(req)
        (OUTPUT_DIRS["requirements"] / f"{req['id']}.html").write_text(content, encoding="utf-8")
        counts["requirements"] += 1

    index_content = render_index("requirements", requirements, "Requirements", domain_lookup=domain_lookup)
    (OUTPUT_DIRS["requirements"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render features
    for feat in features:
        content = render_feature(feat, requirement_lookup=requirement_lookup)
        (OUTPUT_DIRS["features"] / f"{feat['id']}.html").write_text(content, encoding="utf-8")
        counts["features"] += 1

    index_content = render_index("features", features, "Features")
    (OUTPUT_DIRS["features"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render epics
    for epic in epics:
        content = render_epic(epic, requirement_lookup=requirement_lookup)
        (OUTPUT_DIRS["epics"] / f"{epic['id']}.html").write_text(content, encoding="utf-8")
        counts["epics"] += 1

    index_content = render_index("epics", epics, "Epics")
    (OUTPUT_DIRS["epics"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render stories
    for story in stories:
        content = render_story(story, requirement_lookup=requirement_lookup)
        (OUTPUT_DIRS["stories"] / f"{story['id']}.html").write_text(content, encoding="utf-8")
        counts["stories"] += 1

    index_content = render_index("stories", stories, "Stories")
    (OUTPUT_DIRS["stories"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render index.html as redirect to Story Map
    index_redirect = render_index_redirect()
    (DOCS_DIR / "index.html").write_text(index_redirect, encoding="utf-8")

    # Update story-map.html navbar to match standardized navbar
    story_map_path = DOCS_DIR / "story-map.html"
    if story_map_path.exists():
        story_map_content = story_map_path.read_text(encoding="utf-8")
        # Generate navbar with active section set to "" (Story Map is active)
        new_navbar = generate_navbar(active_section="", depth=0)
        # Replace the navbar section (from <header class="topbar"> to </header>)
        import re
        story_map_content = re.sub(
            r'<header class="topbar">.*?</header>',
            new_navbar.strip(),
            story_map_content,
            flags=re.DOTALL
        )
        story_map_path.write_text(story_map_content, encoding="utf-8")

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
