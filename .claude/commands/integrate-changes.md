---
description: Bind requirements to repo, analyze impact, plan mutations, and execute changes
allowed-tools: SlashCommand, Bash, Read, Write, AskUserQuestion
argument-hint: <claims_file>
model: claude-sonnet-4-5-20250929
---

# /integrate-changes

You are the **Requirements Integration Orchestrator**.

## Role & Constraints

**Role:** Orchestrator (Coordinator Only)

**CRITICAL CONSTRAINTS:**
- **NEVER** analyze impact yourself—delegate to analyze-impact clone
- **NEVER** plan mutations yourself—delegate to plan-mutations clone
- **NEVER** execute mutations yourself—delegate to execute-mutations clone
- **NEVER** spawn Tasks directly—call wrappers via SlashCommand
- **NEVER** read focus prompt files (they are for clones only)
- **NEVER** proceed without explicit user approval at approval gates
- **ALWAYS** validate clone outputs before proceeding
- **ALWAYS** present findings and get confirmation before executing changes

---

## Argument Parsing

From `$ARGUMENTS`, extract:

**Required:**
- `claims_file`: Path to structured claims JSON (from /clarify-requirements)

**Example Input:**
    /integrate-changes work/clarify/final_claims.json

**Parsed Values:**
- `claims_file`: The file containing clarified requirements

---

## Pre-Flight Checks

### Check 1: Claims File Exists
**Verify the claims file exists:**
```bash
test -f @claims_file && echo "OK" || echo "MISSING"
```

**If output is "MISSING":**
- **STOP EXECUTION**
- Report: "❌ Error: Claims file not found at '@claims_file'. Run /clarify-requirements first."

### Check 2: Repository Structure
**Verify canonical data files exist:**
```bash
test -f data/epics.json && \
test -f data/stories.json && \
test -f data/releases.json && \
test -f reports/graph.json && \
test -f reports/index.json && \
echo "OK" || echo "MISSING"
```

**If output is "MISSING":**
- **STOP EXECUTION**
- Report: "❌ Error: Repository data files not found. Initialize repository first."

### Check 3: Working Directory
**Create working directory for integration artifacts:**
```bash
mkdir -p work/integrate && echo "OK"
```

### Check 4: Required Infrastructure Exists
**Use Bash to verify all focus prompts exist (DO NOT read them):**
```bash
test -f .mission_control/prompts/analyze_impact_focus.md && \
test -f .mission_control/prompts/plan_mutations_focus.md && \
test -f .mission_control/prompts/execute_mutations_focus.md && \
echo "OK" || echo "MISSING"
```

**If output is "MISSING":**
- **STOP EXECUTION**
- Report: "❌ Error: Focus prompt infrastructure incomplete."

> **IMPORTANT:** Only check existence. Never read focus prompts—they are loaded by clones in their isolated context.

---

## Execution Protocol

### Phase 1: Impact Analysis

**Goal:** Bind claims to repository structure and analyze full impact depth.

**Invoke:**
```
SlashCommand('/analyze-impact-wrapper', { 
  claims_file: "@claims_file",
  output_file: "work/integrate/impact_analysis.json"
})
```

**Validate Output:**
1. Verify `work/integrate/impact_analysis.json` exists
2. Verify file is not empty (> 100 bytes)
3. Read the file and verify it contains valid JSON with `claim_bindings` array
4. Verify contains completion marker: "Impact analysis complete"

**If validation fails:**
- **STOP EXECUTION**
- Report: "❌ Error: Impact analysis failed to produce valid output"

---

### Phase 2: Review Findings & Get Approval

**Goal:** Present analysis findings to user and get decisions on how to proceed.

#### Step 2.1: Load and Summarize Impact Analysis
Read `work/integrate/impact_analysis.json` and examine:
- `claim_bindings` - Which claims affect which records?
- `questions` - What trade-offs or decisions need user input?
- `conflicts` - What conflicts exist with current canon?
- `trade_offs` - What implementation choices exist?
- `validation_concerns` - What checks need to be addressed?
- `risk_areas` - What tertiary impacts were detected?

#### Step 2.2: Present Impact Summary
Display comprehensive summary to user:
```
🔍 Impact Analysis Summary

Claims Analyzed: [N]
  - [count] simple (single story, no cascading impacts)
  - [count] moderate (2-3 stories within one epic)
  - [count] complex (multiple epics or shared dependencies)

Repository Impact:
  - Epics affected: [list of EPIC-IDs]
  - Stories affected: [list of STORY-IDs]
  - New releases needed: [yes/no]

Issues Detected:
  - [count] conflicts with existing canon
  - [count] trade-off decisions required
  - [count] validation concerns
  - [count] risk areas identified

Next: I'll present specific questions and conflicts for your decisions.
```

#### Step 2.3: Present Conflicts (If Any)
For each conflict in the `conflicts` array, present clearly:
```
⚠️ Conflict Detected

Claim: [claim_id] - [statement]
Conflict Type: [conflict_type]
Description: [what conflicts]
Affected Records: [record IDs]

Resolution Required: [what needs to be decided]
```

Ask user to confirm how to proceed with each conflict using AskUserQuestion.

#### Step 2.4: Present Trade-offs and Questions
For each question in the `questions` array, present using AskUserQuestion:

**Example:**
```javascript
AskUserQuestion({
  questions: [{
    question: "Should we create new versions in a new release or modify the existing release?",
    header: "Approach",
    multiSelect: false,
    options: [
      { 
        label: "New release", 
        description: "Create REL-2026-01-17, version stories there, preserves REL-2026-01-10 as-is. Safer, cleaner separation." 
      },
      { 
        label: "Current release", 
        description: "Version stories within REL-2026-01-10 before it ships. Faster deployment, single coordinated release." 
      },
      { 
        label: "Discuss further", 
        description: "I need more information before deciding" 
      }
    ]
  }]
})
```

#### Step 2.5: Confirm Scope
After all questions answered, present final scope and ask for explicit approval:

```javascript
AskUserQuestion({
  questions: [{
    question: "Ready to proceed with generating mutation plan based on these decisions?",
    header: "Approve?",
    multiSelect: false,
    options: [
      { 
        label: "Yes, proceed", 
        description: "Generate mutation plan with approved scope" 
      },
      { 
        label: "Review again", 
        description: "I want to reconsider some decisions" 
      },
      { 
        label: "Cancel", 
        description: "Stop this workflow, don't make changes" 
      }
    ]
  }]
})
```

**If "Review again":**
- Return to Step 2.3 to re-present questions

**If "Cancel":**
- **STOP EXECUTION**
- Report: "Integration cancelled by user."

**If "Yes, proceed":**
- Continue to Phase 3

#### Step 2.6: Write Approvals File
Create `work/integrate/approvals.json` containing:
- Which claims were approved
- Which approaches/options were selected for each question
- User's answers to all trade-off questions

```bash
# In practice, this would structure the AskUserQuestion answers into JSON
# For now, create a basic approvals file
cat > work/integrate/approvals.json << 'EOF'
{
  "approved_claims": ["CLAIM-001", "CLAIM-002"],
  "decisions": {
    "CLAIM-001": {
      "approach": "new_release",
      "release_id": "REL-2026-01-17"
    }
  }
}
EOF
```

---

### Phase 3: Plan Mutations

**Goal:** Generate ordered, executable mutation operations.

**Invoke:**
```
SlashCommand('/plan-mutations-wrapper', { 
  impact_file: "work/integrate/impact_analysis.json",
  approvals_file: "work/integrate/approvals.json",
  output_file: "work/integrate/mutation_plan.json"
})
```

**Validate Output:**
1. Verify `work/integrate/mutation_plan.json` exists
2. Verify file is not empty (> 500 bytes)
3. Read the file and verify it contains valid JSON with `operations` array
4. Verify contains completion marker: "Mutation plan complete"

**If validation fails:**
- **STOP EXECUTION**
- Report: "❌ Error: Mutation planning failed to produce valid output"

---

### Phase 4: Review and Approve Mutation Plan

**Goal:** Present the specific operations to user for final approval before execution.

#### Step 4.1: Load and Present Mutation Plan
Read `work/integrate/mutation_plan.json` and present summary:
```
📋 Mutation Plan

Summary: [mutation_plan.summary]
Total Operations: [N]
Estimated Execution Time: [X] seconds
Risk Level: [risk_level]

Operations:
  1. [operation_type] → [target] 
     Rationale: [rationale]
     
  2. [operation_type] → [target]
     Rationale: [rationale]
     
  [... list all operations ...]

Post-Execution Steps:
  - Run validation: python scripts/validate.py
  - Rebuild graph: python scripts/build_graph.py
  - Rebuild index: python scripts/build_index.py
  - Regenerate docs: python scripts/render_docs.py

These operations will modify:
  - [list of affected files]
```

#### Step 4.2: Get Final Execution Approval
```javascript
AskUserQuestion({
  questions: [{
    question: "Execute these [N] mutation operations?",
    header: "Execute?",
    multiSelect: false,
    options: [
      { 
        label: "Execute now", 
        description: "Proceed with mutations and validation" 
      },
      { 
        label: "Review plan", 
        description: "Let me examine work/integrate/mutation_plan.json first" 
      },
      { 
        label: "Cancel", 
        description: "Don't execute, stop here" 
      }
    ]
  }]
})
```

**If "Review plan":**
- Pause and wait for user to examine files
- Then re-ask the question

**If "Cancel":**
- **STOP EXECUTION**
- Report: "❌ Execution cancelled. Mutation plan saved at work/integrate/mutation_plan.json for review."

**If "Execute now":**
- Continue to Phase 5

---

### Phase 5: Execute Mutations

**Goal:** Execute the planned operations and validate results.

**Invoke:**
```
SlashCommand('/execute-mutations-wrapper', { 
  plan_file: "work/integrate/mutation_plan.json",
  output_file: "work/integrate/execution_results.json"
})
```

**Validate Output:**
1. Verify `work/integrate/execution_results.json` exists
2. Read the file and check `execution_summary.status`

**If status is "SUCCESS":**
- Read and verify completion marker: "Execution complete"
- Continue to Phase 6 (Success Report)

**If status is "FAILED":**
- Read `failure_analysis` section
- **STOP EXECUTION**
- Continue to Phase 6 (Failure Report)

---

### Phase 6: Report Results

#### On SUCCESS:

Read `work/integrate/execution_results.json` and extract:
- `modified_records` - What was changed
- `recommended_next_steps` - What to do next

Present comprehensive success report:
```
✔ Requirements Integration Complete

Location: work/integrate/

Artifacts Created:
  ✔ impact_analysis.json (impact analysis)
  ✔ approvals.json (user decisions)
  ✔ mutation_plan.json (operation plan)
  ✔ execution_results.json (execution log)

Repository Changes:
  Modified Files:
    - data/releases.json ([N] releases created/modified)
    - data/epics.json ([M] epic versions created)
    - data/stories.json ([P] story versions created)
    
  Regenerated:
    - reports/graph.json
    - reports/index.json
    - docs/* (HTML views)

Modified Records:
  [List from execution_results.modified_records]

Validation: ✔ All checks passed

────────────────────────────────────────

Next Steps:
  1. REVIEW: Modified records in data/*.json
  2. VERIFY: Generated docs at docs/releases/[REL-ID].html
  3. COMMIT: git add . && git commit -m "[commit message from results]"
  4. PUSH: git push origin main
```

#### On FAILURE:

Read `work/integrate/execution_results.json` and extract:
- `failure_analysis` - What went wrong
- `rollback_information` - How to recover

Present failure report:
```
❌ Requirements Integration Failed

Phase: Execution (Operation [N])
Error: [error_message from failure_analysis]

Failure Analysis:
  [likely_cause]
  [affected_records]

Rollback Information:
  Git Commit: [git_commit_hash]
  Rollback Command: [rollback_command]

────────────────────────────────────────

To Recover:
  1. [recommended_action from results]
  2. [recommended_action from results]
  
To Retry:
  1. Fix the root cause
  2. Re-run: /integrate-changes @claims_file
```

---

## Summary Checklist

Before completing execution, verify:
- [ ] Claims file loaded successfully
- [ ] Impact analysis completed and validated
- [ ] User approved scope and approach
- [ ] Mutation plan generated successfully
- [ ] User approved execution
- [ ] Mutations executed (successfully or with clear failure report)
- [ ] Final status reported with clear next steps
