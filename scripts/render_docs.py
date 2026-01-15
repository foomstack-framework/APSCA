#!/usr/bin/env python3
"""
render_docs.py - Generate static HTML documentation for APSCA requirements repository.

Generates HTML files in docs/ from canonical JSON data.
Note: docs/domain/ contains authored content and is NOT overwritten.

Usage:
    python scripts/render_docs.py
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from html import escape

# Root directory
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"
REPORTS_DIR = ROOT_DIR / "reports"

# Data files
DATA_FILES = {
    "releases": DATA_DIR / "releases.json",
    "domain": DATA_DIR / "domain.json",
    "requirements": DATA_DIR / "requirements.json",
    "features": DATA_DIR / "features.json",
    "epics": DATA_DIR / "epics.json",
    "stories": DATA_DIR / "stories.json",
}

# Output directories (NOT domain/ - that's authored content)
OUTPUT_DIRS = {
    "releases": DOCS_DIR / "releases",
    "requirements": DOCS_DIR / "requirements",
    "features": DOCS_DIR / "features",
    "epics": DOCS_DIR / "epics",
    "stories": DOCS_DIR / "stories",
}


def load_json(file_path: Path) -> List[Dict]:
    """Load JSON array from file."""
    if not file_path.exists():
        return []
    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return json.loads(content)


def get_current_version(versions: List[Dict]) -> Optional[Dict]:
    """Get the current (non-superseded) version from a versions list."""
    if not versions:
        return None
    active_versions = [v for v in versions if v.get("status") != "superseded"]
    if active_versions:
        return max(active_versions, key=lambda v: v.get("version", 0))
    return max(versions, key=lambda v: v.get("version", 0))


# =============================================================================
# HTML Helpers
# =============================================================================

def e(text: str) -> str:
    """Escape HTML entities."""
    return escape(str(text)) if text else ""


def status_badge(status: str) -> str:
    """Generate status badge HTML."""
    colors = {
        "planned": "#6b7280",
        "released": "#10b981",
        "superseded": "#9ca3af",
        "active": "#10b981",
        "deprecated": "#ef4444",
        "draft": "#f59e0b",
        "approved": "#3b82f6",
        "ready_to_build": "#8b5cf6",
        "in_build": "#ec4899",
        "built": "#10b981",
    }
    color = colors.get(status, "#6b7280")
    return f'<span class="status-badge" style="background-color: {color}">{e(status)}</span>'


def link(href: str, text: str) -> str:
    """Generate a link."""
    return f'<a href="{e(href)}">{e(text)}</a>'


def format_refs_html(refs: List[str], prefix: str = "") -> str:
    """Format a list of references as HTML links."""
    if not refs:
        return "<em>None</em>"
    links = [f'<a href="{prefix}{ref}.html">{e(ref)}</a>' for ref in refs]
    return ", ".join(links)


# =============================================================================
# HTML Layout
# =============================================================================

CSS = """
:root {
    --bg-primary: #f8fafc;
    --bg-secondary: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
    --accent-color: #3b82f6;
    --nav-width: 220px;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
}

.layout {
    display: flex;
    min-height: 100vh;
}

nav {
    width: var(--nav-width);
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    padding: 1.5rem 1rem;
    position: fixed;
    height: 100vh;
    overflow-y: auto;
}

nav h2 {
    font-size: 1rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

nav ul {
    list-style: none;
    margin-bottom: 1.5rem;
}

nav a {
    display: block;
    padding: 0.4rem 0.75rem;
    color: var(--text-primary);
    text-decoration: none;
    border-radius: 4px;
    font-size: 0.9rem;
}

nav a:hover, nav a.active {
    background: var(--bg-primary);
    color: var(--accent-color);
}

nav .brand {
    font-weight: 700;
    font-size: 1.1rem;
    color: var(--accent-color);
    margin-bottom: 1.5rem;
    display: block;
    text-decoration: none;
}

main {
    margin-left: var(--nav-width);
    flex: 1;
    padding: 2rem 3rem;
    max-width: 900px;
}

h1 {
    font-size: 1.75rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

h2 {
    font-size: 1.25rem;
    margin: 1.5rem 0 0.75rem;
    color: var(--text-primary);
}

h3 {
    font-size: 1rem;
    margin: 1rem 0 0.5rem;
    color: var(--text-secondary);
}

p, ul, ol {
    margin-bottom: 1rem;
}

ul, ol {
    padding-left: 1.5rem;
}

a {
    color: var(--accent-color);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

.meta {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
}

.meta strong {
    color: var(--text-primary);
}

.status-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    background: var(--bg-secondary);
    border-radius: 8px;
    overflow: hidden;
}

th, td {
    text-align: left;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-color);
}

th {
    background: var(--bg-primary);
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    color: var(--text-secondary);
}

tr:last-child td {
    border-bottom: none;
}

tr:hover {
    background: var(--bg-primary);
}

.section {
    margin: 1.5rem 0;
}

code {
    background: var(--bg-primary);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-size: 0.9em;
}
"""


def html_page(title: str, content: str, active_section: str = "", depth: int = 1) -> str:
    """Wrap content in full HTML page with navigation."""
    prefix = "../" * depth

    nav_items = [
        ("", "Dashboard", "index.html"),
        ("", "Story Map", "story-map.html"),
        ("features", "Features", "features/index.html"),
        ("epics", "Epics", "epics/index.html"),
        ("stories", "Stories", "stories/index.html"),
        ("requirements", "Requirements", "requirements/index.html"),
        ("releases", "Releases", "releases/index.html"),
    ]

    nav_html = f'<a class="brand" href="{prefix}index.html">APSCA</a>\n'
    nav_html += '<ul>\n'
    for section, label, href in nav_items:
        active_class = ' class="active"' if section == active_section else ""
        nav_html += f'    <li><a href="{prefix}{href}"{active_class}>{label}</a></li>\n'
    nav_html += '</ul>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{e(title)} - APSCA</title>
    <style>{CSS}</style>
</head>
<body>
    <div class="layout">
        <nav>
            {nav_html}
        </nav>
        <main>
            {content}
        </main>
    </div>
</body>
</html>
"""


# =============================================================================
# Render Functions
# =============================================================================

def render_release(release: Dict) -> str:
    """Render a release as HTML."""
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


def render_feature(feat: Dict) -> str:
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
    <p>{format_refs_html(feat['requirement_refs'], '../requirements/')}</p>
</div>
"""
    return html_page(f"{feat['id']}: {feat.get('title', '')}", html, "features", depth=1)


def render_epic(epic: Dict) -> str:
    """Render an epic as HTML."""
    current = get_current_version(epic.get('versions', []))

    html = f"""
<h1>{e(epic['id'])}: {e(epic.get('title', ''))}</h1>
"""
    if current:
        html += f"""
<div class="meta">
    <strong>Version:</strong> {current.get('version')} {status_badge(current.get('status', 'unknown'))} &nbsp;
    <strong>Release:</strong> <a href="../releases/{current.get('release_ref')}.html">{e(current.get('release_ref'))}</a>
</div>
<div class="section">
    <h2>Summary</h2>
    <p>{e(current.get('summary', 'No summary'))}</p>
</div>
"""
        if current.get('assumptions'):
            html += '<div class="section"><h2>Assumptions</h2><ul>'
            for item in current['assumptions']:
                html += f'<li>{e(item)}</li>'
            html += '</ul></div>'

        if current.get('constraints'):
            html += '<div class="section"><h2>Constraints</h2><ul>'
            for item in current['constraints']:
                html += f'<li>{e(item)}</li>'
            html += '</ul></div>'

    if epic.get('feature_ref'):
        html += f"""
<div class="section">
    <h2>Feature</h2>
    <p>Part of <a href="../features/{epic['feature_ref']}.html">{e(epic['feature_ref'])}</a></p>
</div>
"""

    versions = epic.get('versions', [])
    if len(versions) > 1:
        html += '<div class="section"><h2>Version History</h2><table><thead><tr><th>Version</th><th>Status</th><th>Release</th></tr></thead><tbody>'
        for v in sorted(versions, key=lambda x: x.get('version', 0), reverse=True):
            html += f'<tr><td>{v.get("version")}</td><td>{v.get("status")}</td><td>{v.get("release_ref")}</td></tr>'
        html += '</tbody></table></div>'

    return html_page(f"{epic['id']}: {epic.get('title', '')}", html, "epics", depth=1)


def render_story(story: Dict) -> str:
    """Render a story as HTML."""
    current = get_current_version(story.get('versions', []))

    html = f"""
<h1>{e(story['id'])}: {e(story.get('title', ''))}</h1>
"""
    if current:
        html += f"""
<div class="meta">
    <strong>Version:</strong> {current.get('version')} {status_badge(current.get('status', 'unknown'))} &nbsp;
    <strong>Release:</strong> <a href="../releases/{current.get('release_ref')}.html">{e(current.get('release_ref'))}</a>
</div>
<div class="section">
    <h2>Description</h2>
    <p>{e(current.get('description', 'No description'))}</p>
</div>
"""
        # Acceptance Criteria
        ac = current.get('acceptance_criteria', [])
        if ac:
            html += '<div class="section"><h2>Acceptance Criteria</h2><ul>'
            for criterion in ac:
                html += f'<li><strong>{e(criterion.get("id", "AC"))}:</strong> {e(criterion.get("statement", ""))}'
                if criterion.get('notes'):
                    html += f' <em>({e(criterion["notes"])})</em>'
                html += '</li>'
            html += '</ul></div>'

        # Test Intent
        ti = current.get('test_intent', {})
        if ti.get('failure_modes') or ti.get('guarantees'):
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

    if story.get('epic_ref'):
        html += f"""
<div class="section">
    <h2>Epic</h2>
    <p>Part of <a href="../epics/{story['epic_ref']}.html">{e(story['epic_ref'])}</a></p>
</div>
"""

    versions = story.get('versions', [])
    if len(versions) > 1:
        html += '<div class="section"><h2>Version History</h2><table><thead><tr><th>Version</th><th>Status</th><th>Release</th></tr></thead><tbody>'
        for v in sorted(versions, key=lambda x: x.get('version', 0), reverse=True):
            html += f'<tr><td>{v.get("version")}</td><td>{v.get("status")}</td><td>{v.get("release_ref")}</td></tr>'
        html += '</tbody></table></div>'

    return html_page(f"{story['id']}: {story.get('title', '')}", html, "stories", depth=1)


def render_index(artifact_type: str, items: List[Dict], title: str) -> str:
    """Render an index page for a collection."""
    html = f'<h1>{e(title)}</h1>\n'

    if not items:
        html += '<p><em>No items yet.</em></p>'
        return html_page(title, html, artifact_type.lower(), depth=1)

    html += '<table><thead><tr><th>ID</th><th>Title</th><th>Status</th></tr></thead><tbody>'

    for item in sorted(items, key=lambda x: x.get('id', '')):
        item_id = item['id']
        item_title = item.get('title', item_id)
        status = item.get('status', 'unknown')
        if 'versions' in item:
            current = get_current_version(item.get('versions', []))
            status = current.get('status', 'unknown') if current else 'unknown'

        html += f'<tr><td><a href="{item_id}.html">{e(item_id)}</a></td><td>{e(item_title)}</td><td>{status_badge(status)}</td></tr>'

    html += '</tbody></table>'

    return html_page(title, html, artifact_type.lower(), depth=1)


def render_landing_page(counts: Dict[str, int]) -> str:
    """Render the main landing page."""
    html = """
<h1>APSCA Requirements Dashboard</h1>
<p>System of record for requirements, features, epics, and user stories.</p>

<div class="section">
    <h2>Quick Links</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
        <a href="story-map.html" class="card" style="text-decoration: none; color: inherit;">
            <h3 style="margin: 0 0 0.5rem;">Story Map</h3>
            <p style="margin: 0; color: var(--text-secondary);">Visual hierarchy of features, epics, and stories</p>
        </a>
        <a href="features/index.html" class="card" style="text-decoration: none; color: inherit;">
            <h3 style="margin: 0 0 0.5rem;">Features</h3>
            <p style="margin: 0; color: var(--text-secondary);">Top-level capability boundaries</p>
        </a>
        <a href="releases/index.html" class="card" style="text-decoration: none; color: inherit;">
            <h3 style="margin: 0 0 0.5rem;">Releases</h3>
            <p style="margin: 0; color: var(--text-secondary);">Delivery timeline events</p>
        </a>
    </div>
</div>

<div class="section">
    <h2>Artifact Counts</h2>
    <table>
        <thead><tr><th>Type</th><th>Count</th></tr></thead>
        <tbody>
"""
    for key, count in counts.items():
        html += f'<tr><td>{key.title()}</td><td>{count}</td></tr>'

    html += """
        </tbody>
    </table>
</div>

<div class="section">
    <h2>How It Works</h2>
    <p>This repository stores structured requirements as canonical JSON. Documentation is auto-generated from this data.</p>
    <p><strong>Hierarchy:</strong> Requirements → Features → Epics → Stories → Acceptance Criteria</p>
</div>
"""
    return html_page("Dashboard", html, "", depth=0)


def main():
    # Load all data
    releases = load_json(DATA_FILES["releases"])
    requirements = load_json(DATA_FILES["requirements"])
    features = load_json(DATA_FILES["features"])
    epics = load_json(DATA_FILES["epics"])
    stories = load_json(DATA_FILES["stories"])

    # Ensure output directories exist
    for output_dir in OUTPUT_DIRS.values():
        output_dir.mkdir(parents=True, exist_ok=True)

    counts = {"releases": 0, "requirements": 0, "features": 0, "epics": 0, "stories": 0}

    # Render releases
    for release in releases:
        content = render_release(release)
        (OUTPUT_DIRS["releases"] / f"{release['id']}.html").write_text(content, encoding="utf-8")
        counts["releases"] += 1

    index_content = render_index("releases", releases, "Releases")
    (OUTPUT_DIRS["releases"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render requirements
    for req in requirements:
        content = render_requirement(req)
        (OUTPUT_DIRS["requirements"] / f"{req['id']}.html").write_text(content, encoding="utf-8")
        counts["requirements"] += 1

    index_content = render_index("requirements", requirements, "Requirements")
    (OUTPUT_DIRS["requirements"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render features
    for feat in features:
        content = render_feature(feat)
        (OUTPUT_DIRS["features"] / f"{feat['id']}.html").write_text(content, encoding="utf-8")
        counts["features"] += 1

    index_content = render_index("features", features, "Features")
    (OUTPUT_DIRS["features"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render epics
    for epic in epics:
        content = render_epic(epic)
        (OUTPUT_DIRS["epics"] / f"{epic['id']}.html").write_text(content, encoding="utf-8")
        counts["epics"] += 1

    index_content = render_index("epics", epics, "Epics")
    (OUTPUT_DIRS["epics"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render stories
    for story in stories:
        content = render_story(story)
        (OUTPUT_DIRS["stories"] / f"{story['id']}.html").write_text(content, encoding="utf-8")
        counts["stories"] += 1

    index_content = render_index("stories", stories, "Stories")
    (OUTPUT_DIRS["stories"] / "index.html").write_text(index_content, encoding="utf-8")

    # Render landing page
    landing = render_landing_page(counts)
    (DOCS_DIR / "index.html").write_text(landing, encoding="utf-8")

    # Copy data and reports to docs for local testing and story map access
    import shutil
    docs_data = DOCS_DIR / "data"
    docs_reports = DOCS_DIR / "reports"
    docs_data.mkdir(exist_ok=True)
    docs_reports.mkdir(exist_ok=True)

    for json_file in DATA_DIR.glob("*.json"):
        shutil.copy(json_file, docs_data / json_file.name)

    for json_file in REPORTS_DIR.glob("*.json"):
        shutil.copy(json_file, docs_reports / json_file.name)

    print("Documentation generated:")
    for key, count in counts.items():
        print(f"  {key}: {count} files")
    print(f"  Landing page: index.html")


if __name__ == "__main__":
    main()
