"""Render release pages."""

from typing import Dict, List

from lib.html_helpers import (
    e,
    format_secondary,
    html_page,
    render_connected_table,
    render_summary_cell,
    render_tabs,
    status_badge,
)


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
            "id": "epic-versions",
            "label": "Epic Versions",
            "content": render_connected_table(["Epic", "Version", "Summary"], epic_rows, "Epic Versions"),
        },
        {
            "id": "story-versions",
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
