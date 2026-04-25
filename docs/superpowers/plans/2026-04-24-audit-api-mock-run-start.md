# Audit API Mock Run Start Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement mock `POST /api/analyses/{analysisId}/runs` by invoking the existing supervisor skeleton without executing any dangerous tools.

**Architecture:** Extend `AuditMockService` with `start_run(analysis_id)` that assigns a mock `langgraph_run_id`, appends product `run.started` / `run.interrupted` events, invokes `apps/audit-agents.build_supervisor_graph().invoke(...)`, and synchronizes the in-memory `AuditAgentState`. Keep this as a product-layer mock; do not call Agent Server, MCP, sandbox workers, or real dynamic tooling.

**Tech Stack:** Python stdlib, `unittest`, existing `audit_agents.build_supervisor_graph`, existing `AuditMockService`, existing `AuditApiHandler`.

---

### Task 1: Supervisor Idempotency Test

**Files:**
- Modify: `apps/audit-agents/tests/test_supervisor.py`
- Modify: `apps/audit-agents/audit_agents/supervisor.py`

- [ ] **Step 1: Write failing duplicate-approval test**

Add a test where state already contains a pending `firmware-emulation` approval and `approval.requested` event. Invoking `request_dangerous_action_approval` should set status to `interrupted` but should not append a second approval.

- [ ] **Step 2: Run agent tests to verify red**

Run: `cd apps/audit-agents && make test`

Expected: FAIL because current supervisor always appends a new approval.

- [ ] **Step 3: Make approval gate idempotent**

Update `request_dangerous_action_approval` to detect an existing pending approval with action `firmware-emulation`. If present, set `analysis.status` to `interrupted` and return without appending duplicate approval/request event.

- [ ] **Step 4: Run agent tests to verify green**

Run: `cd apps/audit-agents && make test`

Expected: PASS.

### Task 2: Service Run Tests and Implementation

**Files:**
- Modify: `apps/audit-api/tests/test_mock_service.py`
- Modify: `apps/audit-api/audit_api/mock_service.py`

- [ ] **Step 1: Write failing service tests**

Add tests that create a firmware analysis and call `service.start_run("analysis_1")`. Assert response `status == "interrupted"`, `langgraphRunId == "run_1"`, event stream includes `run.started`, `agent.started`, and `run.interrupted`, and no duplicate pending approval is created.

- [ ] **Step 2: Run service tests to verify red**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_mock_service -v`

Expected: FAIL with missing `start_run`.

- [ ] **Step 3: Implement `start_run`**

Add `_next_run`, `_create_run_event`, and `start_run`. Set `analysis.langgraph_run_id`, append `run.started`, invoke `build_supervisor_graph().invoke`, merge state/events back into mock storage, append `run.interrupted`, and synchronize state.

- [ ] **Step 4: Run service tests to verify green**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_mock_service -v`

Expected: PASS.

### Task 3: HTTP Run Route Test and Dispatch

**Files:**
- Modify: `apps/audit-api/tests/test_server.py`
- Modify: `apps/audit-api/audit_api/server.py`

- [ ] **Step 1: Write failing route test**

Add a test for `POST /api/analyses/analysis_1/runs` that asserts `200`, `langgraphRunId == "run_1"`, `status == "interrupted"`, and SSE contains `event: run.interrupted`.

- [ ] **Step 2: Run handler tests to verify red**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_server -v`

Expected: FAIL with 404.

- [ ] **Step 3: Implement route dispatch**

Extend existing `do_POST` to match `/api/analyses/{analysisId}/runs` and return `service.start_run(analysis_id)`.

- [ ] **Step 4: Run handler tests to verify green**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_server -v`

Expected: PASS.

### Task 4: Documentation and Validation

**Files:**
- Modify: `docs/blueprints/implementation-progress.md`
- Modify: `docs/blueprints/feature-registry.md`
- Modify: `docs/blueprints/decision-log.md`
- Modify: `docs/blueprints/openapi-contract.md`
- Modify: `docs/blueprints/event-schema.md` only if event payloads change

- [ ] **Step 1: Register mock run support**

Mark `POST /api/analyses/{analysisId}/runs`, `run.started`, `run.interrupted`, and supervisor idempotency as mock implemented.

- [ ] **Step 2: Record docs and duplicate checks**

Log official documentation links and the duplicate search commands.

- [ ] **Step 3: Run final validation**

Run:

```bash
cd apps/audit-agents && make format && make lint && make test
cd apps/audit-api && make format && make lint && make test
```

Expected: all affected tests pass.

### Self-Review

- Spec coverage: starts mock runs, invokes supervisor skeleton, emits run/agent events, and keeps dangerous execution blocked.
- Placeholder scan: no placeholders; methods, routes, status values, and commands are explicit.
- Type consistency: public HTTP responses remain camelCase; internal state remains `AuditAgentState` with snake_case keys.
