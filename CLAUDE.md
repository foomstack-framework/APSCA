# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

APSCA is a requirements management repository that stores structured requirements, features, epics, stories, and releases as canonical JSON. It serves as the system of record for backlog definition, with execution tools (Jira) consuming by reference rather than duplicating content. Human-readable documentation is generated from this data and served via GitHub Pages.

## Architecture

**Canonical data** (`data/*.json`):
- `domain.json` - Registry for authored domain reference docs (DOM-###)
- `requirements.json` - Declarative obligations (REQ-###)
- `features.json` - Top-level capability boundaries (FEAT-###)
- `epics.json` - Versioned groups of stories (EPIC-###)
- `stories.json` - Versioned commitments with acceptance criteria (STORY-###)
- `releases.json` - Delivery timeline events (REL-YYYY-MM-DD)

**Authored content** (`docs/domain/*.md`):
- Domain reference documents written by humans, not generated

**Generated content**:
- `docs/` (except `docs/domain/`) - GitHub Pages views rendered from JSON
- `reports/graph.json` - Structural relationship graph for traversal
- `reports/index.json` - Denormalized lookup index

**Scripts** (`scripts/`):
- `mutate.py` - All canonical JSON modifications go through this
- `validate.py` - Schema and reference integrity checks
- `build_graph.py` - Generates `reports/graph.json`
- `build_index.py` - Generates `reports/index.json`
- `render_docs.py` - Generates GitHub Pages views

Note: Scripts are currently stubs awaiting implementation.

## Key Principles

1. **Never edit `data/*.json` directly** - Use mutation scripts
2. **AI proposes, tools apply** - Generate mutation payloads for human confirmation, then execute via `mutate.py`
3. **Versioning** - Epics and stories are versioned; prior versions are immutable once superseded
4. **Traceability** - Downstream artifacts reference upstream by stable IDs
5. **Explicit timeline ownership** - Every version is bound to exactly one release

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
| Domain      | DOM-###        |
| Requirement | REQ-###        |
| Feature     | FEAT-###       |
| Epic        | EPIC-###       |
| Story       | STORY-###      |
| Release     | REL-YYYY-MM-DD |

Release IDs are date-based. If multiple releases occur on the same date, use suffix: `REL-2026-01-10-a`

## Releases and Version Binding

- Every epic version and story version must have a `release_ref`
- Releases have status: `planned | released | superseded`
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
- Requirements: `add_requirement`, `update_requirement`, `deprecate_requirement`, `supersede_requirement`
- Features: `add_feature`, `update_feature`, `deprecate_feature`
- Epics: `add_epic` (requires `release_ref`), `create_epic_version`, `set_epic_version_status`
- Stories: `add_story` (requires `release_ref`), `create_story_version`, `set_story_status`

## Validation Rules (Blocking)

- Schema conformance for all `data/*.json`
- ID uniqueness within each artifact family
- Reference integrity (all refs resolve, including `release_ref`)
- Release existence and closure (no versions added to `released` or `superseded` releases)
- Temporal coherence (superseded versions must belong to earlier or equal releases)
- Version lineage integrity (monotonic, no cycles)
- Stories must have acceptance criteria and test intent before `ready_to_build` status

## Test Intent

Stories include test intent that separates concerns:
- **Product defines** what must be protected (`failure_modes`, `guarantees`)
- **Developers implement** tests to satisfy that intent

This removes business reasoning burden from developers.

## GitHub Pages

Deployed from `docs/` via GitHub Actions (`.github/workflows/pages.yml`) on push to main.
