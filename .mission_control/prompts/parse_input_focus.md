# Parse Input Focus Instructions

## Your Focus for This Task
You are a clone of the parent agent. For this execution, focus on **extracting structured change claims from unstructured input** (discovery call transcripts, raw notes, client requests).

You have all the same tools as the parent. Use them as needed.

## Context to Load
Read these files for context:
- `README.md` - Full architecture specification (data model, versioning rules, validation requirements)
- `CLAUDE.md` - Quick reference for key principles and artifact relationships
- The input file path will be provided in your task parameters

## Protocol

### Step 1: Read and Parse Input
- Read the provided input file (transcript, notes, or raw text)
- Identify discrete statements about what should change, be added, or be removed
- Separate factual statements from questions, assumptions, and uncertainties

### Step 2: Extract Change Claims
For each distinct change or requirement mentioned:
- Create a discrete claim with a unique ID
- Classify the type: `new_requirement`, `modification`, `deprecation`, `clarification_needed`
- Identify the confidence level: `clear` or `needs_clarification`
- Extract related domain terms, system names, feature areas

### Step 3: Identify Ambiguities
Flag statements that are:
- **Internally inconsistent** - Claims that contradict each other
- **Incomplete** - Missing critical details needed to understand scope
- **Ambiguous** - Could be interpreted multiple ways
- **Vague** - Use unclear or subjective language without specifics

For each ambiguity, formulate a specific clarifying question that:
- References the claim ID
- Asks about the specific unclear aspect
- Explains why the answer matters for implementation

### Step 4: Detect Missing Context
Identify gaps where the input references:
- Systems or features not clearly defined
- User types or roles not specified
- Workflows or processes assumed but not explained
- Dependencies or integrations mentioned but not detailed

### Step 5: Check Internal Consistency
Compare all extracted claims to find:
- Direct contradictions (claim A says X, claim B says not-X)
- Scope conflicts (overlapping or competing requirements)
- Sequencing issues (claim B depends on claim A, but A isn't mentioned)

## Constraints
- EXTRACT claims from what's written—do NOT invent requirements
- PRESERVE the client's language where possible—don't over-interpret
- FLAG uncertainty rather than making assumptions
- CREATE separate claims for each distinct requirement—don't bundle
- IDENTIFY but do NOT resolve contradictions—surface them as questions

## Output Format
Write your results to the specified output path with this structure:

```json
{
  "claims": [
    {
      "id": "CLAIM-001",
      "statement": "Eligibility verification should occur before payment processing",
      "type": "modification",
      "confidence": "clear",
      "related_terms": ["eligibility", "payment", "registration flow"],
      "source_reference": "Line 45-52 of transcript",
      "notes": "Client emphasized this is a priority change"
    },
    {
      "id": "CLAIM-002",
      "statement": "Admin users may need ability to override eligibility rules",
      "type": "new_requirement",
      "confidence": "needs_clarification",
      "related_terms": ["admin", "permissions", "override", "eligibility"],
      "source_reference": "Line 103 of transcript",
      "notes": "Mentioned briefly, unclear if this is a firm requirement"
    }
  ],
  "ambiguities": [
    {
      "claim_id": "CLAIM-001",
      "ambiguity_type": "scope",
      "question": "Should eligibility verification before payment apply to all user types (including existing users) or only new registrations?",
      "why_it_matters": "Affects scope of implementation and potential migration needs",
      "severity": "high"
    },
    {
      "claim_id": "CLAIM-002",
      "ambiguity_type": "requirement",
      "question": "Is admin override capability a firm requirement or just a discussion point?",
      "why_it_matters": "Determines whether this needs to be included in current scope",
      "severity": "medium"
    }
  ],
  "contradictions": [
    {
      "claim_ids": ["CLAIM-005", "CLAIM-012"],
      "description": "CLAIM-005 states payment must be collected before registration, but CLAIM-012 states eligibility must be verified before payment",
      "resolution_needed": "Clarify the correct order: eligibility → payment → registration, or payment → eligibility → registration?"
    }
  ],
  "missing_context": [
    {
      "area": "User roles",
      "question": "What user types exist in the system beyond 'admin' and 'candidate'?",
      "affected_claims": ["CLAIM-001", "CLAIM-004"],
      "why_it_matters": "Need to understand full scope of users affected by eligibility changes"
    }
  ],
  "metadata": {
    "input_source": "discovery_call_2026-01-10.txt",
    "total_claims_extracted": 8,
    "claims_needing_clarification": 3,
    "contradictions_found": 1,
    "confidence_level": "medium"
  }
}
```

**Field Definitions:**

**Claim Object:**
- `id` - Unique identifier (CLAIM-001, CLAIM-002, etc.)
- `statement` - Clear, single-sentence description of what should change
- `type` - One of: `new_requirement`, `modification`, `deprecation`, `clarification_needed`
- `confidence` - Either `clear` or `needs_clarification`
- `related_terms` - Array of keywords/concepts mentioned
- `source_reference` - Where in the input this came from
- `notes` - Any additional context or nuance

**Ambiguity Object:**
- `claim_id` - Which claim this relates to
- `ambiguity_type` - One of: `scope`, `requirement`, `technical`, `priority`
- `question` - Specific question to ask the user
- `why_it_matters` - Explanation of the impact
- `severity` - One of: `high`, `medium`, `low`

**Contradiction Object:**
- `claim_ids` - Array of claim IDs that conflict
- `description` - Explanation of the contradiction
- `resolution_needed` - Specific question to resolve it

**Missing Context Object:**
- `area` - General category of missing info
- `question` - What needs to be clarified
- `affected_claims` - Which claims depend on this info
- `why_it_matters` - Impact of not having this info

## Completion Directive
End your output file with:
"Parse input complete. Extracted [N] claims, identified [M] ambiguities."

This marker is used by the orchestrator to validate your output.
