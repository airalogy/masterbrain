# AIRA Endpoint

`POST /api/endpoints/aira` implements AIRA, short for AI Research Automation.

## What it does

The endpoint executes one step of a structured research workflow based on the current workflow state.

The current router dispatches among six core AI methods:

1. Generate research goal
2. Generate research strategy
3. Select the next protocol
4. Generate initial values for fields in the next protocol
5. Generate phased research conclusion
6. Generate final research conclusion

## Dispatch model

The backend reads `workflow_data.path_data.path_status` and maps that state to the correct function.

Current statuses include:

- `waiting_for_research_goal`
- `waiting_for_research_strategy`
- `waiting_for_next_protocol`
- `waiting_for_initial_values_for_fields_in_next_protocol`
- `waiting_for_phased_research_conclusion`
- `waiting_for_final_research_conclusion`

Each successful step returns a typed structure that appends or updates the current path data.

## Core payload shape

At a high level, the request carries:

```json
{
  "model": {
    "name": "..."
  },
  "workflow_data": {
    "workflow_info": {},
    "protocols_info": {},
    "path_data": {
      "path_status": "waiting_for_research_goal",
      "steps": []
    }
  }
}
```

The response is not free-form text. It is a structured state transition such as:

- `AddResearchGoal`
- `AddResearchStrategy`
- `AddNextProtocol`
- `AddInitialValuesForFieldsInNextProtocol`
- `AddPhasedResearchConclusion`
- `AddFinalResearchConclusion`

## Why it is state-driven

AIRA is not modeled as one long prompt that re-derives the entire workflow from scratch on every request. Instead, it advances an explicit workflow state.

That approach makes it easier to:

- inspect intermediate steps
- rerun or branch a workflow
- validate transitions
- build UI around the current phase
- test each step independently

The implementation lives under `packages/masterbrain/src/masterbrain/endpoints/aira/`.
