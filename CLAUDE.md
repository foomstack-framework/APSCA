# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

APSCA is a requirements management repository that stores structured requirements, features, epics, stories, and releases as canonical JSON. It serves as the system of record for backlog definition, with execution tools (Jira) consuming by reference rather than duplicating content. Human-readable documentation is generated from this data and served via GitLab Pages.

## Architecture

**Canonical data** (`data/*.json`):
- `domain.json` - Registry for business artifacts (ART-###)
- `requirements.json` - Declarative obligations (REQ-###)
- `features.json` - Top-level capability boundaries (FEAT-###)
- `epics.json` - Versioned groups of stories (EPIC-###)
- `stories.json` - Versioned commitments with acceptance criteria (STORY-###)
- `releases.json` - Delivery timeline events (REL-YYYY-MM-DD)

**Authored content** (`docs/domain/*.md`):
- Domain reference documents written by humans, not generated

**Generated content**:
- `docs/` (except `docs/domain/`) - GitLab Pages views rendered from JSON
- `reports/graph.json` - Structural relationship graph for traversal
- `reports/index.json` - Denormalized lookup index

**Scripts** (`scripts/`):
- `mutate.py` - All canonical JSON modifications go through this
- `validate.py` - Schema and reference integrity checks
- `build_graph.py` - Generates `reports/graph.json`
- `build_index.py` - Generates `reports/index.json`
- `render_docs.py` - Generates HTML documentation

**Shared utilities** (`scripts/lib/`):
- `config.py` - Shared path constants (DATA_FILES, DATA_DIR, etc.)
- `io.py` - JSON I/O utilities (load_json, save_json)
- `versions.py` - Version utilities (get_current_version)

## Key Principles

1. **Never edit `data/*.json` directly** - Use mutation scripts
2. **AI proposes, tools apply** - Generate mutation payloads for human confirmation, then execute via `mutate.py`
3. **Versioning** - Epics and stories are versioned; prior versions are immutable once superseded
4. **Traceability** - Downstream artifacts reference upstream by stable IDs
5. **Explicit timeline ownership** - Every version is bound to exactly one release
6. **CRITICAL: Regenerate HTML after data changes** - The `docs/` folder contains generated HTML that must be rebuilt after any changes to `data/*.json` or `scripts/`. See "Build Process" section below.

## Artifact Relationships

**Core hierarchy (one-way):**
```
Domain → Requirements → Features → Epics → Stories → Acceptance Criteria
```

**Cross-cutting delivery layer:**
```
Releases ← Epic Versions
Releases ← Story Versions
```

Releases are not part of the core hierarchy. They bind specific versions to delivery events and answer: "What shipped when?"

## ID Formats

| Artifact    | Format         |
|-------------|----------------|
| Business Artifact | ART-###   |
| Requirement | REQ-###        |
| Feature     | FEAT-###       |
| Epic        | EPIC-###       |
| Story       | STORY-###      |
| Release     | REL-YYYY-MM-DD |

Release IDs are date-based. If multiple releases occur on the same date, use suffix: `REL-2026-01-10-a`

## Status Model

### Artifact Statuses

| Artifact | Status Field | Valid Values |
|----------|-------------|--------------|
| **Releases** | status | `planned`, `released` |
| **Domain** | status | `draft`, `active`, `deprecated` |
| **Domain** | type | Array of strings (e.g., `["rule"]`, `["policy", "rule"]`) |
| **Requirements** | status | `active`, `deprecated`, `provisional` |
| **Features** | status | `active`, `deprecated` |
| **Epics** | status (artifact) | `active`, `deprecated` |
| **Epic Versions** | status | `backlog`, `released`, `discarded` |
| **Epic Versions** | approved | boolean (default: false) |
| **Stories** | status (artifact) | `active`, `deprecated` |
| **Story Versions** | status | `backlog`, `released`, `discarded` |
| **Story Versions** | approved | boolean (default: false) |

### Version Status Semantics

- **backlog**: Active work version (only ONE per artifact at any time)
- **released**: Shipped with a release
- **discarded**: Abandoned before completion

### Approval Field Semantics

- **approved: false**: Pending client sign-off
- **approved: true**: Client has approved for development

Stories with `approved: true` must have `acceptance_criteria` and `test_intent` with at least one `failure_mode` or `guarantee`.

## Releases and Version Binding

- Every epic version and story version should have a `release_ref` (can be null for unassigned backlog versions)
- Releases have status: `planned | released`
- Once a release is `released`, all assigned versions are closed
- Any subsequent work requires a new version assigned to a new release
- A version's `release_ref` cannot be changed once created
- Newer versions cannot reference earlier releases than their predecessors

## Mutation Operations

```bash
python scripts/mutate.py <operation> --payload '<json>'
python scripts/mutate.py <operation> --payload-file <path>
```

Key operations:
- Releases: `create_release`, `set_release_status`
- Domain: `add_domain_entry`, `update_domain_entry`, `activate_domain_entry`, `deprecate_domain_entry`
- Requirements: `add_requirement`, `update_requirement`, `deprecate_requirement`, `supersede_requirement`
- Features: `add_feature`, `update_feature`, `deprecate_feature`
- Epics: `add_epic` (requires `release_ref`), `create_epic_version`, `set_epic_version_status`, `set_epic_approved`, `deprecate_epic`
- Stories: `add_story` (requires `release_ref`), `create_story_version`, `set_story_status`, `set_story_approved`, `deprecate_story`

## Validation Rules (Blocking)

- Schema conformance for all `data/*.json`
- ID uniqueness within each artifact family
- Reference integrity (all refs resolve, including `release_ref`)
- Release existence and closure (no versions added to `released` releases)
- Version lineage integrity (monotonic, no cycles)
- Single backlog rule: Only one version per epic/story can have `status: "backlog"`
- Approved field required: Epic/story versions must have `approved: boolean`
- Domain type is array: `type` field must be an array of valid type strings
- Completeness for approved: Stories with `approved: true` must have `acceptance_criteria` and `test_intent`

## Test Intent

Stories include test intent that separates concerns:
- **Product defines** what must be protected (`failure_modes`, `guarantees`)
- **Developers implement** tests to satisfy that intent

This removes business reasoning burden from developers.

## Build Process

**IMPORTANT**: The HTML files in `docs/` are generated from `data/*.json`. They are NOT automatically updated when data changes. You MUST run the build scripts to regenerate the HTML before committing.

### Required Build Steps

After making any changes to `data/*.json` or `scripts/`, run these commands in order:

```bash
# 1. Validate data integrity (catches errors before rendering)
python scripts/validate.py

# 2. Regenerate HTML documentation
python scripts/render_docs.py

# 3. Rebuild graph and index (for traversal and search)
python scripts/build_graph.py
python scripts/build_index.py
```

### When to Rebuild

Run all build scripts after:
- Any mutation operation (`python scripts/mutate.py ...`)
- Direct edits to `data/*.json` files
- Changes to rendering scripts (`scripts/render_docs.py`, `scripts/lib/assets.py`)
- Changes to validation rules (`scripts/validate.py`)

### Verification

After rebuilding, verify the changes took effect:
- Open `docs/stories/index.html` in a browser to check story listings
- Open `docs/story-map.html` to verify the interactive visualization
- Check that `docs/data/*.json` files are updated (these are copies for the web UI)

## GitLab Pages

Deployed from `docs/` via GitLab CI (`.gitlab-ci.yml`) on push to the default branch.

Key pages:
- `docs/index.html` - Dashboard landing page
- `docs/story-map.html` - Interactive story map visualization
- `docs/releases/*.html` - Release detail pages
- `docs/features/*.html` - Feature detail pages
- `docs/epics/*.html` - Epic detail pages
- `docs/stories/*.html` - Story detail pages
- `docs/requirements/*.html` - Requirement detail pages
- `docs/domain/*.html` - Generated domain reference pages

## AI Workflow Commands

Two slash commands exist for requirements management:

- `/input-requirements <file_or_text>` - Parse and clarify requirements interactively
- `/integrate-changes <approval_file>` - Execute mutations from approval files

Workflow:
1. Use `/input-requirements` to parse input and generate an approval file in `approvals/`
2. Review and edit the approval file as needed
3. Use `/integrate-changes` to execute mutations and rebuild artifacts
