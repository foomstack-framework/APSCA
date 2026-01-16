#!/usr/bin/env python3
"""
render_docs.py - Generate static HTML documentation for APSCA requirements repository.

Generates HTML files in docs/ from canonical JSON data.
Note: docs/domain/ contains authored content and is NOT overwritten.

Usage:
    python scripts/render_docs.py
"""

import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from html import escape

from lib.config import DATA_FILES, DATA_DIR, DOCS_DIR, REPORTS_DIR, ROOT_DIR
from lib.io import load_json
from lib.versions import get_current_version
from lib.assets import (
    CSS,
    BREADCRUMB_CSS,
    BREADCRUMB_JS,
    VERSION_BANNER_CSS,
    VERSION_BANNER_HTML,
    VERSION_CHECK_JS,
    REDIRECT_HTML
)

# Version file path
VERSION_FILE = DOCS_DIR / "version.json"


def get_build_version() -> str:
    """Get the build version from version.json, or empty string if not available."""
    try:
        if VERSION_FILE.exists():
            version_data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
            return version_data.get("commit", "")
    except (json.JSONDecodeError, IOError):
        pass
    return ""

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
        # Release statuses
        "planned": "#64748b",      # Gray
        "released": "#16a34a",     # Green
        # Artifact lifecycle
        "active": "#16a34a",       # Green
        "deprecated": "#dc2626",   # Red
        "draft": "#94a3b8",        # Light gray
        "provisional": "#f59e0b",  # Amber
        # Version statuses
        "backlog": "#2563eb",      # Blue
        "discarded": "#9ca3af",    # Gray
    }
    color = colors.get(status, "#6b7280")
    label = format_status_label(status)
    return f'<span class="status-badge" style="background-color: {color}">{e(label)}</span>'


def artifact_type_badge(dom_type) -> str:
    """Generate badge HTML for business artifact types. Handles both string and array of types."""
    if isinstance(dom_type, list):
        dom_type = dom_type[0] if dom_type else "unknown"
    type_colors = {
        "policy": "#3b82f6",
        "catalog": "#10b981",
        "classification": "#8b5cf6",
        "rule": "#f59e0b",
    }

    # Handle array of types
    if isinstance(dom_type, list):
        badges = []
        for t in dom_type:
            type_color = type_colors.get(t, "#6b7280")
            badges.append(f'<span class="status-badge" style="background-color: {type_color}">{e(format_status_label(t))}</span>')
        return " ".join(badges)

    # Handle single string type
    type_color = type_colors.get(dom_type, "#6b7280")
    return f'<span class="status-badge" style="background-color: {type_color}">{e(format_status_label(dom_type))}</span>'


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


def format_secondary(text: str) -> str:
    """Render a secondary line within a table cell."""
    return f'<div class="cell-secondary">{e(text)}</div>' if text else ""


def render_connected_table(headers: List[str], rows: List[List[str]], empty_label: str) -> str:
    """Render a compact table for connected records with an empty-state row."""
    header_html = "".join(f"<th>{e(header)}</th>" for header in headers)
    if rows:
        body_html = "".join("<tr>" + "".join(cells) + "</tr>" for cells in rows)
    else:
        body_html = (
            f'<tr><td class="empty-cell" colspan="{len(headers)}">'
            f"<em>There are no {e(empty_label)} to display.</em></td></tr>"
        )
    return (
        '<table class="connected-table">'
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{body_html}</tbody>"
        "</table>"
    )


def render_tabs(group_id: str, tabs: List[Dict[str, str]]) -> str:
    """Render a tabbed UI with panels."""
    if not tabs:
        return ""
    panels = []
    buttons = []
    for idx, tab in enumerate(tabs):
        tab_id = tab["id"]
        label = tab["label"]
        content = tab["content"]
        panel_id = f"{group_id}-{tab_id}"
        is_active = idx == 0
        active_class = " active" if is_active else ""
        aria_selected = "true" if is_active else "false"
        buttons.append(
            f'<button class="tab-button{active_class}" type="button" role="tab" '
            f'data-tab-target="{panel_id}" aria-selected="{aria_selected}">{e(label)}</button>'
        )
        panels.append(
            f'<div class="tab-panel{active_class}" id="{panel_id}" '
            f'data-tab-panel="true" role="tabpanel">{content}</div>'
        )
    return (
        f'<div class="tabs" data-tab-group="{e(group_id)}">'
        f'<div class="tab-list" role="tablist">{"".join(buttons)}</div>'
        f'<div class="tab-panels">{"".join(panels)}</div>'
        "</div>"
    )


def slugify(text: str) -> str:
    """Create a safe ID string for HTML elements."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "tab"


def render_record_cell(item_id: str, title: str, prefix: str) -> str:
    return (
        f'<td class="record-cell"><a href="{prefix}{e(item_id)}.html">{e(item_id)}</a>'
        f"{format_secondary(title)}</td>"
    )


def render_summary_cell(primary: str, secondary: str = "") -> str:
    return (
        f'<td class="summary-cell"><div class="cell-primary">{e(primary)}</div>'
        f"{format_secondary(secondary)}</td>"
    )


def render_release_cell(release_ref: Optional[str], prefix: str) -> str:
    if release_ref:
        return f'<td><a href="{prefix}{e(release_ref)}.html">{e(release_ref)}</a></td>'
    return "<td>Unassigned</td>"


def build_feature_rows(features: List[Dict], prefix: str) -> List[List[str]]:
    rows = []
    for feat in features:
        feat_id = feat.get("id", "")
        title = feat.get("title", "")
        purpose = feat.get("purpose", "No purpose defined")
        business_value = feat.get("business_value", "")
        status = feat.get("status", "unknown")
        rows.append(
            [
                render_record_cell(feat_id, title, prefix),
                render_summary_cell(purpose, business_value),
                f'<td class="status-cell"><div class="badge-stack">{status_badge(status)}</div></td>',
            ]
        )
    return rows


def build_epic_rows(epics: List[Dict], epic_prefix: str, release_prefix: str) -> List[List[str]]:
    rows = []
    for epic in epics:
        epic_id = epic.get("id", "")
        title = epic.get("title", "")
        current = get_current_version(epic.get("versions", []))
        summary = current.get("summary", "No summary") if current else "No versions recorded"
        release_ref = current.get("release_ref") if current else None
        rows.append(
            [
                render_record_cell(epic_id, title, epic_prefix),
                render_summary_cell(summary),
                render_release_cell(release_ref, release_prefix),
            ]
        )
    return rows


def build_story_rows(stories: List[Dict], story_prefix: str, release_prefix: str) -> List[List[str]]:
    rows = []
    for story in stories:
        story_id = story.get("id", "")
        title = story.get("title", "")
        current = get_current_version(story.get("versions", []))
        description = current.get("description", "No description") if current else "No versions recorded"
        release_ref = current.get("release_ref") if current else None
        rows.append(
            [
                render_record_cell(story_id, title, story_prefix),
                render_summary_cell(description),
                render_release_cell(release_ref, release_prefix),
            ]
        )
    return rows


def build_requirement_rows(requirement_refs: List[str], requirement_lookup: Dict[str, Dict], prefix: str) -> List[List[str]]:
    rows = []
    for ref in requirement_refs or []:
        req = requirement_lookup.get(ref, {})
        title = req.get("title", "")
        statement = req.get("statement", "No statement")
        rows.append(
            [
                render_record_cell(ref, title, prefix),
                render_summary_cell(statement),
            ]
        )
    return rows


def build_artifact_rows(artifact_refs: List[str], artifact_lookup: Dict[str, Dict], prefix: str) -> List[List[str]]:
    rows = []
    for ref in artifact_refs or []:
        artifact = artifact_lookup.get(ref, {})
        title = artifact.get("title", "")
        description = artifact.get("description", "Business artifact")
        dom_type = artifact.get("type", "unknown")
        rows.append(
            [
                render_record_cell(ref, title, prefix),
                render_summary_cell(description),
                f'<td class="status-cell"><div class="badge-stack">{artifact_type_badge(dom_type)}</div></td>',
            ]
        )
    return rows


# =============================================================================
# HTML Layout
# =============================================================================



def generate_navbar(active_section: str = "", depth: int = 1) -> str:
    """Generate standardized navbar HTML."""
    prefix = "../" * depth

    nav_items = [
        ("", "Story Map", "story-map.html"),
        ("features", "Features", "features/index.html"),
        ("epics", "Epics", "epics/index.html"),
        ("stories", "Stories", "stories/index.html"),
        ("requirements", "Requirements", "requirements/index.html"),
        ("domain", "Business Artifacts", "domain/index.html"),
        ("releases", "Releases", "releases/index.html"),
    ]

    nav_links = []
    for section, label, href in nav_items:
        active_class = ' class="active"' if section == active_section else ""
        nav_links.append(f'<a href="{prefix}{href}?nav=1"{active_class}>{label}</a>')

    return f"""
<header class="topbar">
    <a class="brand" href="{prefix}story-map.html?nav=1">
        <img class="brand-logo" src="{prefix}images/APSCA-logo.svg" alt="APSCA" width="36" height="36" />
        <span class="brand-name">APSCA Requirements Dashboard</span>
    </a>
    <nav class="topbar-nav" aria-label="Primary">
        {' '.join(nav_links)}
    </nav>
</header>
"""


def html_page(title: str, content: str, active_section: str = "", depth: int = 1, custom_main: bool = False) -> str:
    """Wrap content in full HTML page with navigation.

    Args:
        title: Page title
        content: HTML content
        active_section: Active nav section
        depth: URL depth for relative paths
        custom_main: If True, don't wrap content in <main> tags (for custom layouts)
    """
    nav_html = generate_navbar(active_section, depth)
    breadcrumb_html = '<nav id="breadcrumb-nav" class="breadcrumb-nav" aria-label="Breadcrumb"></nav>'
    prefix = "../" * depth
    build_version = get_build_version()

    # Version banner HTML (hidden by default, shown by JS when version mismatch detected)
    version_banner = '''<div id="version-banner" class="version-banner hidden" role="alert">
        <span class="version-banner-text">
            A newer version is available.
            <span>Or press <kbd class="version-banner-kbd">Ctrl+Shift+R</kbd></span>
        </span>
        <button class="version-banner-refresh" onclick="location.reload(true)">Refresh Now</button>
        <button class="version-banner-dismiss" onclick="dismissVersionBanner()" aria-label="Dismiss">&times;</button>
    </div>'''

    if custom_main:
        main_section = content
    else:
        main_section = f"<main>\n        {breadcrumb_html}\n        {content}\n    </main>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="apsca-version" content="{e(build_version)}">
    <title>{e(title)} - APSCA</title>
    <style>{CSS}</style>
</head>
<body>
    {version_banner}
    {nav_html}
    {main_section}
    <script>
    (() => {{
        function initTabs() {{
            const groups = document.querySelectorAll('[data-tab-group]');
            groups.forEach((group) => {{
                const buttons = Array.from(group.querySelectorAll('.tab-button'));
                const panels = Array.from(group.querySelectorAll('[data-tab-panel]'));
                if (buttons.length === 0 || panels.length === 0) return;

                function setActive(button) {{
                    const targetId = button.dataset.tabTarget;
                    const targetPanel = group.querySelector(`#${{CSS.escape(targetId)}}`);
                    buttons.forEach((btn) => {{
                        btn.classList.remove('active');
                        btn.setAttribute('aria-selected', 'false');
                    }});
                    panels.forEach((panel) => panel.classList.remove('active'));
                    button.classList.add('active');
                    button.setAttribute('aria-selected', 'true');
                    if (targetPanel) {{
                        targetPanel.classList.add('active');
                    }}
                }}

                buttons.forEach((button) => {{
                    button.addEventListener('click', () => setActive(button));
                }});

                const defaultButton = buttons.find(btn => btn.classList.contains('active')) || buttons[0];
                setActive(defaultButton);
            }});
        }}

        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initTabs);
        }} else {{
            initTabs();
        }}
    }})();

    // Breadcrumb Navigation
    const BreadcrumbNav = (() => {{
        const STORAGE_KEY = 'apsca_nav_history';
        const MAX_HISTORY = 10;
        const TRUNCATE_DISPLAY = 5;

        function getHistory() {{
            try {{
                const data = sessionStorage.getItem(STORAGE_KEY);
                return data ? JSON.parse(data) : [];
            }} catch (e) {{ return []; }}
        }}

        function saveHistory(history) {{
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-MAX_HISTORY)));
        }}

        function getCurrentPageInfo() {{
            const path = window.location.pathname;
            const parts = path.split('/').filter(Boolean);
            const filename = parts.pop() || 'index.html';
            const lastDir = parts.pop() || '';

            const knownSections = ['features', 'epics', 'stories', 'requirements', 'domain', 'releases'];
            const dir = knownSections.includes(lastDir) ? lastDir : '';

            const sectionLabels = {{
                'features': 'Features', 'epics': 'Epics', 'stories': 'Stories',
                'requirements': 'Requirements', 'domain': 'Business Artifacts', 'releases': 'Releases'
            }};

            let label;
            if (filename === 'index.html') {{
                label = sectionLabels[dir] || 'Home';
            }} else if (filename === 'story-map.html') {{
                label = 'Story Map';
            }} else {{
                label = filename.replace('.html', '');
            }}

            const url = dir ? dir + '/' + filename : filename;
            return {{ url, label, timestamp: Date.now() }};
        }}

        function updateHistoryOnLoad() {{
            const params = new URLSearchParams(window.location.search);
            const isNavClick = params.has('nav');

            if (isNavClick) {{
                params.delete('nav');
                const newUrl = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
                window.history.replaceState(null, '', newUrl);
                sessionStorage.removeItem(STORAGE_KEY);
            }}

            const history = isNavClick ? [] : getHistory();
            const currentPage = getCurrentPageInfo();
            const existingIndex = history.findIndex(e => e.url === currentPage.url);

            if (existingIndex !== -1) {{
                const truncated = history.slice(0, existingIndex + 1);
                truncated[truncated.length - 1].timestamp = Date.now();
                saveHistory(truncated);
            }} else {{
                history.push(currentPage);
                saveHistory(history);
            }}
        }}

        function getRelativePath(fromUrl, toUrl) {{
            const fromParts = fromUrl.split('/');
            const toParts = toUrl.split('/');
            fromParts.pop();
            const toFile = toParts.pop();
            const fromDir = fromParts.join('/');
            const toDir = toParts.join('/');
            if (fromDir === toDir) {{
                return toFile;
            }}
            const upLevels = fromParts.length;
            return '../'.repeat(upLevels) + toUrl;
        }}

        function renderBreadcrumbs() {{
            const history = getHistory();
            const container = document.getElementById('breadcrumb-nav');
            if (!container || history.length <= 1) {{
                if (container) container.style.display = 'none';
                return;
            }}

            const currentPage = history[history.length - 1];
            const previousPages = history.slice(0, -1);
            let display = previousPages;
            let showEllipsis = false;

            if (previousPages.length > TRUNCATE_DISPLAY) {{
                display = previousPages.slice(-TRUNCATE_DISPLAY);
                showEllipsis = true;
            }}

            let html = showEllipsis ? '<span class="breadcrumb-ellipsis">...</span><span class="breadcrumb-separator">›</span>' : '';

            display.forEach((entry, idx) => {{
                if (idx > 0) html += '<span class="breadcrumb-separator">›</span>';
                const href = getRelativePath(currentPage.url, entry.url);
                html += '<a href="' + href + '" class="breadcrumb-link">' + entry.label + '</a>';
            }});

            if (display.length > 0) {{
                html += '<span class="breadcrumb-separator">›</span>';
            }}
            html += '<span class="breadcrumb-current">' + currentPage.label + '</span>';

            container.innerHTML = html;
            container.style.display = '';
        }}

        function init() {{
            updateHistoryOnLoad();
            renderBreadcrumbs();
        }}

        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', init);
        }} else {{
            init();
        }}

        return {{ init }};
    }})();

    // Version Check
    const VersionCheck = (() => {{
        const DISMISSED_KEY = 'apsca_version_dismissed';
        const VERSION_URL = '{prefix}version.json';

        function getPageVersion() {{
            const meta = document.querySelector('meta[name="apsca-version"]');
            return meta ? meta.getAttribute('content') : '';
        }}

        function getDismissedVersion() {{
            try {{
                return localStorage.getItem(DISMISSED_KEY) || '';
            }} catch (e) {{ return ''; }}
        }}

        function setDismissedVersion(version) {{
            try {{
                localStorage.setItem(DISMISSED_KEY, version);
            }} catch (e) {{}}
        }}

        function showBanner() {{
            const banner = document.getElementById('version-banner');
            if (banner) {{
                banner.classList.remove('hidden');
                document.body.classList.add('has-version-banner');
                // Update keyboard shortcut for Mac
                if (navigator.platform.indexOf('Mac') !== -1) {{
                    const kbd = banner.querySelector('.version-banner-kbd');
                    if (kbd) kbd.textContent = 'Cmd+Shift+R';
                }}
            }}
        }}

        async function checkVersion() {{
            const pageVersion = getPageVersion();
            if (!pageVersion) return; // No version embedded, skip check

            try {{
                const response = await fetch(VERSION_URL + '?t=' + Date.now());
                if (!response.ok) return;
                const data = await response.json();
                const serverVersion = data.commit || '';

                if (serverVersion && serverVersion !== pageVersion) {{
                    const dismissed = getDismissedVersion();
                    if (dismissed !== serverVersion) {{
                        showBanner();
                    }}
                }}
            }} catch (e) {{
                // Network error or version.json missing - silent fail
            }}
        }}

        // Global function for dismiss button
        window.dismissVersionBanner = function() {{
            const banner = document.getElementById('version-banner');
            if (banner) {{
                banner.classList.add('hidden');
                document.body.classList.remove('has-version-banner');
            }}
            // Get server version to store as dismissed
            fetch(VERSION_URL + '?t=' + Date.now())
                .then(r => r.json())
                .then(data => {{
                    if (data.commit) setDismissedVersion(data.commit);
                }})
                .catch(() => {{}});
        }};

        // Run check after page loads
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', checkVersion);
        }} else {{
            checkVersion();
        }}

        return {{ checkVersion }};
    }})();
    </script>
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

    epic_rows = []
    for item in epic_versions:
        epic_id = item.get("id", "")
        title = item.get("title", "")
        version_number = item.get("version", "")
        summary = item.get("summary", "No summary")
        epic_rows.append(
            [
                f'<td class="record-cell"><a href="../epics/{e(epic_id)}.html?version={e(version_number)}">{e(epic_id)}</a>'
                f"{format_secondary(title)}</td>",
                f"<td>v{e(version_number)}</td>",
                render_summary_cell(summary),
            ]
        )

    story_rows = []
    for item in story_versions:
        story_id = item.get("id", "")
        title = item.get("title", "")
        version_number = item.get("version", "")
        description = item.get("description", "No description")
        story_rows.append(
            [
                f'<td class="record-cell"><a href="../stories/{e(story_id)}.html?version={e(version_number)}">{e(story_id)}</a>'
                f"{format_secondary(title)}</td>",
                f"<td>v{e(version_number)}</td>",
                render_summary_cell(description),
            ]
        )

    tabs = [
        {
            "id": slugify("Epic Versions"),
            "label": "Epic Versions",
            "content": render_connected_table(["Epic", "Version", "Summary"], epic_rows, "Epic Versions"),
        },
        {
            "id": slugify("Story Versions"),
            "label": "Story Versions",
            "content": render_connected_table(["Story", "Version", "Description"], story_rows, "Story Versions"),
        },
    ]
    html += f"""
<div class="section">
    <h2>Connected Versions</h2>
    {render_tabs("release-versions", tabs)}
</div>
"""

    return html_page(release['id'], html, "releases", depth=1)


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
        req.get("domain_refs", []),
        artifact_lookup or {},
        "../domain/",
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
        feat.get("domain_refs", []),
        artifact_lookup or {},
        "../domain/",
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


def render_index(artifact_type: str, items: List[Dict], title: str, domain_lookup: Dict[str, Dict] = None, epic_lookup: Dict[str, Dict] = None) -> str:
    """Render an index page for a collection."""
    html = f'<h1>{e(title)}</h1>\n'
    subtitle_map = {
        "releases": "Release snapshots that bind versions to dates.",
        "requirements": "Non-negotiable rules and obligations for the system.",
        "features": "Top-level capability boundaries that organize epics.",
        "epics": "Stable user intent groupings that organize stories.",
        "stories": "Atomic user capabilities with supporting criteria.",
        "domain": "Business artifacts, policies, rules, and reference documentation.",
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
    # For stories and epics, always include both active and deprecated options
    if artifact_type.lower() in ("stories", "epics"):
        status_values = sorted(set(status_values) | {"active", "deprecated"})
    status_options = "\n".join(
        f'<option value="{e(status)}">{e(format_status_label(status))}</option>' for status in status_values
    )

    # Build epic filter dropdown for stories
    epic_filter_html = ""
    if artifact_type.lower() == "stories" and epic_lookup:
        epics_sorted = sorted(epic_lookup.values(), key=lambda x: x.get('id', ''))
        epic_items_html = ""
        for ep in epics_sorted:
            ep_id = e(ep.get('id', ''))
            ep_title = e(ep.get('title', ''))
            epic_items_html += f'''
                <label class="epic-filter-item">
                    <input type="checkbox" value="{ep_id}" />
                    <span><strong>{ep_id}</strong>: {ep_title}</span>
                </label>
            '''
        epic_filter_html = f"""
    <div class="toolbar-field epic-filter-dropdown" id="epic-filter-dropdown">
        <label>Epic</label>
        <button type="button" class="epic-filter-trigger" id="epic-filter-trigger" aria-expanded="false">All epics</button>
        <div class="epic-filter-menu" id="epic-filter-menu">
            <input type="search" class="epic-filter-search" id="epic-filter-search" placeholder="Filter epics..." />
            <div class="epic-filter-list" id="epic-filter-list">
                {epic_items_html}
            </div>
        </div>
    </div>
"""

    # For stories, use "User Story Status" label and default to active
    if artifact_type.lower() == "stories":
        status_filter_label = "User Story Status"
        status_filter_default = "active"
    else:
        status_filter_label = "Status"
        status_filter_default = "all"

    html += f"""
<div class="index-toolbar">
    <div class="toolbar-field">
        <label for="search-input">Search</label>
        <input type="search" id="search-input" placeholder="Search by ID, title, status, release..." />
    </div>
    <div class="toolbar-field">
        <label for="status-filter">{status_filter_label}</label>
        <select id="status-filter">
            <option value="all">All statuses</option>
            {status_options}
        </select>
    </div>
    {epic_filter_html}
    <div class="toolbar-meta" id="results-count"></div>
</div>
<script>
(function() {{
    var statusFilter = document.getElementById('status-filter');
    if (statusFilter && '{status_filter_default}' !== 'all') {{
        statusFilter.value = '{status_filter_default}';
    }}
}})();
</script>
"""

    def requirement_type_badge(req_type: str) -> str:
        type_color = "#3b82f6" if req_type == "functional" else "#8b5cf6"
        return f'<span class="status-badge" style="background-color: {type_color}">{e(format_status_label(req_type))}</span>'

    def build_summary(item: Dict) -> Dict[str, str]:
        kind = artifact_type.lower()
        if kind == "features":
            primary = item.get("purpose", "No purpose defined")
            secondary = item.get("business_value", "")
        elif kind == "epics":
            current = get_current_version(item.get("versions", []))
            primary = current.get("summary", "No summary") if current else "No versions recorded"
            secondary = f"Release: {current.get('release_ref') or 'Unassigned'}" if current else ""
        elif kind == "stories":
            current = get_current_version(item.get("versions", []))
            primary = current.get("description", "No description") if current else "No versions recorded"
            secondary = f"Release: {current.get('release_ref') or 'Unassigned'}" if current else ""
        elif kind == "requirements":
            primary = item.get("statement", "No statement")
            domain_refs = item.get("domain_refs", [])
            if domain_refs and domain_lookup:
                domain_titles = []
                for ref in domain_refs:
                    dom = domain_lookup.get(ref, {})
                    domain_titles.append(f"{ref}: {dom.get('title', ref)}")
                secondary = f"Domain: {', '.join(domain_titles)}"
            elif domain_refs:
                secondary = f"Domain: {', '.join(domain_refs)}"
            else:
                secondary = ""
        elif kind == "domain":
            primary = item.get("description") or "Domain reference document"
            source = item.get("source", "unknown")
            effective = item.get("effective_date")
            secondary = f"Source: {source}"
            if effective:
                secondary += f" | Effective: {effective}"
        elif kind == "releases":
            primary = f"Release Date: {item.get('release_date', 'TBD')}"
            secondary = item.get("description", "")
        else:
            primary = item.get("title", "")
            secondary = ""
        return {"primary": primary, "secondary": secondary}

    if artifact_type.lower() == "requirements":
        html += '<table class="index-table"><thead><tr><th>Record</th><th>Summary</th><th>Type</th><th>Status</th></tr></thead><tbody>'
    elif artifact_type.lower() == "stories" and epic_lookup:
        html += '<table class="index-table"><thead><tr><th>Record</th><th>Summary</th><th>Epic</th><th>Version</th><th>User Story Status</th><th>Version Status</th><th>Version Approval</th></tr></thead><tbody>'
    else:
        html += '<table class="index-table"><thead><tr><th>Record</th><th>Summary</th><th>Status</th></tr></thead><tbody>'

    ordered_items = items
    if artifact_type.lower() != "releases":
        ordered_items = sorted(items, key=lambda x: x.get('id', ''))
    for item in ordered_items:
        item_id = item['id']
        item_title = item.get('title', '')
        status = item.get('status') or 'unknown'
        release_ref = None
        if 'versions' in item:
            current = get_current_version(item.get('versions', []))
            release_ref = current.get('release_ref') if current else None

        summary = build_summary(item)
        primary_summary = summary.get("primary", "")
        secondary_summary = summary.get("secondary", "")

        search_text = " ".join(
            part
            for part in [
                item_id,
                item_title,
                status,
                release_ref,
                item.get("owner"),
                primary_summary,
                secondary_summary,
                item.get("type"),
                item.get("purpose"),
                item.get("description"),
            ]
            if part
        ).lower()

        # Build status badges - for versioned artifacts, show both artifact and version status
        status_badges = [status_badge(status)]
        if artifact_type.lower() in ("stories", "epics") and 'versions' in item:
            current = get_current_version(item.get('versions', []))
            if current:
                version_status = current.get('status', 'unknown')
                status_badges.append(status_badge(version_status))
                # Show approval indicator for backlog items that are approved
                if version_status == 'backlog' and current.get('approved'):
                    status_badges.append('<span class="status-badge" style="background-color: #059669">Approved</span>')

        type_badge = ""
        if artifact_type.lower() == "requirements":
            type_badge = requirement_type_badge(item.get("type", "unknown"))
        if artifact_type.lower() == "domain":
            type_badge = artifact_type_badge(item.get("type", "unknown"))

        if artifact_type.lower() == "requirements":
            html += (
                f'<tr data-filter-item="true" data-status="{e(status)}" data-search-text="{e(search_text)}">'
                f'<td class="record-cell"><a href="{item_id}.html">{e(item_id)}</a>'
                f'{format_secondary(item_title)}</td>'
                f'<td class="summary-cell"><div class="cell-primary">{e(primary_summary)}</div>'
                f'{format_secondary(secondary_summary)}</td>'
                f'<td class="status-cell"><div class="badge-stack">{type_badge}</div></td>'
                f'<td class="status-cell"><div class="badge-stack">{"".join(status_badges)}</div></td>'
                '</tr>'
            )
        elif artifact_type.lower() == "stories" and epic_lookup:
            epic_ref = item.get('epic_ref', '')
            epic_data = epic_lookup.get(epic_ref) if epic_ref else None
            if epic_ref and epic_data:
                epic_cell_html = (
                    f'<td class="epic-cell">'
                    f'<button type="button" class="epic-cell-link" data-epic-id="{e(epic_ref)}" aria-label="View epic details">'
                    f'{e(epic_ref)}'
                    f'</button>'
                    f'</td>'
                )
            else:
                epic_cell_html = '<td class="epic-cell"><span class="epic-cell-none">None</span></td>'

            # Include epic_ref in search text for filtering
            search_text_with_epic = search_text
            if epic_ref:
                epic_title = epic_data.get('title', '') if epic_data else ''
                search_text_with_epic = f"{search_text} {epic_ref} {epic_title}".lower()

            # Get version info for separate columns
            current = get_current_version(item.get('versions', []))
            version_num = f"v{current.get('version', '?')}" if current else "—"
            version_status = current.get('status', 'unknown') if current else 'unknown'
            version_approved = current.get('approved', False) if current else False
            approval_badge = '<span class="status-badge" style="background-color: #059669">Yes</span>' if version_approved else '<span class="status-badge" style="background-color: #9ca3af">No</span>'

            html += (
                f'<tr data-filter-item="true" data-status="{e(status)}" data-epic="{e(epic_ref)}" data-search-text="{e(search_text_with_epic)}">'
                f'<td class="record-cell"><a href="{item_id}.html">{e(item_id)}</a>'
                f'{format_secondary(item_title)}</td>'
                f'<td class="summary-cell"><div class="cell-primary">{e(primary_summary)}</div>'
                f'{format_secondary(secondary_summary)}</td>'
                f'{epic_cell_html}'
                f'<td class="status-cell">{version_num}</td>'
                f'<td class="status-cell">{status_badge(status)}</td>'
                f'<td class="status-cell">{status_badge(version_status)}</td>'
                f'<td class="status-cell">{approval_badge}</td>'
                '</tr>'
            )
        else:
            html += (
                f'<tr data-filter-item="true" data-status="{e(status)}" data-search-text="{e(search_text)}">'
                f'<td class="record-cell"><a href="{item_id}.html">{e(item_id)}</a>'
                f'{format_secondary(item_title)}</td>'
                f'<td class="summary-cell"><div class="cell-primary">{e(primary_summary)}</div>'
                f'{format_secondary(secondary_summary)}</td>'
                f'<td class="status-cell"><div class="badge-stack">{"".join(status_badges)}</div></td>'
                '</tr>'
            )

    html += '</tbody></table>'

    # For stories with epic lookup, add drawer and enhanced JS
    if artifact_type.lower() == "stories" and epic_lookup:
        # Serialize epic data for JavaScript
        import json as json_module
        epic_data_json = json_module.dumps({
            ep_id: {
                'id': ep.get('id'),
                'title': ep.get('title'),
                'feature_ref': ep.get('feature_ref'),
                'versions': ep.get('versions', [])
            }
            for ep_id, ep in epic_lookup.items()
        })

        # Serialize stories data for the drawer table
        # Get current version status for each story
        def get_story_status(story):
            versions = story.get('versions', [])
            current = get_current_version(versions) if versions else None
            return current.get('status', 'unknown') if current else 'unknown'

        stories_data_json = json_module.dumps([
            {
                'id': story.get('id'),
                'title': story.get('title'),
                'epic_ref': story.get('epic_ref'),
                'status': get_story_status(story)
            }
            for story in items
        ])

        # Wrap content in layout container and add drawer
        drawer_html = f"""
<aside class="epic-drawer" id="epic-drawer" aria-hidden="true" aria-label="Epic details">
    <div class="epic-drawer-resize-handle" id="epic-drawer-resize-handle" aria-hidden="true"></div>
    <div class="epic-drawer-header">
        <div>
            <div class="epic-drawer-title" id="epic-drawer-title">Epic Details</div>
            <div class="epic-drawer-meta" id="epic-drawer-meta"></div>
        </div>
        <button class="button" id="epic-drawer-close" type="button">Close</button>
    </div>
    <div class="epic-drawer-body" id="epic-drawer-body">
        <p>Select an epic to view details.</p>
    </div>
</aside>
<div class="epic-drawer-backdrop" id="epic-drawer-backdrop"></div>
<script>
const epicData = {epic_data_json};
const storiesData = {stories_data_json};
</script>
"""

        stories_script = """
<script>
(() => {
    const searchInput = document.getElementById('search-input');
    const statusFilter = document.getElementById('status-filter');
    const epicDropdown = document.getElementById('epic-filter-dropdown');
    const epicTrigger = document.getElementById('epic-filter-trigger');
    const epicMenu = document.getElementById('epic-filter-menu');
    const epicSearch = document.getElementById('epic-filter-search');
    const epicList = document.getElementById('epic-filter-list');
    const items = Array.from(document.querySelectorAll('[data-filter-item]'));
    const countEl = document.getElementById('results-count');
    const storiesLayout = document.getElementById('stories-layout');
    const epicDrawer = document.getElementById('epic-drawer');
    const epicDrawerClose = document.getElementById('epic-drawer-close');
    const epicDrawerBackdrop = document.getElementById('epic-drawer-backdrop');
    const epicDrawerTitle = document.getElementById('epic-drawer-title');
    const epicDrawerMeta = document.getElementById('epic-drawer-meta');
    const epicDrawerBody = document.getElementById('epic-drawer-body');
    const resizeHandle = document.getElementById('epic-drawer-resize-handle');

    if (!searchInput || !statusFilter || !countEl) return;

    // Get selected epics from checkboxes
    function getSelectedEpics() {
        if (!epicList) return [];
        return Array.from(epicList.querySelectorAll('input[type="checkbox"]:checked')).map(input => input.value);
    }

    // Update trigger text
    function updateEpicTrigger() {
        if (!epicTrigger) return;
        const selected = getSelectedEpics();
        if (selected.length === 0) {
            epicTrigger.textContent = 'All epics';
        } else if (selected.length === 1) {
            epicTrigger.textContent = selected[0];
        } else {
            epicTrigger.textContent = `${selected.length} epics selected`;
        }
    }

    // Filter epic list items
    function filterEpicList(term) {
        if (!epicList) return;
        const normalized = (term || '').toLowerCase();
        Array.from(epicList.querySelectorAll('label')).forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = !normalized || text.includes(normalized) ? '' : 'none';
        });
    }

    function applyFilters() {
        const term = searchInput.value.trim().toLowerCase();
        const status = statusFilter.value.toLowerCase();
        const selectedEpics = new Set(getSelectedEpics());
        const filterByEpic = selectedEpics.size > 0;

        let visible = 0;
        items.forEach((item) => {
            const text = (item.dataset.searchText || '').toLowerCase();
            const itemStatus = (item.dataset.status || '').toLowerCase();
            const itemEpic = item.dataset.epic || '';

            const matchesTerm = !term || text.includes(term);
            const matchesStatus = status === 'all' || itemStatus === status;
            const matchesEpic = !filterByEpic || selectedEpics.has(itemEpic);

            const show = matchesTerm && matchesStatus && matchesEpic;
            item.style.display = show ? '' : 'none';
            if (show) visible += 1;
        });
        countEl.textContent = `${visible} of ${items.length} shown`;
        updateEpicTrigger();
    }

    // Epic dropdown toggle
    if (epicTrigger && epicDropdown) {
        epicTrigger.addEventListener('click', () => {
            const isOpen = epicDropdown.classList.contains('open');
            if (isOpen) {
                epicDropdown.classList.remove('open');
                epicTrigger.setAttribute('aria-expanded', 'false');
            } else {
                epicDropdown.classList.add('open');
                epicTrigger.setAttribute('aria-expanded', 'true');
                if (epicSearch) epicSearch.focus();
            }
        });

        // Close on outside click
        document.addEventListener('click', (event) => {
            if (!epicDropdown.contains(event.target)) {
                epicDropdown.classList.remove('open');
                epicTrigger.setAttribute('aria-expanded', 'false');
            }
        });

        // Close on Escape
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && epicDropdown.classList.contains('open')) {
                epicDropdown.classList.remove('open');
                epicTrigger.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // Epic filter search
    if (epicSearch) {
        epicSearch.addEventListener('input', () => {
            filterEpicList(epicSearch.value);
        });
    }

    // Epic filter checkbox changes
    if (epicList) {
        epicList.addEventListener('change', (event) => {
            if (event.target && event.target.matches('input[type="checkbox"]')) {
                applyFilters();
            }
        });
    }

    // Epic drawer functions
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function getCurrentVersion(versions) {
        if (!versions || versions.length === 0) return null;
        // Look for backlog version first (active work version)
        const backlog = versions.filter(v => v.status === 'backlog');
        if (backlog.length > 0) {
            return backlog.reduce((a, b) => (a.version > b.version ? a : b));
        }
        // Fall back to highest version number
        return versions.reduce((a, b) => (a.version > b.version ? a : b));
    }

    function getStatusColor(status) {
        const colors = {
            // Release statuses
            'planned': '#64748b',
            'released': '#16a34a',
            // Artifact lifecycle
            'active': '#16a34a',
            'deprecated': '#dc2626',
            'draft': '#94a3b8',
            'provisional': '#f59e0b',
            // Version statuses
            'backlog': '#2563eb',
            'discarded': '#9ca3af'
        };
        return colors[status] || '#9aa4b2';
    }

    function formatStatus(status) {
        return (status || 'unknown').replace(/_/g, ' ');
    }

    function getConnectedStories(epicId) {
        if (typeof storiesData === 'undefined') return [];
        return storiesData.filter(s => s.epic_ref === epicId);
    }

    function openEpicDrawer(epicId) {
        if (!storiesLayout || !epicDrawer || typeof epicData === 'undefined') return;
        const epic = epicData[epicId];
        if (!epic) return;

        const currentVersion = getCurrentVersion(epic.versions);

        // Update drawer title with link
        epicDrawerTitle.innerHTML = `<a href="../epics/${escapeHtml(epic.id)}.html">${escapeHtml(epic.id)}</a>: ${escapeHtml(epic.title)}`;

        // Update meta info
        if (epic.feature_ref) {
            epicDrawerMeta.innerHTML = `Feature: <a href="../features/${escapeHtml(epic.feature_ref)}.html">${escapeHtml(epic.feature_ref)}</a>`;
        } else {
            epicDrawerMeta.textContent = '';
        }

        // Build body content
        let bodyHtml = '';
        if (currentVersion) {
            const versionBadge = `<span class="status-badge" style="background-color: #2563eb">v${currentVersion.version}</span>`;
            bodyHtml += `
                <div class="epic-drawer-section">
                    <div class="epic-drawer-section-title">Current Version ${versionBadge}</div>
                    <div class="epic-drawer-summary">${escapeHtml(currentVersion.summary || 'No summary')}</div>
                </div>
            `;

            if (currentVersion.release_ref) {
                bodyHtml += `
                    <div class="epic-drawer-section">
                        <div class="epic-drawer-section-title">Release</div>
                        <div><a href="../releases/${escapeHtml(currentVersion.release_ref)}.html">${escapeHtml(currentVersion.release_ref)}</a></div>
                    </div>
                `;
            }

            if (currentVersion.assumptions && currentVersion.assumptions.length > 0) {
                bodyHtml += `
                    <div class="epic-drawer-section">
                        <div class="epic-drawer-section-title">Assumptions</div>
                        <ul>${currentVersion.assumptions.map(a => `<li>${escapeHtml(a)}</li>`).join('')}</ul>
                    </div>
                `;
            }

            if (currentVersion.constraints && currentVersion.constraints.length > 0) {
                bodyHtml += `
                    <div class="epic-drawer-section">
                        <div class="epic-drawer-section-title">Constraints</div>
                        <ul>${currentVersion.constraints.map(c => `<li>${escapeHtml(c)}</li>`).join('')}</ul>
                    </div>
                `;
            }
        } else {
            bodyHtml = '<p>No version information available.</p>';
        }

        // Add connected stories table
        const connectedStories = getConnectedStories(epicId);
        bodyHtml += `
            <div class="epic-drawer-section" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
                <div class="epic-drawer-section-title">Connected Stories (${connectedStories.length})</div>
                <div class="epic-stories-table-wrap">
                    <div class="epic-stories-table-scroll">
                        <table class="epic-stories-table">
                            <colgroup>
                                <col style="width: 25%;">
                                <col style="width: 50%;">
                                <col style="width: 25%;">
                            </colgroup>
                            <thead>
                                <tr>
                                    <th>Record</th>
                                    <th>Summary</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${connectedStories.length > 0 ? connectedStories.map(s => `
                                    <tr>
                                        <td class="story-id"><a href="./${escapeHtml(s.id)}.html">${escapeHtml(s.id)}</a></td>
                                        <td class="story-title">${escapeHtml(s.title)}</td>
                                        <td><span class="status-badge" style="background-color: ${getStatusColor(s.status)}">${formatStatus(s.status)}</span></td>
                                    </tr>
                                `).join('') : '<tr><td colspan="3" style="text-align: center; color: var(--text-muted); font-style: italic;">No stories in this epic</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        bodyHtml += `
            <div class="epic-drawer-section" style="padding-top: 0.5rem; border-top: 1px solid var(--border-color);">
                <a href="../epics/${escapeHtml(epic.id)}.html" class="button primary">View Full Epic</a>
            </div>
        `;

        epicDrawerBody.innerHTML = bodyHtml;

        currentOpenEpicId = epicId;
        storiesLayout.classList.add('drawer-open');
        epicDrawer.setAttribute('aria-hidden', 'false');
    }

    // Track currently open epic
    let currentOpenEpicId = null;

    function closeEpicDrawer() {
        if (!storiesLayout || !epicDrawer) return;
        currentOpenEpicId = null;
        storiesLayout.classList.remove('drawer-open');
        epicDrawer.setAttribute('aria-hidden', 'true');
    }

    function isDrawerOpen() {
        return storiesLayout && storiesLayout.classList.contains('drawer-open');
    }

    // Epic cell click handlers
    document.querySelectorAll('.epic-cell-link').forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const epicId = link.dataset.epicId;
            if (!epicId) return;

            if (isDrawerOpen() && currentOpenEpicId === epicId) {
                // Clicking the same epic that's open - close the drawer
                closeEpicDrawer();
            } else {
                // Clicking a different epic or drawer is closed - open/switch to this epic
                openEpicDrawer(epicId);
            }
        });
    });

    // Close button
    if (epicDrawerClose) {
        epicDrawerClose.addEventListener('click', closeEpicDrawer);
    }

    // Backdrop click
    if (epicDrawerBackdrop) {
        epicDrawerBackdrop.addEventListener('click', closeEpicDrawer);
    }

    // Escape key for drawer
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && storiesLayout && storiesLayout.classList.contains('drawer-open')) {
            closeEpicDrawer();
        }
    });

    // Resize handle
    if (resizeHandle && storiesLayout) {
        let isResizing = false;
        let startX = 0;
        let startWidth = 450;

        function startResize(e) {
            if (window.innerWidth <= 900) return;
            e.stopPropagation();
            e.preventDefault();
            isResizing = true;
            startX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
            startWidth = parseInt(getComputedStyle(storiesLayout).getPropertyValue('--epic-drawer-width')) || 450;
            resizeHandle.classList.add('resizing');
            document.body.style.cursor = 'ew-resize';
            document.body.style.userSelect = 'none';
            document.body.style.pointerEvents = 'none';
            resizeHandle.style.pointerEvents = 'auto';
        }

        function doResize(e) {
            if (!isResizing) return;
            e.stopPropagation();
            e.preventDefault();
            const currentX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
            const diff = startX - currentX;
            const minWidth = 300;
            const maxWidth = Math.max(600, Math.floor(window.innerWidth * 0.5));
            const newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth + diff));
            storiesLayout.style.setProperty('--epic-drawer-width', `${newWidth}px`);
        }

        function stopResize(e) {
            if (!isResizing) return;
            e.stopPropagation();
            isResizing = false;
            resizeHandle.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            document.body.style.pointerEvents = '';
            resizeHandle.style.pointerEvents = '';
        }

        resizeHandle.addEventListener('mousedown', startResize);
        resizeHandle.addEventListener('touchstart', startResize, { passive: false });
        window.addEventListener('mousemove', doResize, { passive: false });
        window.addEventListener('touchmove', doResize, { passive: false });
        window.addEventListener('mouseup', stopResize);
        window.addEventListener('touchend', stopResize);
        window.addEventListener('mouseleave', stopResize);
    }

    searchInput.addEventListener('input', applyFilters);
    statusFilter.addEventListener('change', applyFilters);
    applyFilters();
})();
</script>
"""
        # Wrap content for stories layout (includes breadcrumb container since custom_main=True skips it)
        breadcrumb_html = '<nav id="breadcrumb-nav" class="breadcrumb-nav" aria-label="Breadcrumb"></nav>'
        html = f'<div class="stories-layout" id="stories-layout"><div class="stories-content">{breadcrumb_html}{html}</div>{drawer_html}</div>{stories_script}'
        return html_page(title, html, artifact_type.lower(), depth=1, custom_main=True)

    # Default script for non-stories
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


def render_domain_entry(
    entry: Dict,
    features: List[Dict],
    epics: List[Dict],
    stories: List[Dict],
    requirements: List[Dict],
    requirement_lookup: Optional[Dict[str, Dict]] = None,
) -> str:
    """Render a single business artifact entry as HTML."""
    dom_type = entry.get('type', 'unknown')
    if isinstance(dom_type, list):
        dom_type = dom_type[0] if dom_type else "unknown"
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

    artifact_id = entry.get("id")
    feature_rows = build_feature_rows(
        [feat for feat in features if artifact_id in (feat.get("domain_refs") or [])],
        "../features/",
    )
    epic_rows = build_epic_rows(
        [
            epic
            for epic in epics
            if artifact_id in ((get_current_version(epic.get("versions", [])) or {}).get("domain_refs", []))
        ],
        "../epics/",
        "../releases/",
    )
    story_rows = build_story_rows(
        [
            story
            for story in stories
            if artifact_id in ((get_current_version(story.get("versions", [])) or {}).get("domain_refs", []))
        ],
        "../stories/",
        "../releases/",
    )
    requirement_rows = build_requirement_rows(
        [req.get("id") for req in requirements if artifact_id in (req.get("domain_refs") or [])],
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
    return html_page(f"{entry['id']}: {entry.get('title', '')}", html, "domain", depth=1)


def render_domain_index(domain_entries: List[Dict]) -> str:
    """Render a business artifacts index page listing all domain entries."""
    html = '<h1>Business Artifacts</h1>\n'
    html += '<p>Business artifacts, policies, rules, and reference documentation.</p>\n'

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

    html += '<table class="index-table"><thead><tr><th>Record</th><th>Summary</th><th>Type</th><th>Status</th></tr></thead><tbody>'

    for item in sorted(domain_entries, key=lambda x: x.get('id', '')):
        dom_type = item.get('type', 'unknown')
        if isinstance(dom_type, list):
            dom_type = dom_type[0] if dom_type else "unknown"
        status = item.get("status") or "unknown"
        description = item.get("description") or "Domain reference document"
        source = item.get("source", "unknown")
        effective = item.get("effective_date")
        secondary = f"Source: {source}"
        if effective:
            secondary += f" | Effective: {effective}"

        search_text = " ".join(
            part
            for part in [
                item.get("id"),
                item.get("title"),
                description,
                dom_type,
                status,
                source,
                effective,
            ]
            if part
        ).lower()

        html += (
            f'<tr data-filter-item="true" data-status="{e(status)}" data-search-text="{e(search_text)}">'
            f'<td class="record-cell"><a href="{item["id"]}.html">{e(item["id"])}</a>'
            f'{format_secondary(item.get("title", ""))}</td>'
            f'<td class="summary-cell"><div class="cell-primary">{e(description)}</div>'
            f'{format_secondary(secondary)}</td>'
            f'<td class="status-cell"><div class="badge-stack">{artifact_type_badge(dom_type)}</div></td>'
            f'<td class="status-cell"><div class="badge-stack">{status_badge(status)}</div></td>'
            '</tr>'
        )

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

    return html_page("Domain", html, "domain", depth=1)


def render_index_redirect() -> str:
    """Render a simple redirect page that sends users to the Story Map."""
    return REDIRECT_HTML


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
        content = render_domain_entry(
            entry,
            features,
            epics,
            stories,
            requirements,
            requirement_lookup=requirement_lookup,
        )
        (domain_dir / f"{entry['id']}.html").write_text(content, encoding="utf-8")
        counts["domain"] += 1
    domain_index = render_domain_index(domain)
    (domain_dir / "index.html").write_text(domain_index, encoding="utf-8")

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
            artifact_lookup=domain_lookup,
        )
        (OUTPUT_DIRS["requirements"] / f"{req['id']}.html").write_text(content, encoding="utf-8")
        counts["requirements"] += 1

    index_content = render_index("requirements", requirements, "Requirements", domain_lookup=domain_lookup)
    (OUTPUT_DIRS["requirements"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render features
    for feat in features:
        content = render_feature(
            feat,
            epics,
            stories,
            requirement_lookup=requirement_lookup,
            artifact_lookup=domain_lookup,
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
            artifact_lookup=domain_lookup,
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
            artifact_lookup=domain_lookup,
        )
        (OUTPUT_DIRS["stories"] / f"{story['id']}.html").write_text(content, encoding="utf-8")
        counts["stories"] += 1

    epic_lookup = {ep['id']: ep for ep in epics}
    index_content = render_index("stories", stories, "Stories", epic_lookup=epic_lookup)
    (OUTPUT_DIRS["stories"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render index.html as redirect to Story Map
    index_redirect = render_index_redirect()
    (DOCS_DIR / "index.html").write_text(index_redirect, encoding="utf-8")

    # Update story-map.html navbar and add breadcrumb support
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

        # Add breadcrumb CSS if not already present
        if '.breadcrumb-current' not in story_map_content:
            # Insert CSS before closing </style> tag (check for .breadcrumb-current to ensure full CSS is present)
            story_map_content = story_map_content.replace('</style>', BREADCRUMB_CSS + '</style>', 1)

        # Add breadcrumb container if not present
        breadcrumb_container = '<nav id="breadcrumb-nav" class="breadcrumb-nav" aria-label="Breadcrumb"></nav>'
        if 'id="breadcrumb-nav"' not in story_map_content:
            # Insert after </header> and before the stats-bar
            story_map_content = re.sub(
                r'(</header>\s*)',
                r'\1\n    ' + breadcrumb_container + '\n',
                story_map_content,
                count=1
            )

        # Add breadcrumb JavaScript if not present
        if 'BreadcrumbNav' not in story_map_content:
            # Insert before closing </body> tag
            story_map_content = story_map_content.replace('</body>', BREADCRUMB_JS + '</body>')

        # Add version detection features
        build_version = get_build_version()

        # Add version meta tag if not present
        if 'name="apsca-version"' not in story_map_content:
            story_map_content = re.sub(
                r'(<meta name="viewport"[^>]*>)',
                r'\1\n    <meta name="apsca-version" content="">',
                story_map_content,
                count=1
            )

        # Update version meta tag content
        story_map_content = re.sub(
            r'<meta name="apsca-version" content="[^"]*">',
            f'<meta name="apsca-version" content="{build_version}">',
            story_map_content
        )

        # Add version banner CSS if not present
        if '.version-banner {' not in story_map_content:
            story_map_content = story_map_content.replace('</style>', VERSION_BANNER_CSS + '</style>', 1)

        # Add version banner HTML if not present
        if 'id="version-banner"' not in story_map_content:
            story_map_content = re.sub(
                r'(<body>)',
                r'\1\n    ' + VERSION_BANNER_HTML,
                story_map_content,
                count=1
            )

        # Add version check JavaScript if not present
        if 'VersionCheck' not in story_map_content:
            story_map_content = story_map_content.replace('</body>', VERSION_CHECK_JS + '</body>')

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
