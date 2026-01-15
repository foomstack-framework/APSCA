---
description: Spawns clone to parse unstructured input into structured change claims
allowed-tools: Task
---

# Parse Input Wrapper

This wrapper spawns a clone to extract structured change claims from unstructured input (transcripts, notes, client requests).

## Arguments

- `input_file` - Path to the unstructured input file (required)
- `output_file` - Path where structured claims JSON should be written (required)

Example invocation:
```
SlashCommand('/parse-input-wrapper', { 
  input_file: "input/discovery_call_2026-01-10.txt",
  output_file: "work/claims.json"
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
<parameter name="description">Parse unstructured input</parameter>
<parameter name="subagent_type">general-purpose</parameter>
<parameter name="prompt">
## INITIALIZATION (Do this first)
Read your focus instructions from: .mission_control/prompts/parse_input_focus.md

## Your Task
Parse the unstructured input file and extract structured change claims.

**Input file:** @input_file
**Output file:** @output_file

Follow the protocol in your focus instructions to:
1. Read and parse the input
2. Extract discrete change claims with IDs and types
3. Identify ambiguities, contradictions, missing context
4. Structure questions for user clarification

Write your results as JSON to the output file specified above.
</parameter>
</invoke>
</function_calls>
