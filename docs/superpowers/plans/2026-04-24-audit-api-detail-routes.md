# Audit API Detail Routes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement mock detail reads for `Project`, `Sample`, and `Analysis` resources through the existing product business API.

**Architecture:** Extend the existing `AuditMockService` and `AuditApiHandler`. Keep public JSON as camelCase, internal resources as `audit-common` snake_case dictionaries, and do not add persistence, Agent Server calls, MCP exposure, sandbox workers, or new parallel API modules.

**Tech Stack:** Python stdlib, `unittest`, existing `AuditMockService`, existing `AuditApiHandler`.

---

### Task 1: Service Detail Methods

**Files:**
- Modify: `apps/audit-api/tests/test_mock_service.py`
- Modify: `apps/audit-api/audit_api/mock_service.py`

- [x] **Step 1: Write failing service tests**

Add tests for `get_project("project_1")`, `get_sample("sample_1")`, and `get_analysis("analysis_1")` returning public camelCase detail dictionaries.

- [x] **Step 2: Run service tests to verify red**

Run targeted service tests.

Expected: `get_project` and `get_sample` fail with `AttributeError`; `get_analysis` already exists and passes.

- [x] **Step 3: Implement service methods**

Add `get_project` and `get_sample` to `AuditMockService`, reusing existing resource dictionaries and `_require_*` guards.

- [x] **Step 4: Run service tests to verify green**

Run targeted service tests.

Expected: PASS.

### Task 2: HTTP Detail Routes

**Files:**
- Modify: `apps/audit-api/tests/test_server.py`
- Modify: `apps/audit-api/audit_api/server.py`

- [x] **Step 1: Write failing route tests**

Add tests for `GET /api/projects/project_1`, `GET /api/samples/sample_1`, and `GET /api/analyses/analysis_1`.

- [x] **Step 2: Run route tests to verify red**

Run targeted handler tests.

Expected: detail routes fail with 404 before dispatch exists.

- [x] **Step 3: Implement route dispatch**

Extend `do_GET` to dispatch detail routes to the existing service. Keep specific `/events`, `/state`, and `/interrupts` routes ahead of generic analysis detail routing.

- [x] **Step 4: Run route tests to verify green**

Run targeted handler tests.

Expected: PASS.

### Task 3: Documentation and Validation

**Files:**
- Modify: `docs/blueprints/implementation-progress.md`
- Modify: `docs/blueprints/feature-registry.md`
- Modify: `docs/blueprints/decision-log.md`
- Modify: `docs/blueprints/openapi-contract.md`

- [x] **Step 1: Register detail support**

Mark project, sample, and analysis detail routes as mock implemented.

- [x] **Step 2: Record docs and duplicate checks**

Log official documentation links, adopted conclusions, and duplicate search commands.

- [x] **Step 3: Run final validation**

Run:

```bash
cd apps/audit-api && make format && make lint && make test
```

Expected: all API checks pass.

### Self-Review

- Scope coverage: only mock detail reads are implemented.
- Placeholder scan: no TODO placeholders; routes, methods, and validation commands are explicit.
- Boundary consistency: no Agent Server, MCP, persistence, sandbox, worker, or dynamic execution behavior is added.
