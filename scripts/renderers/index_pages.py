"""Render index and redirect pages."""

from typing import Dict, List, Optional

from lib.assets import REDIRECT_HTML
from lib.html_helpers import (
    artifact_type_badge,
    e,
    format_secondary,
    format_status_label,
    html_page,
    status_badge,
)
from lib.versions import get_current_version


def render_index(
    artifact_type: str,
    items: List[Dict],
    title: str,
    domain_lookup: Dict[str, Dict] = None,
    epic_lookup: Dict[str, Dict] = None,
) -> str:
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

    # For stories and epics, use explicit status labels and default to active
    if artifact_type.lower() == "stories":
        status_filter_label = "User Story Status"
        status_filter_default = "active"
    elif artifact_type.lower() == "epics":
        status_filter_label = "Epic Status"
        status_filter_default = "all"
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
    elif artifact_type.lower() == "epics":
        html += '<table class="index-table"><thead><tr><th>Record</th><th>Summary</th><th>Version</th><th>Epic Status</th><th>Version Status</th><th>Version Approval</th></tr></thead><tbody>'
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
            approval_badge = '<span class="status-badge" style="background-color: #059669">Approved</span>' if version_approved else '<span class="status-badge" style="background-color: #9ca3af">Pending Approval</span>'

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
        elif artifact_type.lower() == "epics":
            current = get_current_version(item.get('versions', []))
            version_num = f"v{current.get('version', '?')}" if current else "—"
            version_status = current.get('status', 'unknown') if current else 'unknown'
            version_approved = current.get('approved', False) if current else False
            approval_badge = '<span class="status-badge" style="background-color: #059669">Approved</span>' if version_approved else '<span class="status-badge" style="background-color: #9ca3af">Pending Approval</span>'

            html += (
                f'<tr data-filter-item="true" data-status="{e(status)}" data-search-text="{e(search_text)}">'
                f'<td class="record-cell"><a href="{item_id}.html">{e(item_id)}</a>'
                f'{format_secondary(item_title)}</td>'
                f'<td class="summary-cell"><div class="cell-primary">{e(primary_summary)}</div>'
                f'{format_secondary(secondary_summary)}</td>'
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
