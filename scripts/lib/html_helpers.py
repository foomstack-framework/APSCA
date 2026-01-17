"""Shared HTML helpers for documentation rendering."""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path
from typing import Dict, List, Optional

from lib.assets import CSS, TOPBAR_CSS, VERSION_BANNER_HTML
from lib.config import DOCS_DIR
from lib.versions import get_current_version

# Version file path
VERSION_FILE = DOCS_DIR / "version.json"

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
_TEMPLATE_CACHE: Dict[str, str] = {}


def get_build_version() -> str:
    """Get the build version from version.json, or empty string if not available."""
    try:
        if VERSION_FILE.exists():
            version_data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
            return version_data.get("commit", "")
    except (json.JSONDecodeError, IOError):
        pass
    return ""


# =============================================================================
# HTML Helpers
# =============================================================================

def e(text: str) -> str:
    """Escape HTML entities."""
    return escape(str(text)) if text else ""


def load_template(name: str) -> str:
    """Load and cache an HTML template by filename."""
    if name in _TEMPLATE_CACHE:
        return _TEMPLATE_CACHE[name]
    template_path = TEMPLATES_DIR / name
    content = template_path.read_text(encoding="utf-8")
    _TEMPLATE_CACHE[name] = content
    return content


def render_template(name: str, replacements: Dict[str, str]) -> str:
    """Render a template by replacing <!--TOKEN--> placeholders."""
    content = load_template(name)
    for key, value in replacements.items():
        placeholder = f"<!--{key}-->"
        if placeholder not in content:
            raise ValueError(f"Missing placeholder {placeholder} in template {name}")
        content = content.replace(placeholder, value, 1)
    return content


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

    version_banner = VERSION_BANNER_HTML

    if custom_main:
        main_section = content
    else:
        main_section = f"<main>\n        {breadcrumb_html}\n        {content}\n    </main>"

    page_scripts = f"""<script>
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
        const DEBUG_PREFIX = '[VersionCheck]';

        function log(...args) {{
            console.debug(DEBUG_PREFIX, ...args);
        }}

        function getPageVersion() {{
            const meta = document.querySelector('meta[name=\"apsca-version\"]');
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
                log('Stored dismissed version:', version.substring(0, 7));
            }} catch (e) {{
                log('Failed to store dismissed version:', e);
            }}
        }}

        function showBanner() {{
            const banner = document.getElementById('version-banner');
            if (banner) {{
                banner.classList.remove('hidden');
                document.body.classList.add('has-version-banner');
                log('Banner shown');
                // Update keyboard shortcut for Mac
                if (navigator.platform.indexOf('Mac') !== -1) {{
                    const kbd = banner.querySelector('.version-banner-kbd');
                    if (kbd) kbd.textContent = 'Cmd+Shift+R';
                }}
            }}
        }}

        async function checkVersion() {{
            const pageVersion = getPageVersion();
            log('Check started - Page version:', pageVersion ? pageVersion.substring(0, 7) : '(none)');

            if (!pageVersion) {{
                log('No page version found, skipping check');
                return;
            }}

            try {{
                const response = await fetch(VERSION_URL + '?t=' + Date.now());
                if (!response.ok) {{
                    log('Fetch failed with status:', response.status);
                    return;
                }}
                const data = await response.json();
                const serverVersion = data.commit || '';
                const dismissed = getDismissedVersion();

                log('Server version:', serverVersion ? serverVersion.substring(0, 7) : '(none)');
                log('Dismissed version:', dismissed ? dismissed.substring(0, 7) : '(none)');

                if (serverVersion && serverVersion !== pageVersion) {{
                    log('Version mismatch detected');
                    if (dismissed !== serverVersion) {{
                        log('Server version not dismissed, showing banner');
                        showBanner();
                    }} else {{
                        log('Server version already dismissed, hiding banner');
                    }}
                }} else {{
                    log('Versions match, no banner needed');
                }}
            }} catch (e) {{
                log('Check failed:', e.message || e);
            }}
        }}

        // Global function for dismiss button
        window.dismissVersionBanner = function() {{
            log('Dismiss button clicked');
            const banner = document.getElementById('version-banner');
            if (banner) {{
                banner.classList.add('hidden');
                document.body.classList.remove('has-version-banner');
            }}
            // Get server version to store as dismissed
            fetch(VERSION_URL + '?t=' + Date.now())
                .then(r => r.json())
                .then(data => {{
                    if (data.commit) {{
                        log('Dismissing version:', data.commit.substring(0, 7));
                        setDismissedVersion(data.commit);
                    }}
                }})
                .catch((e) => {{
                    log('Failed to fetch version for dismiss:', e);
                }});
        }};

        // Global function for refresh button - dismiss then refresh
        window.refreshWithDismiss = async function() {{
            log('Refresh button clicked');
            try {{
                // Fetch server version and store as dismissed before refreshing
                const response = await fetch(VERSION_URL + '?t=' + Date.now());
                if (response.ok) {{
                    const data = await response.json();
                    if (data.commit) {{
                        log('Dismissing version before refresh:', data.commit.substring(0, 7));
                        setDismissedVersion(data.commit);
                    }}
                }}
            }} catch (e) {{
                log('Failed to dismiss before refresh:', e);
            }}
            log('Refreshing page...');
            // Refresh with cache-busting query param
            location.href = location.pathname + '?refresh=' + Date.now();
        }};

        // Run check after page loads
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', checkVersion);
        }} else {{
            checkVersion();
        }}

        return {{ checkVersion }};
    }})();
    </script>"""

    return render_template(
        "page.html",
        {
            "BUILD_VERSION": e(build_version),
            "TITLE": e(title),
            "CSS": TOPBAR_CSS + CSS,
            "VERSION_BANNER": version_banner,
            "NAVBAR": nav_html,
            "MAIN": main_section,
            "SCRIPTS": page_scripts,
        },
    )
