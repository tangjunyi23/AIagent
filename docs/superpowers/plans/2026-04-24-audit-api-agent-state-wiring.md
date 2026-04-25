# Audit API Agent State Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `AuditMockService.create_analysis` to the existing `apps/audit-agents.create_initial_state` helper and expose the mock latest state through the reserved state endpoint.

**Architecture:** Keep `apps/audit-agents` as the owner of `AuditAgentState` construction. Extend `apps/audit-api` to depend on that package, store one in-memory state per analysis, and return public camelCase state snapshots from `GET /api/analyses/{analysisId}/state`. Do not add Agent Server calls, checkpoint storage, or a parallel state schema.

**Tech Stack:** Python stdlib, `unittest`, existing `audit_agents.create_initial_state`, existing `AuditMockService`, existing `AuditApiHandler`.

---

### Task 1: Service State Wiring Tests

**Files:**
- Modify: `apps/audit-api/tests/test_mock_service.py`
- Modify: `apps/audit-api/audit_api/mock_service.py`
- Modify: `apps/audit-api/Makefile`
- Modify: `apps/audit-api/pyproject.toml`

- [ ] **Step 1: Write failing service tests**

Add tests that create a firmware analysis and assert:

```python
state = service.get_analysis_state(str(analysis["id"]))
self.assertEqual(state["analysis"]["id"], analysis["id"])
self.assertEqual(state["analysis"]["langgraphThreadId"], analysis["langgraphThreadId"])
self.assertEqual(state["approvalRequests"][0]["interruptId"], "interrupt_analysis_1_firmware_emulation")
self.assertEqual(state["artifacts"], [])
self.assertEqual(state["findings"], [])
self.assertEqual(state["toolExecutions"], [])
```

Add a decision test that approving an interrupt updates `state["approvalRequests"][0]["status"]` to `approved`.

- [ ] **Step 2: Run service tests to verify red**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_mock_service -v`

Expected: FAIL with missing `get_analysis_state` or missing `audit_agents` package wiring.

### Task 2: Service State Implementation

**Files:**
- Modify: `apps/audit-api/audit_api/mock_service.py`
- Modify: `apps/audit-api/Makefile`
- Modify: `apps/audit-api/pyproject.toml`

- [ ] **Step 1: Add package wiring**

Add `audit-agents` as an app dependency and include `../audit-agents` in `apps/audit-api/Makefile` `PYTHONPATH`.

- [ ] **Step 2: Store agent states**

Import `AuditAgentState` and `create_initial_state`, add `self._agent_states`, and populate it inside `create_analysis` using the generated analysis/thread IDs. Replace the generated state analysis with the API analysis object so policy and timestamps match the HTTP resource.

- [ ] **Step 3: Keep approvals/events in state synchronized**

After creating the deterministic approval and events, copy `approval_requests` and `events` into the stored state. After `decide_approval`, update the stored state approval and append the decision event.

- [ ] **Step 4: Run service tests to verify green**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_mock_service -v`

Expected: PASS.

### Task 3: HTTP State Endpoint Tests and Dispatch

**Files:**
- Modify: `apps/audit-api/tests/test_server.py`
- Modify: `apps/audit-api/audit_api/server.py`

- [ ] **Step 1: Write failing handler test**

Add a route test for `GET /api/analyses/analysis_1/state`, asserting `analysis.id`, `analysis.langgraphThreadId`, empty artifacts/findings/toolExecutions, and pending approval request.

- [ ] **Step 2: Run handler tests to verify red**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_server -v`

Expected: FAIL with 404 for the state endpoint.

- [ ] **Step 3: Implement route dispatch**

Extend existing `do_GET` to match `/api/analyses/{analysisId}/state` and return `service.get_analysis_state(analysis_id)`.

- [ ] **Step 4: Run handler tests to verify green**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_server -v`

Expected: PASS.

### Task 4: Documentation and Validation

**Files:**
- Modify: `docs/blueprints/implementation-progress.md`
- Modify: `docs/blueprints/feature-registry.md`
- Modify: `docs/blueprints/decision-log.md`
- Modify: `docs/blueprints/openapi-contract.md`
- Modify: `docs/blueprints/event-schema.md` only if the state payload contract changes

- [ ] **Step 1: Update feature registry and contracts**

Mark `GET /api/analyses/{analysisId}/state` as mock implemented and register `get_analysis_state`.

- [ ] **Step 2: Record official docs and duplicate checks**

Log `https://docs.langchain.com/mcp`, LangGraph overview, persistence, streaming, and LangGraph Platform conclusions.

- [ ] **Step 3: Run final validation**

Run: `cd apps/audit-api && make format && make lint && make test`

Expected: all API tests pass with the updated PYTHONPATH.

### Self-Review

- Spec coverage: connects API analysis creation to the existing agent state helper and exposes the reserved state route.
- Placeholder scan: no open-ended placeholders; exact methods, files, and commands are listed.
- Type consistency: internal state remains Python snake_case `AuditAgentState`; HTTP/service outputs are public camelCase dictionaries.
