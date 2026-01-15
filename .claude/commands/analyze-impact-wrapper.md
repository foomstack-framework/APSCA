---
description: Spawns clone to bind claims to repo structure and analyze full impact depth
allowed-tools: Task
---

# Analyze Impact Wrapper

This wrapper spawns a clone to bind change claims to the repository structure, assess complexity, and analyze impacts at multiple levels.

## Arguments

- `claims_file` - Path to structured claims JSON (from parse-input phase) (required)
- `output_file` - Path where impact analysis JSON should be written (required)

Example invocation:
```
SlashCommand('/analyze-impact-wrapper', { 
  claims_file: "work/claims.json",
  output_file: "work/impact_analysis.json"
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
<parameter name="description">Analyze impact depth</parameter>
<parameter name="subagent_type">general-purpose</parameter>
<parameter name="prompt">
## INITIALIZATION (Do this first)
Read your focus instructions from: .mission_control/prompts/analyze_impact_focus.md

## Your Task
Bind change claims to the repository structure and analyze their full impact.

**Claims file:** @claims_file
**Output file:** @output_file

Follow the protocol in your focus instructions to:
1. Load and understand the claims
2. Bind each claim to canonical structure (epics/stories)
3. Assess complexity signals (simple/moderate/complex)
4. Perform deep analysis for complex claims
5. Surface conflicts, trade-offs, questions, risk areas

Use the following files for traversal and lookup:
- data/epics.json
- data/stories.json
- reports/graph.json
- reports/index.json

Write your results as JSON to the output file specified above.
</parameter>
</invoke>
</function_calls>
