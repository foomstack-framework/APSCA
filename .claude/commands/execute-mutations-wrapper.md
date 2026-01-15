---
description: Spawns clone to execute mutation operations and validate results
allowed-tools: Task
---

# Execute Mutations Wrapper

This wrapper spawns a clone to execute the planned mutation operations via bash commands and validate the results.

## Arguments

- `plan_file` - Path to mutation plan JSON (from plan-mutations phase) (required)
- `output_file` - Path where execution results JSON should be written (required)

Example invocation:
```
SlashCommand('/execute-mutations-wrapper', { 
  plan_file: "work/mutation_plan.json",
  output_file: "work/execution_results.json"
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
<parameter name="description">Execute mutations</parameter>
<parameter name="subagent_type">general-purpose</parameter>
<parameter name="prompt">
## INITIALIZATION (Do this first)
Read your focus instructions from: .mission_control/prompts/execute_mutations_focus.md

## Your Task
Execute the planned mutation operations and validate results.

**Mutation plan file:** @plan_file
**Output file:** @output_file

Follow the protocol in your focus instructions to:
1. Pre-execution validation (git state, command syntax)
2. Execute operations sequentially with immediate validation
3. Post-execution full validation (validate.py, rebuild graph/index/docs)
4. Generate comprehensive execution summary

CRITICAL: Stop immediately on any operation failure. Do not continue to next operation.

Write your results as JSON to the output file specified above.
</parameter>
</invoke>
</function_calls>
