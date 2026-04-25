# Audit API Mock Run Resume Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a safe mock run resume endpoint that consumes an approved dangerous-action gate and completes the mock run without executing sandboxed or dynamic tooling.

**Architecture:** Extend `AuditMockService` with `resume_run(analysis_id)` and `AuditApiHandler` with `POST /api/analyses/{analysisId}/runs:resume`. The service requires an existing mock run and an approved `firmware-emulation` approval, emits product-owned `run.resumed` and `run.succeeded` events, updates `AuditAgentState`, and does not call Agent Server, MCP, checkpoints, workers, or tools.

**Tech Stack:** Python stdlib, `unittest`, existing `AuditMockService`, existing `AuditApiHandler`.

---

### Task 1: Service Resume Tests and Implementation

**Files:**
- Modify: `apps/audit-api/tests/test_mock_service.py`
- Modify: `apps/audit-api/audit_api/mock_service.py`

- [x] **Step 1: Write failing service tests**

Add tests for approved resume completion and unapproved resume rejection.

- [x] **Step 2: Run service tests to verify red**

Expected: FAIL with missing `resume_run`.

- [x] **Step 3: Implement `resume_run`**

Require an existing `langgraph_run_id` and approved `firmware-emulation` approval. Emit `run.resumed` and `run.succeeded`, set status `succeeded`, and sync state. Do not execute tools.

- [x] **Step 4: Run service tests to verify green**

Expected: PASS.

### Task 2: HTTP Resume Route

**Files:**
- Modify: `apps/audit-api/tests/test_server.py`
- Modify: `apps/audit-api/audit_api/server.py`

- [x] **Step 1: Write failing route test**

Add a test for `POST /api/analyses/analysis_1/runs:resume` after approval.

- [x] **Step 2: Run route test to verify red**

Expected: FAIL with 404.

- [x] **Step 3: Implement route dispatch**

Add `/runs:resume` dispatch before the existing `/runs` dispatch.

- [x] **Step 4: Run route test to verify green**

Expected: PASS.

### Task 3: Documentation and Validation

**Files:**
- Modify: `docs/blueprints/implementation-progress.md`
- Modify: `docs/blueprints/feature-registry.md`
- Modify: `docs/blueprints/decision-log.md`
- Modify: `docs/blueprints/openapi-contract.md`

- [x] **Step 1: Register resume support**

Mark `POST /api/analyses/{analysisId}/runs:resume` as mock implemented and register `resume_run`.

- [x] **Step 2: Record docs and duplicate checks**

Log official documentation links, adopted conclusions, and duplicate search commands.

- [x] **Step 3: Run final validation**

Run:

```bash
cd apps/audit-api && make format && make lint && make test
```

Expected: all API checks pass.

### Self-Review

- Scope coverage: only mock resume is implemented.
- Safety: approved dangerous-action requests are acknowledged, but no dynamic execution or tool execution is launched.
- Boundary consistency: no Agent Server, MCP, checkpoint persistence, worker, sandbox, or LangGraph `Command(resume=...)` integration is added.
