"""Render the Definitions page with canonical artifact type definitions."""

from lib.html_helpers import html_page

# Color scheme for artifact types
ARTIFACT_COLORS = {
    "feature": "#8b5cf6",      # Purple
    "epic": "#2563eb",         # Blue
    "requirement": "#f59e0b",  # Amber
    "artifact": "#10b981",     # Emerald
    "story": "#16a34a",        # Green
    "release": "#64748b",      # Slate
}

DEFINITIONS_CSS = """
<style>
/* Definitions Page - Compact Print-Friendly Layout */
.definitions-page {
    max-width: 900px;
    margin: 0 auto;
}

.definitions-header {
    text-align: center;
    margin-bottom: 0.6rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid var(--border-color);
}

.definitions-header h1 {
    font-size: 1.25rem;
    margin-bottom: 0.15rem;
}

.definitions-header p {
    font-size: 0.78rem;
    color: var(--text-secondary);
    margin: 0;
}

/* 2-column grid for definition cards */
.definitions-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin-bottom: 0.6rem;
}

.definition-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    overflow: hidden;
    font-size: 0.74rem;
    page-break-inside: avoid;
}

.definition-card-header {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.definition-card-icon {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.7rem;
    color: white;
    flex-shrink: 0;
}

.definition-card-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}

.definition-card-subtitle {
    font-size: 0.65rem;
    color: var(--text-muted);
}

.definition-card-body {
    padding: 0.4rem 0.5rem;
}

.definition-row {
    margin-bottom: 0.25rem;
}

.definition-row:last-child {
    margin-bottom: 0;
}

.definition-row-label {
    font-size: 0.58rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    margin-bottom: 0.05rem;
}

.definition-row-value {
    font-size: 0.74rem;
    color: var(--text-primary);
    line-height: 1.3;
}

.definition-props {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem;
    margin: 0;
    padding: 0;
    list-style: none;
}

.definition-props li {
    background: var(--bg-primary);
    padding: 0.12rem 0.32rem;
    border-radius: 3px;
    font-size: 0.64rem;
    color: var(--text-secondary);
}

.definition-props code {
    font-size: 0.58rem;
    background: transparent;
    padding: 0;
}

.definition-examples {
    font-size: 0.66rem;
    color: var(--text-muted);
    font-style: italic;
}

/* Bottom sections - side by side */
.definitions-footer {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
}

.footer-section {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    overflow: hidden;
    page-break-inside: avoid;
}

.footer-section-header {
    padding: 0.25rem 0.5rem;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-muted);
}

.footer-section-header h2 {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}

.footer-section-body {
    padding: 0.4rem 0.5rem;
}

/* Boundary table */
.boundary-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.7rem;
}

.boundary-table th,
.boundary-table td {
    padding: 0.22rem 0.4rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.boundary-table th {
    font-size: 0.58rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    font-weight: 600;
}

.boundary-table tbody tr:last-child td {
    border-bottom: none;
}

.boundary-table td:first-child {
    color: var(--text-secondary);
}

.boundary-table td:last-child {
    font-weight: 600;
}

.type-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 0.25rem;
    vertical-align: middle;
}

/* When in doubt list */
.doubt-list {
    margin: 0;
    padding-left: 0.9rem;
    font-size: 0.7rem;
    color: var(--text-secondary);
    line-height: 1.4;
}

.doubt-list li {
    margin-bottom: 0.15rem;
}

.doubt-list li:last-child {
    margin-bottom: 0;
}

.doubt-list strong {
    color: var(--text-primary);
}

/* Print styles - optimized for single 8.5x11 page */
@media print {
    @page {
        size: letter;
        margin: 0.4in 0.4in 0.35in 0.4in;
    }

    * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }

    body {
        font-size: 9.5pt;
        background: white !important;
        line-height: 1.25;
    }

    .topbar,
    .breadcrumb-nav,
    .version-banner {
        display: none !important;
    }

    main {
        padding: 0 !important;
    }

    .definitions-page {
        max-width: none;
    }

    .definitions-header {
        margin-bottom: 0.25rem;
        padding-bottom: 0.2rem;
        border-bottom-width: 1.5px;
    }

    .definitions-header h1 {
        font-size: 14pt;
        margin-bottom: 0.1rem;
    }

    .definitions-header p {
        font-size: 8.5pt;
    }

    .definitions-grid {
        gap: 0.25rem;
        margin-bottom: 0.3rem;
    }

    .definition-card {
        border: 1px solid #bbb;
        box-shadow: none;
    }

    .definition-card-header {
        padding: 0.22rem 0.35rem;
        gap: 0.3rem;
        background: #f0f0f0 !important;
    }

    .definition-card-icon {
        width: 20px;
        height: 20px;
        font-size: 9.5pt;
    }

    .definition-card-title {
        font-size: 9.5pt;
    }

    .definition-card-subtitle {
        font-size: 7.5pt;
    }

    .definition-card-body {
        padding: 0.25rem 0.35rem;
    }

    .definition-row {
        margin-bottom: 0.15rem;
    }

    .definition-row-label {
        font-size: 6.5pt;
        margin-bottom: 0;
    }

    .definition-row-value {
        font-size: 8pt;
        line-height: 1.25;
    }

    .definition-props {
        gap: 0.15rem;
    }

    .definition-props li {
        padding: 0.06rem 0.22rem;
        font-size: 7pt;
        background: #e8e8e8 !important;
    }

    .definition-props code {
        font-size: 6.5pt;
    }

    .definition-examples {
        font-size: 7.5pt;
    }

    .definitions-footer {
        gap: 0.25rem;
    }

    .footer-section {
        border: 1px solid #bbb;
    }

    .footer-section-header {
        padding: 0.18rem 0.35rem;
        background: #f0f0f0 !important;
    }

    .footer-section-header h2 {
        font-size: 8.5pt;
    }

    .footer-section-body {
        padding: 0.22rem 0.35rem;
    }

    .boundary-table {
        font-size: 7.5pt;
    }

    .boundary-table th,
    .boundary-table td {
        padding: 0.14rem 0.28rem;
    }

    .boundary-table th {
        font-size: 6.5pt;
    }

    .type-dot {
        width: 7px;
        height: 7px;
    }

    .doubt-list {
        font-size: 7.5pt;
        padding-left: 0.75rem;
        line-height: 1.3;
    }

    .doubt-list li {
        margin-bottom: 0.1rem;
    }
}

/* Responsive - stack on small screens */
@media screen and (max-width: 700px) {
    .definitions-grid {
        grid-template-columns: 1fr;
    }

    .definitions-footer {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def _render_compact_card(
    type: str,
    title: str,
    subtitle: str,
    definition: str,
    purpose: str,
    statuses: str,
    examples: str,
) -> str:
    """Render a compact definition card."""
    color = ARTIFACT_COLORS.get(type, "#6b7280")
    icon_letter = title[0].upper()

    return f'''
<div class="definition-card" id="{type}">
    <div class="definition-card-header">
        <div class="definition-card-icon" style="background: {color};">{icon_letter}</div>
        <div>
            <div class="definition-card-title">{title}</div>
            <div class="definition-card-subtitle">{subtitle}</div>
        </div>
    </div>
    <div class="definition-card-body">
        <div class="definition-row">
            <div class="definition-row-label">Definition</div>
            <div class="definition-row-value">{definition}</div>
        </div>
        <div class="definition-row">
            <div class="definition-row-label">Purpose</div>
            <div class="definition-row-value">{purpose}</div>
        </div>
        <div class="definition-row">
            <div class="definition-row-label">Statuses</div>
            <ul class="definition-props">{statuses}</ul>
        </div>
        <div class="definition-row">
            <div class="definition-row-label">Examples</div>
            <div class="definition-examples">{examples}</div>
        </div>
    </div>
</div>
'''


def render_definitions() -> str:
    """Render the Definitions page HTML."""

    # Compact definitions data with updated copy
    definitions = [
        {
            "type": "feature",
            "title": "Feature",
            "subtitle": "Top-level capability",
            "definition": "A major, stable business capability that organizes the system into meaningful, long-lived areas.",
            "purpose": "Defines \"what the system does\" at the highest level. Anchor points for organizing epics.",
            "statuses": "<li><code>active</code></li><li><code>deprecated</code></li>",
            "examples": "User Authentication, Report Generation, Payment Processing",
        },
        {
            "type": "epic",
            "title": "Epic",
            "subtitle": "Workflow grouping",
            "definition": "A coherent workflow or responsibility that groups related user stories under a feature.",
            "purpose": "Represents \"how\" a feature is delivered. Groups stories that share context.",
            "statuses": "<li><code>active</code></li><li><code>deprecated</code></li><li>Versions: <code>backlog</code></li><li><code>released</code></li><li><code>discarded</code></li>",
            "examples": "Password Reset Flow, Monthly Revenue Report, Refund Processing",
        },
        {
            "type": "requirement",
            "title": "Requirement",
            "subtitle": "Business constraint",
            "definition": "A verifiable business rule or constraint that the system must enforce.",
            "purpose": "Captures \"what must be true\" regardless of implementation. Must remain valid even if UI, workflow, or technology changes. Traces to artifacts.",
            "statuses": "<li><code>active</code></li><li><code>deprecated</code></li><li><code>provisional</code></li>",
            "examples": "\"Password must be 12+ chars\", \"API responses under 500ms\"",
        },
        {
            "type": "artifact",
            "title": "Business Artifact",
            "subtitle": "Source document",
            "definition": "A document or specification describing business rules or reference data.",
            "purpose": "Authoritative source for requirements. Describes sources of truth, not system behavior. Policies, rules, or catalogs the system respects.",
            "statuses": "<li><code>draft</code></li><li><code>active</code></li><li><code>deprecated</code></li><li>Types: <code>policy</code></li><li><code>rule</code></li><li><code>catalog</code></li>",
            "examples": "Password Policy, Fee Schedule, Classification Rules",
        },
        {
            "type": "story",
            "title": "User Story",
            "subtitle": "Deliverable capability",
            "definition": "A user-centered capability with acceptance criteria and test intent. Derived from Epics and Requirements.",
            "purpose": "Atomic unit of delivery. Describes what a user can do with verification criteria.",
            "statuses": "<li><code>active</code></li><li><code>deprecated</code></li><li>Versions: <code>backlog</code></li><li><code>released</code></li><li><code>discarded</code></li><li><code>approved</code></li>",
            "examples": "Reset password via email, View monthly revenue, Request refund",
        },
        {
            "type": "release",
            "title": "Release",
            "subtitle": "Delivery milestone",
            "definition": "A planned delivery milestone that binds versions to a specific date.",
            "purpose": "Answers \"what shipped when?\" Timeline overlay tracking delivery events.",
            "statuses": "<li><code>planned</code></li><li><code>released</code></li>",
            "examples": "REL-2026-01-15, REL-2026-03-01, REL-2026-06-30",
        },
    ]

    # Build cards
    cards_html = ""
    for d in definitions:
        cards_html += _render_compact_card(**d)

    # Boundary rules
    boundary_rows = [
        ("A major system capability area", "feature", "Feature"),
        ("A group of related stories", "epic", "Epic"),
        ("A rule the system must enforce", "requirement", "Requirement"),
        ("A source document for rules", "artifact", "Business Artifact"),
        ("Something a user can do", "story", "User Story"),
        ("When something ships", "release", "Release"),
    ]

    boundary_html = ""
    for desc, type_key, type_name in boundary_rows:
        color = ARTIFACT_COLORS.get(type_key, "#6b7280")
        boundary_html += f'<tr><td>{desc}</td><td><span class="type-dot" style="background:{color};"></span>{type_name}</td></tr>'

    content = f'''
{DEFINITIONS_CSS}
<div class="definitions-page">
    <div class="definitions-header">
        <h1>APSCA Workshop Discovery Definitions</h1>
        <p>Canonical definitions for classifying work consistently across the project</p>
    </div>

    <div class="definitions-grid">
{cards_html}
    </div>

    <div class="definitions-footer">
        <div class="footer-section">
            <div class="footer-section-header">
                <h2>Classification Guide</h2>
            </div>
            <div class="footer-section-body">
                <table class="boundary-table">
                    <thead>
                        <tr><th>If you're describing...</th><th>Use</th></tr>
                    </thead>
                    <tbody>
{boundary_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="footer-section">
            <div class="footer-section-header">
                <h2>When in Doubt</h2>
            </div>
            <div class="footer-section-body">
                <ol class="doubt-list">
                    <li><strong>Features</strong> are stable and broad (added rarely)</li>
                    <li><strong>Epics</strong> group stories sharing context</li>
                    <li><strong>Requirements</strong> must be testable with authority</li>
                    <li><strong>Stories</strong> have clear acceptance criteria</li>
                    <li><strong>Artifacts</strong> are source docs, not behavior</li>
                    <li><strong>Releases</strong> are purely about timing</li>
                </ol>
            </div>
        </div>
    </div>
</div>
'''

    return html_page(
        title="Definitions",
        content=content,
        active_section="definitions",
        depth=0,
    )
