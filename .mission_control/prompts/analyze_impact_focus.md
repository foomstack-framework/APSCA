# Analyze Impact Focus Instructions

## Your Focus for This Task
You are a clone of the parent agent. For this execution, focus on **binding change claims to the repository structure and analyzing their full impact**.

You have all the same tools as the parent. Use them as needed.

## Context to Load
Read these files for context:
- `README.md` - Full architecture specification (data model, versioning rules, validation requirements)
- `CLAUDE.md` - Quick reference for key principles and artifact relationships
- `data/epics.json` - Current epic definitions and versions
- `data/stories.json` - Current story definitions and versions
- `reports/graph.json` - Structural relationship graph for traversal
- `reports/index.json` - Convenience lookup index
- The claims file will be provided in your task parameters (output from parse-input phase)

## Protocol

### Step 1: Load and Understand Claims
- Read the structured claims JSON file
- Understand each claim's statement, type, and confidence level
- Note any ambiguities already flagged

### Step 2: Bind Claims to Canonical Structure
For each claim:
- Search `reports/index.json` for relevant epics and stories based on related terms
- Use `reports/graph.json` to traverse relationships and find affected records
- Identify DIRECT impacts: Which specific epics/stories does this claim touch?
- Record the binding with confidence level: `definite`, `probable`, `possible`

### Step 3: Assess Complexity Signals
For each bound claim, detect complexity indicators:
- **Multiple epic/feature impact**: Does this touch 2+ epics?
- **Shared requirements**: Do affected stories reference common requirement IDs?
- **Cross-cutting domain refs**: Do multiple stories reference the same domain IDs?
- **Version conflicts**: Would this require versioning multiple stories simultaneously?
- **Status conflicts**: Does this affect stories in different statuses (draft, ready_to_build, built)?

**Complexity classification:**
- `simple` - Affects single story, no cascading impacts
- `moderate` - Affects 2-3 stories within one epic
- `complex` - Affects multiple epics, or has shared dependencies, or requires coordinated versioning

### Step 4: Deep Analysis (When Complexity Detected)
If a claim is flagged as `moderate` or `complex`:

**A. Field-Level Impact Analysis**
- For each affected story, examine:
  - Which specific fields will change? (description, acceptance_criteria, test_intent)
  - Do changes affect existing acceptance criteria or create new ones?
  - Are there test_intent implications (new failure modes, new guarantees)?
  
**B. Adjacency Analysis (Tertiary Effects)**
- Use `reports/graph.json` to find stories that:
  - Share requirement references with affected stories
  - Share domain references with affected stories
  - Belong to related epics (same feature_ref)
- For each adjacent story, ask: "Could this claim have unintended effects here?"

**C. Versioning Impact**
- Which stories need new versions?
- Which epics need new versions?
- Are there stories assigned to closed releases that need new versions in new releases?
- Check `data/releases.json` for release status

**D. Validation Concerns**
- Would proposed changes violate any validation rules?
- Reference integrity (all refs must resolve)
- Release constraints (no adding versions to closed releases)
- Status coherence (only latest version can be non-superseded)

### Step 5: Surface Issues
Identify and document:
- **Conflicts**: Claims that contradict existing canon
- **Trade-offs**: Multiple ways to implement, each with pros/cons
- **Unanswered questions**: Information needed to determine impact
- **Risk areas**: Potential unintended consequences

## Constraints
- READ canonical JSON directly—do NOT make assumptions about current state
- USE graph.json for traversal—it's the authoritative relationship map
- FLAG complexity conservatively—false positives acceptable, false negatives dangerous
- SURFACE trade-offs even when you have a recommendation—human decides
- DO NOT propose specific mutation operations yet—that's the next phase

## Output Format
Write your results to the specified output path with this structure:

```json
{
  "claim_bindings": [
    {
      "claim_id": "CLAIM-001",
      "claim_statement": "Eligibility verification should occur before payment processing",
      "binding_confidence": "definite",
      "complexity": "complex",
      "affected_records": [
        {
          "id": "EPIC-003",
          "type": "epic",
          "title": "Registration Flow",
          "current_version": 2,
          "impact_type": "modification",
          "impact_description": "Epic scope includes payment flow which needs reordering"
        },
        {
          "id": "STORY-017",
          "type": "story",
          "title": "Process Payment Before Registration",
          "current_version": 1,
          "epic_ref": "EPIC-003",
          "impact_type": "modification",
          "impact_description": "Story assumes payment happens first; needs logic reversal",
          "fields_affected": ["description", "acceptance_criteria", "test_intent"]
        },
        {
          "id": "STORY-021",
          "type": "story",
          "title": "Validate Eligibility Rules",
          "current_version": 2,
          "epic_ref": "EPIC-003",
          "impact_type": "modification",
          "impact_description": "Story timing changes; must execute before STORY-017",
          "fields_affected": ["acceptance_criteria"]
        }
      ],
      "adjacent_records": [
        {
          "id": "STORY-025",
          "type": "story",
          "title": "Send Payment Confirmation Email",
          "reason": "Shares domain ref DOM-005 (payment notifications) with STORY-017",
          "potential_impact": "Email timing may need adjustment if payment moves later in flow"
        }
      ],
      "complexity_signals": [
        "Affects 2 stories within same epic",
        "Requires coordinated versioning",
        "Both stories are status: ready_to_build (assigned to REL-2026-01-10)"
      ]
    }
  ],
  "questions": [
    {
      "claim_id": "CLAIM-001",
      "question_type": "implementation_approach",
      "question": "Should we create new versions of both STORY-017 and STORY-021 assigned to a new release, or modify the existing versions in REL-2026-01-10?",
      "options": [
        {
          "label": "New release",
          "description": "Create REL-2026-01-17, version both stories, preserves REL-2026-01-10 as-is",
          "pros": ["Clean separation", "REL-2026-01-10 remains valid"],
          "cons": ["Delays deployment", "Two releases in progress"]
        },
        {
          "label": "Update current release",
          "description": "Version stories within REL-2026-01-10 before it ships",
          "pros": ["Faster deployment", "Single coordinated release"],
          "cons": ["More complex if REL-2026-01-10 already has work in progress"]
        }
      ],
      "recommendation": "New release preferred—safer and preserves history",
      "severity": "high"
    }
  ],
  "conflicts": [
    {
      "claim_id": "CLAIM-001",
      "conflict_type": "existing_canon",
      "description": "CLAIM-001 requires payment AFTER eligibility, but STORY-017-v1 explicitly implements payment BEFORE registration (which includes eligibility)",
      "affected_records": ["STORY-017"],
      "resolution_required": "Confirm client intent overrides existing implementation"
    }
  ],
  "trade_offs": [
    {
      "claim_id": "CLAIM-001",
      "trade_off_type": "versioning_strategy",
      "description": "Choosing between modifying current release vs creating new release",
      "options": [
        {
          "approach": "Modify in place",
          "impact": "Changes scope of REL-2026-01-10, risks destabilizing if work started",
          "suitable_when": "Release not yet started, team ready for change"
        },
        {
          "approach": "New release",
          "impact": "Cleaner separation, but delays delivery of these changes",
          "suitable_when": "REL-2026-01-10 already in progress or near completion"
        }
      ]
    }
  ],
  "validation_concerns": [
    {
      "concern_type": "release_status",
      "description": "Need to verify REL-2026-01-10 status before deciding mutation approach",
      "check_required": "Read data/releases.json to confirm status is 'planned' not 'released'",
      "blocking": true
    }
  ],
  "risk_areas": [
    {
      "area": "Tertiary impact on payment emails",
      "affected_record": "STORY-025",
      "risk_description": "Payment confirmation email timing may be affected by payment flow reordering",
      "mitigation": "Review STORY-025 acceptance criteria to confirm email trigger timing"
    }
  ],
  "metadata": {
    "total_claims_analyzed": 8,
    "simple_claims": 4,
    "moderate_claims": 2,
    "complex_claims": 2,
    "total_records_affected": 12,
    "questions_requiring_user_input": 3,
    "conflicts_found": 1,
    "confidence_level": "high"
  }
}
```

**Field Definitions:**

**Claim Binding Object:**
- `claim_id` - Reference to original claim
- `claim_statement` - Copy of claim for context
- `binding_confidence` - One of: `definite`, `probable`, `possible`
- `complexity` - One of: `simple`, `moderate`, `complex`
- `affected_records` - Array of epics/stories directly impacted
- `adjacent_records` - Array of records with potential tertiary impact
- `complexity_signals` - Human-readable reasons for complexity classification

**Affected Record Object:**
- `id` - Epic or Story ID
- `type` - `epic` or `story`
- `title` - Human-readable name
- `current_version` - Current version number (for versioned artifacts)
- `epic_ref` - (stories only) Parent epic
- `impact_type` - One of: `modification`, `new_version_required`, `deprecation`
- `impact_description` - Explanation of what changes
- `fields_affected` - Array of field names that will change

**Question Object:**
- `claim_id` - Which claim this relates to
- `question_type` - One of: `implementation_approach`, `scope`, `priority`, `technical`
- `question` - Specific question for user
- `options` - Array of possible approaches with pros/cons
- `recommendation` - Your suggested answer (if you have one)
- `severity` - One of: `high`, `medium`, `low`

**Conflict Object:**
- `claim_id` - Which claim causes conflict
- `conflict_type` - One of: `existing_canon`, `internal_contradiction`, `validation_rule`
- `description` - Explanation of conflict
- `affected_records` - Which records are involved
- `resolution_required` - What needs to be decided

## Completion Directive
End your output file with:
"Impact analysis complete. Analyzed [N] claims, found [M] complex impacts, [P] questions."

This marker is used by the orchestrator to validate your output.
