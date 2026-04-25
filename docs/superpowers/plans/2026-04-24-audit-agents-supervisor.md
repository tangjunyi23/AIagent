# Audit Agents Supervisor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the minimal `apps/audit-agents` LangGraph supervisor skeleton for the binary audit platform.

**Architecture:** Add a focused Python app package that imports shared product contracts from `libs/audit-common`, defines an `AuditAgentState`, builds a minimal supervisor `StateGraph`, and exposes deterministic node functions for triage and dangerous-action approval placeholders. Keep LangGraph integration product-owned and avoid modifying core LangGraph libraries.

**Tech Stack:** Python 3.10+, `langgraph`, `audit-common`, stdlib `unittest`, `make` commands mirroring the monorepo library pattern.

---

### Task 1: Package Skeleton and State Contract

**Files:**
- Create: `apps/audit-agents/pyproject.toml`
- Create: `apps/audit-agents/Makefile`
- Create: `apps/audit-agents/README.md`
- Create: `apps/audit-agents/audit_agents/__init__.py`
- Create: `apps/audit-agents/audit_agents/state.py`
- Test: `apps/audit-agents/tests/test_state.py`

- [ ] **Step 1: Write failing tests**

```python
from audit_agents.state import create_initial_state


def test_create_initial_state_uses_audit_common_contract_names() -> None:
    state = create_initial_state(
        analysis_id="analysis_123",
        project_id="project_123",
        sample_ids=["sample_123"],
        scenario="firmware",
        thread_id="thread_123",
    )

    assert state["analysis"]["status"] == "queued"
    assert state["analysis"]["sample_ids"] == ["sample_123"]
    assert state["events"] == []
    assert state["approval_requests"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/audit-agents && TEST=tests/test_state.py make test`
Expected: FAIL with `ModuleNotFoundError: No module named 'audit_agents'`.

- [ ] **Step 3: Implement minimal state code**

Create `AuditAgentState` with product-owned state fields and `create_initial_state(...)` returning an `Analysis` object compatible with `audit_common.schemas`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/audit-agents && TEST=tests/test_state.py make test`
Expected: PASS.

### Task 2: Supervisor Graph and Approval Placeholder

**Files:**
- Create: `apps/audit-agents/audit_agents/supervisor.py`
- Test: `apps/audit-agents/tests/test_supervisor.py`

- [ ] **Step 1: Write failing tests**

```python
from audit_agents.state import create_initial_state
from audit_agents.supervisor import build_supervisor_graph, request_dangerous_action_approval, triage_sample


def test_triage_sample_adds_agent_event() -> None:
    state = create_initial_state(
        analysis_id="analysis_123",
        project_id="project_123",
        sample_ids=["sample_123"],
        scenario="firmware",
        thread_id="thread_123",
    )

    update = triage_sample(state)

    assert update["analysis"]["status"] == "running"
    assert update["events"][0]["type"] == "agent.started"


def test_approval_placeholder_creates_request_without_running_tool() -> None:
    state = create_initial_state(
        analysis_id="analysis_123",
        project_id="project_123",
        sample_ids=["sample_123"],
        scenario="firmware",
        thread_id="thread_123",
    )

    update = request_dangerous_action_approval(state)

    assert update["analysis"]["status"] == "interrupted"
    assert update["approval_requests"][0]["action"] == "firmware-emulation"
    assert update["events"][0]["type"] == "approval.requested"


def test_build_supervisor_graph_compiles() -> None:
    graph = build_supervisor_graph()

    assert graph is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/audit-agents && TEST=tests/test_supervisor.py make test`
Expected: FAIL with `ModuleNotFoundError: No module named 'audit_agents.supervisor'`.

- [ ] **Step 3: Implement minimal supervisor code**

Create deterministic node functions and a compiled `StateGraph` with `triage` then `approval_gate` then `END`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/audit-agents && TEST=tests/test_supervisor.py make test`
Expected: PASS.

### Task 3: Documentation and Validation

**Files:**
- Modify: `docs/blueprints/implementation-progress.md`
- Modify: `docs/blueprints/feature-registry.md`
- Modify: `docs/blueprints/decision-log.md`
- Modify: `docs/blueprints/openapi-contract.md`

- [ ] **Step 1: Update docs**

Record official docs checked, duplicate function check commands, files changed, and minimal validation output. Register `apps/audit-agents` as implemented skeleton and add the decision to keep dangerous action nodes as approval placeholders until real sandbox workers exist.

- [ ] **Step 2: Run validation**

Run: `cd apps/audit-agents && make format && make lint && make test`
Expected: all commands exit 0.
