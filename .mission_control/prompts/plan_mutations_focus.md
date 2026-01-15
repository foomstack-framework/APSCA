# Plan Mutations Focus Instructions

## Your Focus for This Task
You are a clone of the parent agent. For this execution, focus on **converting approved changes into ordered, executable mutation operations** using the mutation scripts.

You have all the same tools as the parent. Use them as needed.

## Context to Load
Read these files for context:
- `README.md` - Full architecture specification (mutation operations, versioning rules, validation requirements)
- `CLAUDE.md` - Quick reference for key principles and artifact relationships
- `data/epics.json` - Current epic state (to determine version numbers)
- `data/stories.json` - Current story state (to determine version numbers)
- `data/releases.json` - Current release state (to validate release refs)
- The impact analysis file will be provided in your task parameters (output from analyze-impact phase)
- The user's approval decisions will be provided (which claims approved, which approaches chosen)

## Protocol

### Step 1: Load Approved Scope
- Read the impact analysis JSON
- Read the approval decisions (which claims were approved, answers to questions)
- Understand which records need mutation and what type of changes

### Step 2: Determine Operation Types
For each affected record, determine the correct mutation operation:

**For New Releases:**
- `create_release` - Must execute before any versions can reference it

**For Epics:**
- `add_epic` - If creating a brand new epic
- `create_epic_version` - If adding a new version to existing epic
- `set_epic_version_status` - If only changing status (draft → approved)

**For Stories:**
- `add_story` - If creating a brand new story
- `create_story_version` - If adding a new version to existing story
- `set_story_status` - If only changing status (draft → ready_to_build → in_build → built)

### Step 3: Build Operation Sequence
Order operations to respect dependencies:

1. **Release operations first** - Any new releases must exist before versions reference them
2. **Epic operations before story operations** - If creating new epic, do it before stories reference it
3. **Version operations in dependency order** - If story A depends on story B, handle B first
4. **Status operations last** - Change status after all structural changes complete

### Step 4: Generate Mutation Commands
For each operation, generate the correct bash command:

**Release Creation:**
```bash
python scripts/mutate.py create_release --payload '{
  "id": "REL-2026-01-17",
  "release_date": "2026-01-17",
  "description": "Eligibility flow reordering and admin override capability"
}'
```

**Epic Version Creation:**
```bash
python scripts/mutate.py create_epic_version --payload '{
  "epic_id": "EPIC-003",
  "release_ref": "REL-2026-01-17",
  "summary": "Updated registration flow with eligibility-first approach",
  "assumptions": ["Payment gateway supports deferred charging", "Users understand new flow"],
  "constraints": ["Must maintain backward compatibility for in-flight registrations"],
  "requirement_refs": ["REQ-042", "REQ-043"],
  "domain_refs": ["DOM-001", "DOM-005"]
}'
```

**Story Version Creation:**
```bash
python scripts/mutate.py create_story_version --payload '{
  "story_id": "STORY-017",
  "release_ref": "REL-2026-01-17",
  "description": "As a candidate, I want eligibility verified before payment so that I don'\''t pay for ineligible registrations",
  "requirement_refs": ["REQ-042"],
  "domain_refs": ["DOM-001"],
  "acceptance_criteria": [
    {
      "id": "AC-001",
      "statement": "System must verify eligibility before presenting payment form",
      "notes": null
    },
    {
      "id": "AC-002",
      "statement": "Ineligible candidates must see clear messaging explaining why registration is unavailable",
      "notes": null
    }
  ],
  "test_intent": {
    "failure_modes": ["Eligible user blocked from payment", "Ineligible user completes payment"],
    "guarantees": ["All payments are from eligible candidates", "Eligibility check completes within 2 seconds"],
    "exclusions": ["Payment gateway integration testing (covered by STORY-018)"]
  }
}'
```

**Status Changes:**
```bash
python scripts/mutate.py set_story_status --payload '{
  "story_id": "STORY-017",
  "version": 2,
  "status": "ready_to_build"
}'
```

### Step 5: Validate Operation Plan
Before finalizing, verify:
- All `release_ref` values reference releases that will exist (either existing or created earlier in sequence)
- All `epic_ref` values reference epics that will exist
- Version numbers are correct (next version = current_version + 1)
- No operations attempt to modify closed releases (status: `released` or `superseded`)
- JSON payloads are valid (proper escaping, no syntax errors)
- Operation order respects dependencies

### Step 6: Add Safety Checks
For each command, note any validation that should be confirmed after execution:
- Reference integrity (all refs resolve)
- Version lineage (supersedes chain is correct)
- Status coherence (only latest version is non-superseded)

## Constraints
- GENERATE valid bash commands—test JSON escaping carefully
- ORDER operations to respect dependencies—releases before versions
- INCLUDE all required fields in payloads—check spec for required vs optional
- DO NOT generate operations for unapproved claims
- VALIDATE release refs—do not reference non-existent releases
- ESCAPE single quotes in JSON strings using `'\''` pattern
- USE monotonically increasing version numbers—read current state to determine next version

## Output Format
Write your results to the specified output path with this structure:

```json
{
  "mutation_plan": {
    "summary": "Create new release REL-2026-01-17, version EPIC-003 and 2 stories to implement eligibility-first flow",
    "total_operations": 4,
    "estimated_execution_time": "2-3 seconds",
    "risk_level": "medium"
  },
  "operations": [
    {
      "sequence": 1,
      "operation_type": "create_release",
      "target": "REL-2026-01-17",
      "rationale": "New release required for coordinated versioning of EPIC-003, STORY-017, STORY-021",
      "command": "python scripts/mutate.py create_release --payload '{\"id\": \"REL-2026-01-17\", \"release_date\": \"2026-01-17\", \"description\": \"Eligibility flow reordering and admin override capability\"}'",
      "validation_after": [
        "Confirm REL-2026-01-17 exists in data/releases.json",
        "Confirm status is 'planned'"
      ]
    },
    {
      "sequence": 2,
      "operation_type": "create_epic_version",
      "target": "EPIC-003",
      "rationale": "Epic scope changes to reflect eligibility-first approach",
      "dependencies": ["REL-2026-01-17 must exist"],
      "command": "python scripts/mutate.py create_epic_version --payload '{\"epic_id\": \"EPIC-003\", \"release_ref\": \"REL-2026-01-17\", \"summary\": \"Updated registration flow with eligibility-first approach\", \"assumptions\": [\"Payment gateway supports deferred charging\"], \"constraints\": [\"Must maintain backward compatibility\"], \"requirement_refs\": [\"REQ-042\"], \"domain_refs\": [\"DOM-001\"]}'",
      "validation_after": [
        "Confirm EPIC-003 now has version 3",
        "Confirm version 2 status is 'superseded'",
        "Confirm version 3 release_ref is REL-2026-01-17"
      ]
    },
    {
      "sequence": 3,
      "operation_type": "create_story_version",
      "target": "STORY-017",
      "rationale": "Story logic reverses payment/eligibility order",
      "dependencies": ["REL-2026-01-17 must exist", "EPIC-003-v3 should exist (for context, not enforced)"],
      "command": "python scripts/mutate.py create_story_version --payload '{\"story_id\": \"STORY-017\", \"release_ref\": \"REL-2026-01-17\", \"description\": \"As a candidate, I want eligibility verified before payment so that I don'\\''t pay for ineligible registrations\", \"requirement_refs\": [\"REQ-042\"], \"domain_refs\": [\"DOM-001\"], \"acceptance_criteria\": [{\"id\": \"AC-001\", \"statement\": \"System must verify eligibility before presenting payment form\", \"notes\": null}], \"test_intent\": {\"failure_modes\": [\"Eligible user blocked from payment\", \"Ineligible user completes payment\"], \"guarantees\": [\"All payments are from eligible candidates\"], \"exclusions\": [\"Payment gateway integration testing\"]}}'",
      "validation_after": [
        "Confirm STORY-017 now has version 2",
        "Confirm version 1 status is 'superseded'",
        "Confirm version 2 release_ref is REL-2026-01-17"
      ]
    },
    {
      "sequence": 4,
      "operation_type": "create_story_version",
      "target": "STORY-021",
      "rationale": "Story timing changes to execute before payment",
      "dependencies": ["REL-2026-01-17 must exist"],
      "command": "python scripts/mutate.py create_story_version --payload '{\"story_id\": \"STORY-021\", \"release_ref\": \"REL-2026-01-17\", \"description\": \"As a system, I validate candidate eligibility against current rules\", \"requirement_refs\": [\"REQ-042\"], \"domain_refs\": [\"DOM-001\"], \"acceptance_criteria\": [{\"id\": \"AC-001\", \"statement\": \"Eligibility check completes within 2 seconds\", \"notes\": \"Performance requirement\"}], \"test_intent\": {\"failure_modes\": [\"Slow eligibility check blocks user\", \"Eligibility check returns false positive\"], \"guarantees\": [\"Eligibility determination is accurate\"], \"exclusions\": []}}'",
      "validation_after": [
        "Confirm STORY-021 now has version 3",
        "Confirm version 2 status is 'superseded'",
        "Confirm version 3 release_ref is REL-2026-01-17"
      ]
    }
  ],
  "rollback_plan": {
    "description": "If validation fails, manually inspect data/*.json and restore from git",
    "git_commit_before": "Ensure clean git state before execution",
    "validation_script": "python scripts/validate.py"
  },
  "post_execution_steps": [
    "Run validation: python scripts/validate.py",
    "Rebuild graph: python scripts/build_graph.py",
    "Rebuild index: python scripts/build_index.py",
    "Regenerate docs: python scripts/render_docs.py",
    "Verify changes in data/epics.json, data/stories.json, data/releases.json",
    "Commit changes to git with message: 'REL-2026-01-17: Implement eligibility-first registration flow'"
  ],
  "metadata": {
    "claims_implemented": ["CLAIM-001"],
    "records_modified": {
      "releases_created": 1,
      "epic_versions_created": 1,
      "story_versions_created": 2
    },
    "confidence_level": "high",
    "review_recommended": true
  }
}
```

**Field Definitions:**

**Operation Object:**
- `sequence` - Execution order (starts at 1)
- `operation_type` - Mutation operation name
- `target` - Record ID being mutated
- `rationale` - Why this operation is needed
- `dependencies` - What must exist before this runs (optional)
- `command` - Exact bash command to execute
- `validation_after` - Checks to perform after execution

**Important Notes on JSON Escaping:**
- Single quotes inside JSON strings must be escaped as: `'\''`
- Example: `"I don't"` becomes `"I don'\''t"`
- Entire JSON payload is wrapped in single quotes: `--payload '{ ... }'`
- All JSON strings inside use double quotes: `"field": "value"`

## Completion Directive
End your output file with:
"Mutation plan complete. [N] operations sequenced, ready for execution."

This marker is used by the orchestrator to validate your output.
