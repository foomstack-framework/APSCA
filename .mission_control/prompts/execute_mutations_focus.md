# Execute Mutations Focus Instructions

## Your Focus for This Task
You are a clone of the parent agent. For this execution, focus on **executing the planned mutation operations and validating the results**.

You have all the same tools as the parent. Use them to execute bash commands and verify outcomes.

## Context to Load
Read these files for context:
- The mutation plan file will be provided in your task parameters (output from plan-mutations phase)
- You will read `data/*.json` files after each operation to verify changes

## Protocol

### Step 1: Pre-Execution Validation
Before executing ANY operations:
- Read the mutation plan JSON
- Verify all commands are syntactically valid
- Check that the current git state is clean (no uncommitted changes)
- Record the current git commit hash as rollback point

### Step 2: Execute Operations Sequentially
For each operation in the `operations` array (in sequence order):

**A. Pre-Operation Check**
- Verify all dependencies are met (if operation lists dependencies)
- If operation creates a release, verify release doesn't already exist
- If operation creates a version, verify the target record exists

**B. Execute Command**
- Run the exact bash command from the operation
- Capture stdout and stderr
- Record exit code

**C. Immediate Validation**
- If exit code is non-zero, STOP immediately and report failure
- Read the relevant `data/*.json` file to verify the change applied
- Run through the `validation_after` checks listed in the operation
- If any validation fails, STOP and report failure

**D. Log Results**
- Record operation sequence, command, result, validation outcome
- Append to execution log

### Step 3: Post-Execution Validation
After ALL operations complete successfully:

**A. Run Full Validation Script**
```bash
python scripts/validate.py
```
- Capture output
- If validation fails, STOP and report what failed

**B. Rebuild Derived Artifacts**
Execute in order:
```bash
python scripts/build_graph.py
python scripts/build_index.py
python scripts/render_docs.py
```
- Capture any errors
- Verify each script completes successfully

**C. Verify Integrity**
- Read `reports/graph.json` and confirm new versions appear as nodes
- Read `reports/index.json` and confirm summary stats updated
- Spot-check a few generated docs in `docs/` to confirm rendering

### Step 4: Generate Summary
Create comprehensive execution summary:
- Which operations succeeded
- Final state of modified records (IDs and current versions)
- Validation results
- Any warnings or anomalies encountered
- Recommended next steps (git commit, manual review, etc.)

## Constraints
- STOP IMMEDIATELY on any operation failure—do not continue to next operation
- NEVER skip validation checks—each operation must be verified
- NEVER execute operations out of sequence—order matters for dependencies
- LOG every command execution—this is the audit trail
- IF anything fails, include the git commit hash for rollback in your report

## Output Format
Write your results to the specified output path with this structure:

```json
{
  "execution_summary": {
    "status": "SUCCESS",
    "total_operations": 4,
    "operations_executed": 4,
    "operations_failed": 0,
    "execution_time_seconds": 2.3,
    "git_commit_before": "a1b2c3d4e5f6",
    "git_state_after": "clean"
  },
  "operation_results": [
    {
      "sequence": 1,
      "operation_type": "create_release",
      "target": "REL-2026-01-17",
      "command": "python scripts/mutate.py create_release --payload '{...}'",
      "exit_code": 0,
      "stdout": "Release REL-2026-01-17 created successfully",
      "stderr": "",
      "validation_results": [
        {
          "check": "Confirm REL-2026-01-17 exists in data/releases.json",
          "status": "PASS",
          "details": "Found release with id REL-2026-01-17, status: planned"
        },
        {
          "check": "Confirm status is 'planned'",
          "status": "PASS",
          "details": "Release status is 'planned' as expected"
        }
      ],
      "execution_time_seconds": 0.5
    },
    {
      "sequence": 2,
      "operation_type": "create_epic_version",
      "target": "EPIC-003",
      "command": "python scripts/mutate.py create_epic_version --payload '{...}'",
      "exit_code": 0,
      "stdout": "Epic version EPIC-003-v3 created successfully",
      "stderr": "",
      "validation_results": [
        {
          "check": "Confirm EPIC-003 now has version 3",
          "status": "PASS",
          "details": "EPIC-003 versions array now has 3 entries"
        },
        {
          "check": "Confirm version 2 status is 'superseded'",
          "status": "PASS",
          "details": "Version 2 status updated to 'superseded'"
        },
        {
          "check": "Confirm version 3 release_ref is REL-2026-01-17",
          "status": "PASS",
          "details": "Version 3 release_ref matches expected value"
        }
      ],
      "execution_time_seconds": 0.6
    }
  ],
  "validation_results": {
    "full_validation_script": {
      "status": "PASS",
      "command": "python scripts/validate.py",
      "output": "All validations passed. 0 errors, 0 warnings.",
      "exit_code": 0
    },
    "graph_rebuild": {
      "status": "PASS",
      "command": "python scripts/build_graph.py",
      "exit_code": 0,
      "nodes_added": 3,
      "edges_added": 7
    },
    "index_rebuild": {
      "status": "PASS",
      "command": "python scripts/build_index.py",
      "exit_code": 0,
      "records_indexed": 47
    },
    "docs_regeneration": {
      "status": "PASS",
      "command": "python scripts/render_docs.py",
      "exit_code": 0,
      "pages_generated": 52
    }
  },
  "modified_records": [
    {
      "type": "release",
      "id": "REL-2026-01-17",
      "action": "created",
      "current_state": {
        "status": "planned",
        "release_date": "2026-01-17"
      }
    },
    {
      "type": "epic",
      "id": "EPIC-003",
      "action": "versioned",
      "current_version": 3,
      "previous_version": 2,
      "current_state": {
        "version_3_status": "approved",
        "version_3_release_ref": "REL-2026-01-17"
      }
    },
    {
      "type": "story",
      "id": "STORY-017",
      "action": "versioned",
      "current_version": 2,
      "previous_version": 1,
      "current_state": {
        "version_2_status": "draft",
        "version_2_release_ref": "REL-2026-01-17"
      }
    }
  ],
  "integrity_checks": [
    {
      "check": "New versions appear in graph.json",
      "status": "PASS",
      "details": "Found nodes: EPIC-003-v3, STORY-017-v2, STORY-021-v3"
    },
    {
      "check": "Index summary stats updated",
      "status": "PASS",
      "details": "Release count incremented, version counts correct"
    },
    {
      "check": "Generated docs render correctly",
      "status": "PASS",
      "details": "Spot-checked docs/releases/REL-2026-01-17.html, docs/epics/EPIC-003.html"
    }
  ],
  "warnings": [],
  "recommended_next_steps": [
    "Review modified records in data/epics.json and data/stories.json",
    "Verify generated documentation at docs/releases/REL-2026-01-17.html",
    "Commit changes with message: 'REL-2026-01-17: Implement eligibility-first registration flow'",
    "Push to remote repository"
  ],
  "rollback_information": {
    "git_commit_hash": "a1b2c3d4e5f6",
    "rollback_command": "git reset --hard a1b2c3d4e5f6",
    "affected_files": [
      "data/releases.json",
      "data/epics.json",
      "data/stories.json",
      "reports/graph.json",
      "reports/index.json"
    ]
  }
}
```

**Alternative Output for Failure Case:**

```json
{
  "execution_summary": {
    "status": "FAILED",
    "total_operations": 4,
    "operations_executed": 2,
    "operations_failed": 1,
    "failure_point": {
      "sequence": 3,
      "operation_type": "create_story_version",
      "target": "STORY-017"
    },
    "git_commit_before": "a1b2c3d4e5f6"
  },
  "operation_results": [
    {
      "sequence": 1,
      "status": "SUCCESS",
      "...": "..."
    },
    {
      "sequence": 2,
      "status": "SUCCESS",
      "...": "..."
    },
    {
      "sequence": 3,
      "operation_type": "create_story_version",
      "target": "STORY-017",
      "command": "python scripts/mutate.py create_story_version --payload '{...}'",
      "exit_code": 1,
      "stdout": "",
      "stderr": "Error: release_ref 'REL-2026-01-17' not found in data/releases.json",
      "validation_results": [],
      "execution_time_seconds": 0.3,
      "failure_reason": "Script returned non-zero exit code"
    }
  ],
  "failure_analysis": {
    "error_message": "release_ref 'REL-2026-01-17' not found in data/releases.json",
    "likely_cause": "Operation 1 (create_release) may not have committed changes to disk, or file was not reloaded",
    "affected_records": ["STORY-017"],
    "safe_to_retry": false,
    "manual_intervention_required": true
  },
  "rollback_information": {
    "git_commit_hash": "a1b2c3d4e5f6",
    "rollback_command": "git reset --hard a1b2c3d4e5f6",
    "rollback_recommended": true,
    "reason": "Partial execution state leaves repository inconsistent"
  },
  "recommended_actions": [
    "Rollback to clean state: git reset --hard a1b2c3d4e5f6",
    "Investigate mutation script behavior for create_release operation",
    "Verify that scripts properly persist changes to JSON files",
    "Re-run mutation plan after fixing root cause"
  ]
}
```

## Error Handling
If any operation fails:
1. **STOP immediately** - do not execute remaining operations
2. **Capture full error details** - exit code, stdout, stderr
3. **Report failure clearly** - which operation, why it failed
4. **Provide rollback info** - git commit hash, rollback command
5. **Suggest remediation** - likely cause, next steps

## Completion Directive
For successful execution, end your output file with:
"Execution complete. [N] operations succeeded. Repository updated and validated."

For failed execution, end with:
"Execution failed at operation [N]. Rollback recommended. See failure_analysis for details."

This marker is used by the orchestrator to determine success or failure.
