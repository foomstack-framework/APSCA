# APSCA Requirements Repository Workflow

## Overview

This document describes the workflow for managing the APSCA requirements repository. The workflow consists of 2 commands that handle requirements clarification and integration.

---

## Workflow Architecture

### Phase 1: Requirements Clarification

**Entry Point:** `/input-requirements <input_file> [| context]`

**Purpose:** Parse unstructured input (discovery transcripts, notes, inline text) and clarify requirements through interactive dialogue.

**Flow:**
```
User → /input-requirements input/transcript.txt
    ↓
    Parse input file or inline text
    ↓
    Determine intent level (high-level, detailed, or mixed)
    ↓
    AskUserQuestion: Batch clarification questions
        - Scope boundaries
        - Artifact types needed
        - ID assignments
        - Priority/dependencies
    ↓
    Generate structured approval file
    ↓
    Output: approvals/<descriptive-name>.txt
```

**Human Interaction Points:**
- Clarifying questions about scope and boundaries
- Confirming artifact types and relationships
- Reviewing generated approval file

**Output:** `approvals/<name>.txt` - Structured approval file ready for integration

---

### Phase 2: Requirements Integration

**Entry Point:** `/integrate-changes <approval_file>`

**Purpose:** Parse approval files and execute mutations to update canonical data.

**Flow:**
```
User → /integrate-changes approvals/exam-purchasing.txt
    ↓
    Parse approval file sections:
        - ARTIFACTS (ART-###)
        - REQUIREMENTS (REQ-###)
        - FEATURES (FEAT-###)
        - MIGRATION ACTIONS
    ↓
    Present mutation summary
    ↓
    AskUserQuestion: Execute / Show Commands / Cancel
    ↓
    Execute mutations via mutate.py (if approved):
        1. Business artifacts (no dependencies)
        2. Requirements (may reference artifacts)
        3. Features (may reference requirements and artifacts)
        4. Deprecations/migrations
    ↓
    Rebuild artifacts:
        - python scripts/validate.py
        - python scripts/build_graph.py
        - python scripts/build_index.py
        - python scripts/render_docs.py
    ↓
    Report results
```

**Human Interaction Points:**
- Reviewing mutation summary before execution
- Approving execution or requesting changes
- Reviewing results after execution

**Output:** Updated repository with new canonical data, regenerated reports and docs

---

## Command Inventory

| Command | File | Purpose |
|---------|------|---------|
| `/input-requirements` | `.claude/commands/input-requirements.md` | Parse and clarify requirements interactively |
| `/integrate-changes` | `.claude/commands/integrate-changes.md` | Execute mutations from approval files |

**Total: 2 commands**

---

## Artifact Flow

```
User Input (transcript, notes, text)
    ↓
    /input-requirements
    ↓
Approval File (approvals/*.txt)
    ↓
    /integrate-changes
    ↓
Canonical Data (data/*.json)
    ↓
    Build Scripts
    ↓
Reports (reports/*.json) + Docs (docs/*.html)
```

---

## Key Design Decisions

### 1. Two-Phase Separation
- **Phase 1 (Clarify):** Conversational, iterative, focused on understanding
- **Phase 2 (Integrate):** Deterministic, approval-gated, focused on execution

### 2. Approval Files as Intermediate Format
- Human-readable text format
- Can be reviewed and edited before integration
- Provides audit trail of requirements decisions

### 3. Single Approval Gate
- User approves mutation list before execution
- Can preview exact commands via "Show Commands" option
- Easy to cancel and revise

### 4. Deterministic Mutations
- All changes via `scripts/mutate.py`
- Operations ordered to respect dependencies
- Validation after all operations

---

## Expected User Experience

### Typical Happy Path

1. **User has discovery call transcript**
   ```bash
   /input-requirements input/discovery_2026-01-10.txt
   ```

2. **Agent asks batched clarifying questions**
   - User answers via AskUserQuestion interface
   - Agent generates approval file

3. **User reviews approval file**
   - Can edit manually if needed
   - Proceeds when satisfied

4. **User runs integration**
   ```bash
   /integrate-changes approvals/exam-purchasing.txt
   ```

5. **Agent presents mutation summary**
   - User approves execution
   - Mutations run sequentially
   - Reports regenerated

6. **User commits changes**
   ```bash
   git add .
   git commit -m "Add exam purchasing requirements"
   git push
   ```

---

## Files Created During Workflow

### Approval Files
```
approvals/
└── <descriptive-name>.txt    # Structured requirements for integration
```

### Repository Updates
```
data/
├── artifacts.json           # Business artifacts added/updated
├── requirements.json        # Requirements added/updated
├── features.json            # Features added/updated
├── epics.json               # Epics added/updated
├── stories.json             # Stories added/updated
└── releases.json            # Releases added/updated

reports/
├── graph.json               # Relationship graph rebuilt
└── index.json               # Lookup index rebuilt

docs/
├── index.html               # Landing page regenerated
├── releases/*.html          # Release pages regenerated
├── features/*.html          # Feature pages regenerated
├── epics/*.html             # Epic pages regenerated
├── stories/*.html           # Story pages regenerated
├── requirements/*.html      # Requirement pages regenerated
└── artifacts/               # Artifact docs (authored, not generated)
```

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/mutate.py` | All canonical JSON modifications |
| `scripts/validate.py` | Schema and reference integrity checks |
| `scripts/build_graph.py` | Generate `reports/graph.json` |
| `scripts/build_index.py` | Generate `reports/index.json` |
| `scripts/render_docs.py` | Generate HTML documentation |

---

## Document Version

**Version:** 2.0
**Updated:** 2026-01-15
**Status:** Simplified architecture (removed wrapper/clone pattern)
