# APSCA Requirements Repository — Canonical Architecture Specification

## Purpose

This document defines the implementation-ready architecture for the APSCA requirements repository: canonical storage, data model, mutation/validation tooling, AI-assisted workflow (Claude Code master/clone), and view generation (GitLab Pages + reports).

It is designed to be sufficient for engineering to begin immediately.

---

# Design Principles

1. **Separation of concerns** — Domain facts, requirements, execution artifacts, and delivery events are distinct.
2. **Single source of truth** — Each datum has one authoritative home.
3. **Structured canon** — Requirements/planning truth is stored as JSON and validated.
4. **Generated views** — Human-facing Markdown/HTML is generated from canonical data (except domain reference docs).
5. **Traceability by construction** — Downstream artifacts reference upstream artifacts by stable IDs.
6. **Versioning preserves history** — Prior intent is not overwritten; it is superseded.
7. **Explicit timeline ownership** — Every version is bound to exactly one release; delivery dates are provable facts.
8. **Mutation is tool-mediated** — Canonical updates happen only via mutation scripts.
9. **AI proposes; tools apply** — AI performs investigation/analysis/proposals; scripts apply validated edits.

---

# Canonical Storage Strategy

## Canonical vs generated

**Canonical**

-   `data/*.json` — Structured truth for requirements, features, epics, stories, releases, and domain registry.
-   `docs/domain/*.md` — Domain reference documents (authored prose, not generated).

**Generated**

-   `docs/*` — Views and navigation for GitLab Pages (generated, except `docs/domain/*`).
-   `reports/*` — Derived graphs, indexes, and analysis artifacts.

## Why this avoids "sync" problems

The system avoids drift by normalizing truth:

-   Each record family has exactly one canonical home (`data/*.json`).
-   Relationships are expressed only as ID references inside JSON.
-   No requirement/feature/epic/story content is duplicated into Markdown.
-   Views are generated from JSON; therefore the view layer cannot drift.

Domain reference documents are the only authored Markdown. They are referenced by stable IDs stored in `data/domain.json`.

---

# Repository Layout

The layout is intentionally flat and database-like (one JSON file per artifact family) to minimize complexity and avoid file-move churn.

```
repo-root/
├── data/
│   ├── domain.json           # Registry/index for domain docs
│   ├── requirements.json
│   ├── features.json
│   ├── epics.json
│   ├── stories.json
│   └── releases.json         # Delivery timeline
│
├── docs/                     # GitLab Pages root
│   ├── domain/               # Authored domain reference docs
│   │   ├── eligibility.md
│   │   ├── exam-catalog.md
│   │   └── ...
│   ├── requirements/         # Generated
│   ├── features/             # Generated
│   ├── epics/                # Generated
│   ├── stories/              # Generated
│   ├── releases/             # Generated
│   ├── reports/              # Generated (human-facing)
│   └── index.html            # Generated navigation/dashboard
│
├── reports/                  # Generated (machine-facing)
│   ├── graph.json            # Structural relationship graph
│   └── index.json            # Convenience lookup index
│
├── scripts/
│   ├── mutate.py
│   ├── validate.py
│   ├── build_graph.py
│   ├── build_index.py
│   └── render_docs.py
│
└── .claude/
    └── commands/
```

Notes:

-   GitLab Pages serves `docs/`.
-   `docs/domain/` is authored and never regenerated.
-   Everything else under `docs/` is generated from `data/*.json`.

---

# Artifact Taxonomy and Directionality

## Core hierarchy (one-way)

**Domain → Requirements → Features → Epics → Stories → Acceptance Criteria / Test Intent**

Upstream artifacts may be referenced downstream. Downstream artifacts must never redefine upstream truth.

## Cross-cutting delivery layer

**Releases** are not part of the core hierarchy. They are a cross-cutting layer that binds specific versions to delivery events.

```
Releases ← Epic Versions
Releases ← Story Versions
```

Releases answer: "What shipped when?"

## First-class artifact families

1. Domain reference artifacts (registry + authored docs)
2. Requirements
3. Features
4. Epics (versioned)
5. Stories (versioned)
6. Releases (delivery events)

Acceptance criteria and test intent live exclusively inside stories.

---

# Persistent Artifacts vs Delivery Units

The repository distinguishes between:

| Concept                  | Description                                                        | Example                   |
| ------------------------ | ------------------------------------------------------------------ | ------------------------- |
| **Persistent artifacts** | Epics and stories as enduring descriptions of scope and intent     | EPIC-003, STORY-017       |
| **Artifact versions**    | Immutable snapshots representing evolving understanding            | EPIC-003-v2, STORY-017-v1 |
| **Releases**             | Time-bounded delivery events that group specific artifact versions | REL-2026-01-10            |

> Jira epics and stories represent _units of execution_.
> Repository epics and stories represent _persistent truth_.
> Releases bridge the two.

---

# Identity and Versioning Model

## Stable IDs

Stable IDs are referenced everywhere. Format conventions:

| Artifact     | Format                       |
| ------------ | ---------------------------- |
| Domain       | `ART-###`                    |
| Requirements | `REQ-###`                    |
| Features     | `FEAT-###`                   |
| Epics        | `EPIC-###`                   |
| Stories      | `STORY-###`                  |
| Releases     | `REL-YYYY-MM-DD` (see below) |

IDs are globally unique within their artifact family.

## Release ID format

Releases use date-based IDs:

```
REL-YYYY-MM-DD
```

Examples:

-   `REL-2026-01-10`
-   `REL-2026-02-01`

If multiple releases occur on the same date, an optional suffix may be used:

-   `REL-2026-01-10-a`
-   `REL-2026-01-10-b`

The release ID answers: "When did this scope ship?"

## Versioning

Epics and stories are versioned. Domain, requirements, features, and releases are not versioned.

For versioned artifacts:

-   Versions are immutable once superseded.
-   New understanding produces a new version entry; prior versions are never edited.
-   Versioning is represented as a `versions: []` array on the record.
-   `versions[n].version` is a monotonically increasing integer starting at 1.
-   Creating version N automatically marks version N-1 as `superseded`.
-   **Every version must reference exactly one release via `release_ref`.**

---

# Common Fields

All record types include these common fields:

| Field        | Type     | Description                                     |
| ------------ | -------- | ----------------------------------------------- |
| `id`         | string   | Stable unique identifier                        |
| `title`      | string   | Human-readable name                             |
| `status`     | enum     | Record-specific status (see each artifact type) |
| `tags`       | string[] | Free-form classification tags                   |
| `owner`      | string   | Responsible person or role                      |
| `created_at` | ISO8601  | Creation timestamp                              |
| `updated_at` | ISO8601  | Last modification timestamp                     |
| `notes`      | string   | Optional free-form notes                        |

---

# Canonical Data Files

## 1) `data/domain.json` — Domain Registry

**Purpose:** Provide stable IDs and metadata for authored domain reference documents.

**Status enum:** `active | deprecated`

**Record fields:**

| Field            | Type         | Description                                                                                                                                     |
| ---------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Common fields    |              |                                                                                                                                                 |
| `type`           | enum         | `policy \| catalog \| classification \| rule`                                                                                                   |
| `source`         | string       | Origin of the information (e.g., "Meg / APSCA policy", "APSCA operations", "regulatory")                                                        |
| `effective_date` | ISO8601 date | When this domain knowledge became effective                                                                                                     |
| `doc_path`       | string       | Path to the authored markdown file (e.g., `docs/domain/eligibility.md`)                                                                         |
| `anchors`        | string[]     | Optional list of stable section anchors within the document for fine-grained referencing (e.g., `["eligibility-tier-1", "eligibility-tier-2"]`) |

**Rules:**

-   Domain docs are descriptive, not prescriptive.
-   Downstream artifacts reference domain by `ART-###` ID.
-   The `anchors` field enables references to specific sections, not just entire documents.
-   Domain docs are authored directly in `docs/domain/`; the registry tracks metadata only.

---

## 2) `data/requirements.json` — Requirements

**Purpose:** Declarative obligations that must always hold true for the system.

**Status enum:** `active | deprecated`

**Record fields:**

| Field           | Type           | Description                                               |
| --------------- | -------------- | --------------------------------------------------------- |
| Common fields   |                |                                                           |
| `type`          | enum           | `functional \| non-functional`                            |
| `invariant`     | boolean        | True if this is a non-negotiable business/regulatory rule |
| `statement`     | string         | Declarative requirement (what must be true)               |
| `rationale`     | string         | Why this requirement exists                               |
| `domain_refs`   | string[]       | DOM IDs this requirement relates to                       |
| `superseded_by` | string \| null | REQ ID if this requirement was replaced by another        |

**Rules:**

-   Requirements are never duplicated in epics or stories.
-   Downstream artifacts reference by `id` only.
-   Semantic changes should create a new requirement and deprecate the old one (set `superseded_by`).
-   Minor fixes (typos, clarification without semantic change) may use an update operation.

---

## 3) `data/features.json` — Features

**Purpose:** Top-level capability boundaries that organize epics.

**Status enum:** `active | deprecated`

**Record fields:**

| Field              | Type     | Description                              |
| ------------------ | -------- | ---------------------------------------- |
| Common fields      |          |                                          |
| `purpose`          | string   | What this feature accomplishes           |
| `business_value`   | string   | Why this feature matters to the business |
| `in_scope`         | string[] | What is included in this feature         |
| `out_of_scope`     | string[] | What is explicitly excluded              |
| `requirement_refs` | string[] | REQ IDs this feature addresses           |
| `domain_refs`      | string[] | DOM IDs relevant to this feature         |

**Rules:**

-   Features evolve slowly; no versioning.
-   Features do not contain acceptance criteria or implementation detail.

---

## 4) `data/releases.json` — Releases

**Purpose:** Immutable delivery snapshots that bind specific artifact versions to a point in time.

**Status enum:** `planned | released | superseded`

**Record fields:**

| Field          | Type           | Description                            |
| -------------- | -------------- | -------------------------------------- |
| Common fields  |                |                                        |
| `release_date` | ISO8601 date   | Authoritative delivery date            |
| `git_tag`      | string \| null | Optional Git tag (e.g., `v2026.01.10`) |
| `description`  | string         | Summary of the release intent          |

**Rules:**

-   Releases are immutable once status is `released`.
-   If scope changes after a release, a new release must be created.
-   No new versions may be added to a release once its status is `released`.
-   A release marked `superseded` indicates it was replaced before shipping (e.g., scope was rolled into a later release).

---

## 5) `data/epics.json` — Epics (Versioned)

**Purpose:** Group stories into coherent slices of intent. Versioned to preserve evolving understanding.

**Epic record fields:**

| Field         | Type     | Description                  |
| ------------- | -------- | ---------------------------- |
| `id`          | string   | EPIC-###                     |
| `title`       | string   | Epic name                    |
| `feature_ref` | string   | FEAT ID this epic belongs to |
| `tags`        | string[] | Classification tags          |
| `owner`       | string   | Responsible person/role      |
| `created_at`  | ISO8601  | When epic was created        |
| `versions`    | array    | Version history (see below)  |

**Epic version fields (`versions[]`):**

| Field              | Type        | Description                                           |
| ------------------ | ----------- | ----------------------------------------------------- |
| `version`          | int         | Version number (monotonic, starts at 1)               |
| `status`           | enum        | `draft \| approved \| superseded`                     |
| `release_ref`      | string      | **Required.** REL ID this version belongs to          |
| `summary`          | string      | What this epic accomplishes                           |
| `assumptions`      | string[]    | What we assume to be true                             |
| `constraints`      | string[]    | Known limitations or boundaries                       |
| `requirement_refs` | string[]    | REQ IDs addressed by this epic version                |
| `domain_refs`      | string[]    | DOM IDs relevant to this epic version                 |
| `supersedes`       | int \| null | Version number this supersedes (null for v1)          |
| `created_at`       | ISO8601     | When this version was created                         |
| `updated_at`       | ISO8601     | Last modification to this version                     |
| `owner`            | string      | Owner for this version (if different from epic owner) |
| `notes`            | string      | Optional version-specific notes                       |

**Rules:**

-   Only the latest version may be `draft` or `approved`.
-   Prior versions are immutable and must have status `superseded`.
-   Every version must have a `release_ref` that points to a valid, non-closed release.
-   A version's `release_ref` may not be changed once created.

---

## 6) `data/stories.json` — Stories (Versioned)

**Purpose:** Concrete, versioned commitments. Owns acceptance criteria and test intent.

**Story record fields:**

| Field        | Type     | Description                                                                              |
| ------------ | -------- | ---------------------------------------------------------------------------------------- |
| `id`         | string   | STORY-###                                                                                |
| `title`      | string   | Story name                                                                               |
| `epic_ref`   | string   | EPIC ID this story belongs to (story belongs to epic as a whole, not a specific version) |
| `tags`       | string[] | Classification tags                                                                      |
| `owner`      | string   | Responsible person/role                                                                  |
| `created_at` | ISO8601  | When story was created                                                                   |
| `versions`   | array    | Version history (see below)                                                              |

**Story version fields (`versions[]`):**

| Field                 | Type        | Description                                                     |
| --------------------- | ----------- | --------------------------------------------------------------- |
| `version`             | int         | Version number (monotonic, starts at 1)                         |
| `status`              | enum        | `draft \| ready_to_build \| in_build \| built \| superseded`    |
| `release_ref`         | string      | **Required.** REL ID this version belongs to                    |
| `description`         | string      | Story description (e.g., "As a [user], I want [X] so that [Y]") |
| `requirement_refs`    | string[]    | REQ IDs this story satisfies                                    |
| `domain_refs`         | string[]    | DOM IDs relevant to this story                                  |
| `acceptance_criteria` | array       | See structure below                                             |
| `test_intent`         | object      | See structure below                                             |
| `supersedes`          | int \| null | Version number this supersedes (null for v1)                    |
| `created_at`          | ISO8601     | When this version was created                                   |
| `updated_at`          | ISO8601     | Last modification to this version                               |
| `owner`               | string      | Owner for this version (if different from story owner)          |
| `notes`               | string      | Optional version-specific notes                                 |

**Acceptance criteria structure (`acceptance_criteria[]`):**

| Field       | Type           | Description                                                     |
| ----------- | -------------- | --------------------------------------------------------------- |
| `id`        | string         | Story-local ID (e.g., `AC-001`, `AC-002`) — not globally unique |
| `statement` | string         | The acceptance criterion                                        |
| `notes`     | string \| null | Optional clarification                                          |

**Test intent structure (`test_intent`):**

| Field           | Type     | Description                                         |
| --------------- | -------- | --------------------------------------------------- |
| `failure_modes` | string[] | What must not happen (failure scenarios to prevent) |
| `guarantees`    | string[] | What must always be true (invariants to protect)    |
| `exclusions`    | string[] | What is explicitly not tested by this story         |

**Rules:**

-   Acceptance criteria and test intent exist only inside stories.
-   Prior story versions are immutable.
-   A story belongs to an epic as a whole, not a specific epic version.
-   Every version must have a `release_ref` that points to a valid, non-closed release.
-   A version's `release_ref` may not be changed once created.

---

# Version Lifecycle Rules

## Version creation

-   Creating a new epic or story version **requires specifying `release_ref`**.
-   Creating version N automatically supersedes version N-1.
-   The target release must exist and have status `planned` (not `released` or `superseded`).

## After a release is cut

When a release is marked `released`:

-   All epic versions assigned to that release are considered **closed**.
-   All story versions assigned to that release are considered **closed**.
-   Any subsequent work requires:
    -   A new version
    -   Assigned to a **new release**

This cleanly models "reopening" work as new scope, not mutation of history.

## Temporal coherence

-   Superseded versions must belong to earlier or equal releases.
-   A newer version may not reference an earlier release than its predecessor.

---

# Mutation Model (Tooling)

## Principle

Canonical JSON is modified only via `scripts/mutate.py` (or equivalent command wrappers). No direct edits to `data/*.json`.

Domain reference documents (`docs/domain/*.md`) are authored directly and do not go through mutation scripts.

## Interface

The mutation tool must be callable non-interactively.

Recommended pattern:

```
python scripts/mutate.py <operation> --payload '<json>'
python scripts/mutate.py <operation> --payload-file <path>
```

## Required operations (minimum viable set)

**Releases:**

-   `create_release` — Create a new release (status: planned)
-   `set_release_status` — Transition release status (planned → released, or planned → superseded)

**Domain registry:**

-   `add_domain_entry` — Add a new domain registry entry
-   `update_domain_entry` — Update metadata for existing entry
-   `deprecate_domain_entry` — Set status to deprecated

**Requirements:**

-   `add_requirement` — Add a new requirement
-   `update_requirement` — Update fields (minor fixes only; semantic changes should create new + deprecate)
-   `deprecate_requirement` — Set status to deprecated
-   `supersede_requirement` — Create new requirement that supersedes an existing one

**Features:**

-   `add_feature` — Add a new feature
-   `update_feature` — Update feature fields
-   `deprecate_feature` — Set status to deprecated

**Epics:**

-   `add_epic` — Add a new epic with initial version (requires `release_ref`)
-   `create_epic_version` — Add new version to existing epic (requires `release_ref`; auto-supersedes previous)
-   `set_epic_version_status` — Change status of current version (e.g., draft → approved)

**Stories:**

-   `add_story` — Add a new story with initial version (requires `release_ref`)
-   `create_story_version` — Add new version to existing story (requires `release_ref`; auto-supersedes previous)
-   `set_story_status` — Change status of current version

## Behavior rules

-   Mutations are deterministic and format output consistently (stable key ordering).
-   Creating a new version automatically sets the previous version's status to `superseded`.
-   Mutations must refuse to edit immutable (superseded) versions.
-   Mutations must refuse to add versions to closed releases (status `released` or `superseded`).
-   Mutations must reject missing or invalid `release_ref`.
-   Every mutation updates the `updated_at` timestamp.

---

# Validation Layer (Blocking Gates)

Validation is executed after every mutation and in CI.

## Required validations (block on failure)

1. **Schema validation** — All `data/*.json` files conform to their schemas.

2. **ID uniqueness** — No duplicate IDs within each artifact family.

3. **Reference integrity** — All refs resolve to existing records:

    - `domain_refs` → DOM IDs in `domain.json`
    - `requirement_refs` → REQ IDs in `requirements.json`
    - `feature_ref` → FEAT ID in `features.json`
    - `epic_ref` → EPIC ID in `epics.json`
    - `release_ref` → REL ID in `releases.json`

4. **Release existence** — Every `release_ref` resolves to a valid entry in `data/releases.json`.

5. **Single-release ownership** — Every epic version and story version has exactly one `release_ref`.

6. **Release immutability** — A version's `release_ref` may not be changed once created.

7. **Release closure** — No new versions may be added to a release once its status is `released` or `superseded`.

8. **Temporal coherence** — Superseded versions must belong to earlier or equal releases. A newer version may not reference an earlier release than its predecessor.

9. **Version lineage integrity:**

    - Version numbers are monotonically increasing
    - `supersedes` chain is linear (no cycles)
    - Only one non-superseded version exists per record

10. **Status coherence:**

    - Superseded versions must have status `superseded`
    - Only the latest version can be `draft`, `approved`, `ready_to_build`, etc.

11. **Story completeness for build eligibility:**
    - If status is `ready_to_build` or later, story must have:
        - At least one acceptance criterion
        - Test intent with at least one entry in `failure_modes` or `guarantees`

## Optional validations (warn only)

-   Current-version artifacts referencing deprecated upstream artifacts (historical reference is allowed but surfaces risk).
-   Domain registry entries pointing to non-existent markdown files.

---

# Derived Reports (Required Infrastructure)

Two machine-facing reports are regenerated on every mutation:

## `reports/graph.json` — Structural Relationship Graph

**Purpose:** Authoritative derived graph for traversal, impact analysis, and AI reasoning.

**What it contains:**

-   Nodes (all artifacts and versions)
-   Edges (relationships between artifacts)
-   Minimal metadata needed for structural reasoning

**Schema:**

```json
{
    "nodes": [
        { "id": "REL-2026-01-10", "type": "release", "status": "released" },
        { "id": "REQ-042", "type": "requirement", "status": "active" },
        { "id": "FEAT-001", "type": "feature", "status": "active" },
        { "id": "EPIC-003", "type": "epic" },
        { "id": "EPIC-003-v2", "type": "epic_version", "status": "approved" },
        { "id": "STORY-017", "type": "story" },
        {
            "id": "STORY-017-v2",
            "type": "story_version",
            "status": "ready_to_build"
        }
    ],
    "edges": [
        { "from": "STORY-017-v2", "to": "REQ-042", "type": "satisfies" },
        { "from": "STORY-017", "to": "EPIC-003", "type": "belongs_to" },
        { "from": "EPIC-003", "to": "FEAT-001", "type": "scoped_by" },
        { "from": "STORY-017-v2", "to": "STORY-017-v1", "type": "supersedes" },
        { "from": "STORY-017-v2", "to": "STORY-017", "type": "version_of" },
        {
            "from": "STORY-017-v2",
            "to": "ART-001",
            "type": "references_domain"
        },
        {
            "from": "STORY-017-v2",
            "to": "REL-2026-01-10",
            "type": "assigned_to_release"
        },
        {
            "from": "EPIC-003-v2",
            "to": "REL-2026-01-10",
            "type": "assigned_to_release"
        }
    ]
}
```

**Node types:** `release`, `domain`, `requirement`, `feature`, `epic`, `epic_version`, `story`, `story_version`

**Edge types:** `satisfies`, `belongs_to`, `scoped_by`, `version_of`, `supersedes`, `references_domain`, `assigned_to_release`

**Properties:**

-   Lossless — relationships can be reconstructed from it
-   Minimal — no duplicated prose content
-   Machine-first — optimized for traversal, not human reading
-   Rebuilt on every canonical data change

**Use cases:**

-   Impact analysis ("what breaks if REQ-042 changes?")
-   Coverage checks ("which requirements have no stories?")
-   AI traversal without loading all JSON files
-   Historical reasoning via version/supersession edges
-   Timeline traversal ("what changed since last release?")
-   Delivery impact analysis ("what's in this release?")

---

## `reports/index.json` — Convenience Lookup Index

**Purpose:** Denormalized, precomputed summaries for fast lookup and UI generation.

**What it contains:**

-   Reverse lookups (requirement → stories, epic → stories, feature → epics, release → versions)
-   Current version pointers
-   Status summaries and counts
-   Coverage indicators
-   Per-release summaries

**Schema (example):**

```json
{
    "releases": {
        "REL-2026-01-10": {
            "status": "released",
            "release_date": "2026-01-10",
            "epic_versions": ["EPIC-003-v2", "EPIC-004-v1"],
            "story_versions": ["STORY-017-v2", "STORY-021-v1", "STORY-022-v1"],
            "story_count": 3
        }
    },
    "requirements": {
        "REQ-042": {
            "title": "Prevent ineligible registration",
            "status": "active",
            "satisfied_by": ["STORY-017-v2", "STORY-021-v1"],
            "coverage": "full"
        }
    },
    "features": {
        "FEAT-001": {
            "title": "Eligibility Enforcement",
            "status": "active",
            "epics": ["EPIC-003", "EPIC-004"],
            "story_count": 12
        }
    },
    "epics": {
        "EPIC-003": {
            "title": "Registration Eligibility",
            "current_version": 2,
            "current_status": "approved",
            "stories": ["STORY-017", "STORY-021", "STORY-022"]
        }
    },
    "stories": {
        "STORY-017": {
            "title": "Prevent Ineligible Exam Registration",
            "current_version": 2,
            "current_status": "ready_to_build",
            "epic_ref": "EPIC-003",
            "release_ref": "REL-2026-01-10"
        }
    },
    "summary": {
        "total_requirements": 42,
        "active_requirements": 38,
        "total_stories": 87,
        "ready_to_build": 12,
        "in_build": 5,
        "built": 34,
        "releases_planned": 2,
        "releases_shipped": 5
    }
}
```

**Properties:**

-   Derived and redundant — built from canonical data and/or `graph.json`
-   Not lossless — summary data only
-   Human- and UI-friendly
-   Can change shape over time without breaking core logic

**Use cases:**

-   Rendering GitLab Pages views efficiently
-   Generating reports without repeated graph traversal
-   Giving AI a "summary lens" for quick orientation
-   Dashboard statistics
-   Release-scoped views ("what's in REL-2026-01-10?")

---

## Relationship Between graph.json and index.json

| File         | Role                           | Analogy                    |
| ------------ | ------------------------------ | -------------------------- |
| `graph.json` | Structural truth for traversal | Database normalized tables |
| `index.json` | Convenience cache for lookup   | Materialized views         |

**Rules:**

-   `graph.json` is the source of derived structural truth.
-   `index.json` is built from `graph.json` and/or canonical JSON.
-   Nothing depends on `index.json` for correctness.
-   If `index.json` is missing or corrupt, it can be fully rebuilt.

---

# Rendering and GitLab Pages

## Rule

Humans browse `docs/`, not `data/`.

## Generated outputs

`render_docs.py` generates:

-   `docs/index.html` — Navigation dashboard
-   `docs/requirements/*.html` — Requirement detail views
-   `docs/features/*.html` — Feature detail views
-   `docs/epics/*.html` — Epic and epic-version views
-   `docs/stories/*.html` — Story and story-version views
-   `docs/releases/*.html` — Release detail views (what shipped, when)
-   `docs/reports/*.html` — Human-readable reports (coverage, traceability, release history)

Domain docs are already authored at `docs/domain/*.md` and are linked from generated pages via `ART-###` registry entries.

---

# AI Workflow (Claude Code)

## Principle

Claude Code performs investigation and proposal; mutation scripts remain the authority. AI never edits `data/*.json` directly.

## Slash commands (minimum set)

**Targeted (scope locked upfront):**

-   `/update-story STORY-###` — Propose changes to a specific story
-   `/create-story-version STORY-###` — Create a new version of a story
-   `/create-epic-version EPIC-###` — Create a new version of an epic
-   `/supersede-requirement REQ-###` — Supersede a requirement with a new one
-   `/add-requirement` — Add a new requirement
-   `/create-release` — Create a new planned release
-   `/release REL-###` — Mark a release as shipped

**Exploratory (AI determines scope):**

-   `/process-client-change <text|file>` — Analyze client input and propose updates
-   `/analyze-transcript <file>` — Extract requirements/changes from discovery transcript
-   `/release-summary REL-###` — Summarize what's included in a release

## High-level flow (master/clone architecture)

1. **Investigation agent:** Semantic search across repo; identify potentially relevant artifacts.
2. **Impact agent:** Assess scope using `graph.json`; identify affected records; flag missing links.
3. **Proposal agent:** Produce structured mutation payloads (operation + payload JSON).
4. **Parent agent:** Summarize proposed changes; request human confirmation; execute `mutate.py`; run `validate.py`; regenerate graph, index, and docs.

## Key constraints

-   AI proposes; human confirms; scripts execute.
-   AI uses `graph.json` for traversal, `index.json` for summaries.
-   AI may read any file; AI may only write via mutation scripts.
-   When creating new versions, AI must specify a valid `release_ref`.

---

# Non-goals and Boundaries

This repository does not attempt to:

-   Replace Jira or sprint management tools
-   Track developer tasks
-   Host production application code
-   Store executable test code

**Protocol:**

-   Requirements define what must be true.
-   Stories define acceptance criteria and test intent.
-   Releases define what shipped when.
-   External systems (Jira, CI, test frameworks) execute work and report outcomes.
-   This repo is the source of truth that those systems reference.

---

# Database Decision

No external database is required for v1.

**Rationale:**

-   Git provides the audit log.
-   JSON + scripts provide structure and constraints.
-   Write frequency is low; read frequency is high.
-   Migration to SQLite/Postgres remains possible later if scale or concurrency demands it.

---

# Engineering Readiness Checklist

Engineering can begin when:

-   [ ] `data/` files exist with valid (empty or seeded) JSON
-   [ ] JSON schemas exist for all artifact types (including releases)
-   [ ] `mutate.py` implements the minimum operations (including release operations)
-   [ ] `validate.py` blocks structural violations (including release-related validations)
-   [ ] `build_graph.py` generates `reports/graph.json` (including release nodes and edges)
-   [ ] `build_index.py` generates `reports/index.json` (including release summaries)
-   [ ] `render_docs.py` generates GitLab Pages views (including release views)
-   [ ] One end-to-end vertical slice exists:
    -   REL-#### created (planned)
    -   DOM entry + authored doc
    -   REQ referencing the DOM
    -   FEAT referencing the REQ
    -   EPIC (v1) under the FEAT, assigned to the release
    -   STORY (v1) under the EPIC, referencing REQ and DOM, assigned to the release
    -   Generated docs render correctly
    -   Graph and index include all relationships including release assignments
    -   Release marked as shipped; subsequent version requires new release
