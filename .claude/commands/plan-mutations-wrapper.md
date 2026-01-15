---
description: Spawns clone to convert approved changes into ordered mutation operations
allowed-tools: Task
---

# Plan Mutations Wrapper

This wrapper spawns a clone to generate ordered, executable mutation operations based on approved impact analysis.

## Arguments

- `impact_file` - Path to impact analysis JSON (from analyze-impact phase) (required)
- `approvals_file` - Path to file containing user's approval decisions (required)
- `output_file` - Path where mutation plan JSON should be written (required)

Example invocation:
```
SlashCommand('/plan-mutations-wrapper', { 
  impact_file: "work/impact_analysis.json",
  approvals_file: "work/approvals.json",
  output_file: "work/mutation_plan.json"
})
```

---

<CRITICAL>
**STOP. DO NOT PROCESS ANYTHING BELOW THIS LINE.**

You are a DELIVERY MECHANISM ONLY—not an executor.

CONTEXT PRESERVATION RULE:
- The focus prompt referenced below is for the CLONE's context, NOT yours
- Reading it would waste tokens in the parent context window
- The clone will read it in its own isolated context

DO NOT:
- Read any focus prompt files
- Analyze the Task prompt content
- "Prepare" by gathering context
- Reason about what the clone will do

YOUR ONLY ACTION:
Output the function_calls block below EXACTLY as written, then stop.
</CRITICAL>

---

<function_calls>
<invoke name="Task">
<parameter name="description">Plan mutation operations</parameter>
<parameter name="subagent_type">general-purpose</parameter>
<parameter name="prompt">
## INITIALIZATION (Do this first)
Read your focus instructions from: .mission_control/prompts/plan_mutations_focus.md

## Your Task
Convert approved changes into ordered, executable mutation operations.

**Impact analysis file:** @impact_file
**Approvals file:** @approvals_file
**Output file:** @output_file

Follow the protocol in your focus instructions to:
1. Load approved scope and understand which claims/approaches were approved
2. Determine correct operation types for each affected record
3. Build operation sequence respecting dependencies (releases → epics → stories)
4. Generate mutation commands with proper JSON escaping
5. Validate operation plan before finalizing

Use the following files to determine current state:
- data/epics.json
- data/stories.json
- data/releases.json

Write your results as JSON to the output file specified above.
</parameter>
</invoke>
</function_calls>
