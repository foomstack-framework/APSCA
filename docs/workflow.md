# APSCA Requirements Repository Workflow - Complete Implementation

## Overview

This document summarizes the complete master-clone architecture workflow for managing the APSCA requirements repository. The workflow consists of 2 orchestrators, 4 wrappers, and 4 focus prompts.

---

## Workflow Architecture

### Phase 1: Requirements Clarification (Conversational)

**Entry Point:** `/clarify-requirements <input_file>`

**Purpose:** Parse unstructured input (discovery transcripts, notes) and clarify requirements through interactive dialogue.

**Flow:**
```
User → /clarify-requirements input/transcript.txt
    ↓
    Calls: /parse-input-wrapper
        ↓ (spawns clone)
        Clone reads: parse_input_focus.md
        Clone extracts: structured claims, ambiguities, contradictions
        Clone outputs: work/clarify/claims.json
    ↓
    Parent reads claims.json
    ↓
    LOOP: AskUserQuestion for clarifications
        ↓ (until all high-severity issues resolved)
        Parent updates: work/clarify/answers.json
    ↓
    Parent creates: work/clarify/final_claims.json
    ↓
    Output: ✔ Requirements ready for integration
```

**Human Interaction Points:**
- Clarifying questions about ambiguous requirements
- Resolving contradictions
- Providing missing context
- Final confirmation before proceeding

**Output:** `work/clarify/final_claims.json` - Structured, unambiguous requirements

---

### Phase 2: Requirements Integration (Deterministic)

**Entry Point:** `/integrate-changes <claims_file>`

**Purpose:** Bind requirements to repo, analyze impact, plan mutations, execute changes with approval gates.

**Flow:**
```
User → /integrate-changes work/clarify/final_claims.json
    ↓
    Phase 1: Impact Analysis
        Calls: /analyze-impact-wrapper
            ↓ (spawns clone)
            Clone reads: analyze_impact_focus.md
            Clone loads: data/*.json, reports/*.json
            Clone analyzes: claim bindings, complexity, impacts
            Clone outputs: work/integrate/impact_analysis.json
        ↓
        Parent validates output
    ↓
    Phase 2: Review Findings
        Parent reads impact_analysis.json
        Parent presents: summary, conflicts, trade-offs
        ↓
        LOOP: AskUserQuestion for decisions
            ↓ (conflicts, approaches, scope)
            Parent records: work/integrate/approvals.json
        ↓
        Final approval gate
    ↓
    Phase 3: Plan Mutations
        Calls: /plan-mutations-wrapper
            ↓ (spawns clone)
            Clone reads: plan_mutations_focus.md
            Clone loads: impact_analysis.json, approvals.json, data/*.json
            Clone generates: mutation commands with proper ordering
            Clone outputs: work/integrate/mutation_plan.json
        ↓
        Parent validates output
    ↓
    Phase 4: Review Mutation Plan
        Parent presents: operation list, rationale, risks
        ↓
        AskUserQuestion: Execute approval gate
    ↓
    Phase 5: Execute Mutations
        Calls: /execute-mutations-wrapper
            ↓ (spawns clone)
            Clone reads: execute_mutations_focus.md
            Clone executes: mutation commands sequentially
            Clone validates: after each operation
            Clone rebuilds: graph.json, index.json, docs/
            Clone outputs: work/integrate/execution_results.json
        ↓
        Parent validates execution status
    ↓
    Phase 6: Report Results
        Success: Show modified records, next steps (commit/push)
        Failure: Show error, rollback info, recovery steps
```

**Human Interaction Points:**
- Reviewing impact analysis findings
- Resolving conflicts with existing canon
- Choosing implementation approaches (trade-offs)
- Final approval before execution
- (Optional) Reviewing mutation plan before execution

**Output:** Updated repository with new versions, validated and ready to commit

---

## Complete Artifact Inventory

### Orchestrators (User-Invoked Commands)

| Command | File | Purpose | Size |
|---------|------|---------|------|
| `/clarify-requirements` | `.claude/commands/clarify-requirements.md` | Parse and clarify requirements interactively | 7.5 KB |
| `/integrate-changes` | `.claude/commands/integrate-changes.md` | Bind, analyze, plan, execute changes | 13 KB |

### Wrappers (Agent-Invoked Sub-Commands)

| Command | File | Spawns Clone For | Size |
|---------|------|------------------|------|
| `/parse-input-wrapper` | `.claude/commands/parse-input-wrapper.md` | Extract claims from unstructured input | 2.0 KB |
| `/analyze-impact-wrapper` | `.claude/commands/analyze-impact-wrapper.md` | Bind claims and analyze impacts | 2.2 KB |
| `/plan-mutations-wrapper` | `.claude/commands/plan-mutations-wrapper.md` | Generate mutation operations | 2.4 KB |
| `/execute-mutations-wrapper` | `.claude/commands/execute-mutations-wrapper.md` | Execute and validate mutations | 2.1 KB |

### Focus Prompts (Clone Instructions)

| Focus Prompt | File | Read By | Size |
|--------------|------|---------|------|
| `parse_input_focus` | `.mission_control/prompts/parse_input_focus.md` | parse-input clone | 6.3 KB |
| `analyze_impact_focus` | `.mission_control/prompts/analyze_impact_focus.md` | analyze-impact clone | 11 KB |
| `plan_mutations_focus` | `.mission_control/prompts/plan_mutations_focus.md` | plan-mutations clone | 12 KB |
| `execute_mutations_focus` | `.mission_control/prompts/execute_mutations_focus.md` | execute-mutations clone | 10 KB |

**Total: 10 documents (2 orchestrators + 4 wrappers + 4 focus prompts)**

---

## Master-Clone Architecture Principles

### Context Isolation
- **Orchestrators** coordinate but never do heavy work
- **Wrappers** contain Task invocation blocks with guardrails
- **Clones** work in isolated 200k token context windows
- **Focus prompts** are read by clones, NOT by parent

### Guardrails Prevent Parent Execution
Every wrapper includes:
```markdown
<CRITICAL>
**STOP. DO NOT PROCESS ANYTHING BELOW THIS LINE.**
You are a DELIVERY MECHANISM ONLY—not an executor.
...
</CRITICAL>
```

### Dynamic Context Loading
Wrappers pass file paths as arguments using `@variable` pattern:
```
SlashCommand('/parse-input-wrapper', { 
  input_file: "@input_file",
  output_file: "work/claims.json"
})
```

### Validation at Every Phase
Orchestrators validate clone outputs before proceeding:
- File exists
- File not empty
- Contains expected JSON structure
- Contains completion marker

---

## Key Design Decisions

### 1. Two-Phase Separation
- **Phase 1 (Clarify):** Conversational, iterative, focused on understanding
- **Phase 2 (Integrate):** Deterministic, approval-gated, focused on execution

### 2. Progressive Complexity
- Claims start simple
- Deep analysis triggered only when complexity signals detected
- Conservative flagging (better to over-analyze than miss impacts)

### 3. Multiple Approval Gates
- After clarification (ready to proceed?)
- After impact analysis (approve scope and approach?)
- Before execution (execute these operations?)

### 4. Explicit Trade-offs
- Agent surfaces options with pros/cons
- Human makes final decisions
- Decisions recorded in approvals.json

### 5. Failure Transparency
- Every operation logs results
- Failures include rollback information
- Clear remediation steps provided

### 6. Deterministic Mutations
- All changes via scripts/mutate.py
- Operations ordered to respect dependencies
- JSON escaping handled carefully
- Validation after every operation

---

## Expected User Experience

### Typical Happy Path

1. **User has discovery call transcript**
   ```bash
   /clarify-requirements input/discovery_2026-01-10.txt
   ```

2. **Agent asks 3-4 clarifying questions**
   - User answers via AskUserQuestion interface
   - Agent loops until requirements are clear

3. **User proceeds to integration**
   ```bash
   /integrate-changes work/clarify/final_claims.json
   ```

4. **Agent presents impact analysis**
   - Shows which epics/stories affected
   - Presents conflicts and trade-offs
   - User makes decisions

5. **Agent presents mutation plan**
   - Lists specific operations
   - Shows affected files
   - User approves

6. **Agent executes mutations**
   - Sequential execution with validation
   - Rebuilds graph, index, docs
   - Reports success with next steps

7. **User commits changes**
   ```bash
   git add .
   git commit -m "REL-2026-01-17: Implement eligibility-first flow"
   git push
   ```

### Estimated Time
- Clarification: 5-15 minutes (depending on complexity)
- Integration: 2-5 minutes (mostly automated)
- Total: 10-20 minutes for complex changes

---

## Files Created During Workflow

### Working Directory Structure
```
work/
├── clarify/
│   ├── claims.json           # Initial parse output
│   ├── answers.json          # User clarification answers
│   └── final_claims.json     # Ready for integration
│
└── integrate/
    ├── impact_analysis.json  # Impact analysis results
    ├── approvals.json        # User decisions on scope/approach
    ├── mutation_plan.json    # Generated mutation operations
    └── execution_results.json # Execution log and validation
```

### Repository Updates
```
data/
├── releases.json             # New releases created
├── epics.json               # Epic versions added
└── stories.json             # Story versions added

reports/
├── graph.json               # Relationship graph rebuilt
└── index.json               # Lookup index rebuilt

docs/
├── releases/[REL-ID].html   # Generated release pages
├── epics/[EPIC-ID].html     # Generated epic pages
└── stories/[STORY-ID].html  # Generated story pages
```

---

## Next Steps

### 1. Build Mutation Scripts
The workflow references `scripts/mutate.py` which needs to be created:
- `create_release`
- `add_epic` / `create_epic_version` / `set_epic_version_status`
- `add_story` / `create_story_version` / `set_story_status`

### 2. Build Validation Script
`scripts/validate.py` - Validates canonical data integrity

### 3. Build Generator Scripts
- `scripts/build_graph.py` - Generate reports/graph.json
- `scripts/build_index.py` - Generate reports/index.json
- `scripts/render_docs.py` - Generate docs/*.html

### 4. Seed Repository
Create initial data/*.json files with seed data:
- Sample releases
- Sample epics
- Sample stories

### 5. Test Workflow
Run the complete workflow end-to-end with real APSCA requirements

---

## Maintenance Notes

### Adding New Operations
To add new mutation operations:
1. Update architecture spec with operation definition
2. Implement operation in `scripts/mutate.py`
3. Update `plan_mutations_focus.md` with command example
4. No changes needed to orchestrators/wrappers

### Adjusting Validation Rules
To change validation rules:
1. Update architecture spec with new rules
2. Implement in `scripts/validate.py`
3. Update `execute_mutations_focus.md` if needed
4. No changes needed to orchestrators/wrappers

### Tuning Question Flow
To adjust how questions are asked:
1. Modify orchestrator (clarify-requirements or integrate-changes)
2. Adjust AskUserQuestion calls
3. Focus prompts remain unchanged

---

## Architecture Compliance

✅ **Follows master-clone architecture**
- Orchestrators coordinate only
- Wrappers deliver Task payloads
- Clones do all heavy work

✅ **Context window isolation**
- Parent context stays clean
- Each clone gets fresh 200k tokens
- No cross-contamination

✅ **Deterministic data flow**
- Markdown never exists (JSON only)
- All mutations via scripts
- Dashboards read generated JSON

✅ **Single source of truth**
- data/*.json is canonical
- reports/*.json is derived
- docs/*.html is generated

✅ **Human-in-the-loop**
- Multiple approval gates
- Explicit decision points
- Clear rollback paths

---

## Success Criteria

The workflow is successful if:

1. ✅ Requirements extracted from transcripts accurately
2. ✅ Ambiguities surfaced and resolved
3. ✅ Impact analysis finds all affected records
4. ✅ No surprises during execution (all impacts known upfront)
5. ✅ Mutations execute cleanly with validation passing
6. ✅ Repository remains consistent and valid
7. ✅ User experience is smooth and efficient

---

## Document Version

**Version:** 1.0  
**Created:** 2026-01-13  
**Status:** Implementation Complete  
**Next:** Build mutation scripts and test workflow
