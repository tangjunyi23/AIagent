# Audit API Mock Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `apps/audit-api` as a minimal business API mock layer for frontend and agent integration development.

**Architecture:** Add a small Python package that owns public HTTP JSON naming conversion, in-memory business resources, and mock SSE event formatting. Keep the API layer separate from native LangGraph/Agent Server routes and use `audit-common` schema names internally.

**Tech Stack:** Python 3.10+, stdlib `unittest`, stdlib `http.server` for optional local serving, `audit-common` typed contracts.

---

### Task 1: Casing Contract Utilities

**Files:**
- Create: `apps/audit-api/pyproject.toml`
- Create: `apps/audit-api/Makefile`
- Create: `apps/audit-api/README.md`
- Create: `apps/audit-api/audit_api/__init__.py`
- Create: `apps/audit-api/audit_api/casing.py`
- Test: `apps/audit-api/tests/test_casing.py`

- [ ] **Step 1: Write failing tests**

```python
from audit_api.casing import to_camel, to_snake


def test_to_camel_converts_nested_resource_names() -> None:
    payload = {"project_id": "project_1", "sample_ids": ["sample_1"], "policy": {"network_policy": "none"}}
    assert to_camel(payload) == {"projectId": "project_1", "sampleIds": ["sample_1"], "policy": {"networkPolicy": "none"}}


def test_to_snake_converts_nested_resource_names() -> None:
    payload = {"projectId": "project_1", "sampleIds": ["sample_1"], "policy": {"networkPolicy": "none"}}
    assert to_snake(payload) == {"project_id": "project_1", "sample_ids": ["sample_1"], "policy": {"network_policy": "none"}}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/audit-api && PYTHONPATH=. python3 -m unittest discover tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'audit_api'`.

- [ ] **Step 3: Implement casing utilities**

Create recursive conversion helpers for dicts and lists while preserving scalar values.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/audit-api && TEST=tests/test_casing.py make test`
Expected: PASS.

### Task 2: In-Memory Mock Business Service

**Files:**
- Create: `apps/audit-api/audit_api/mock_service.py`
- Test: `apps/audit-api/tests/test_mock_service.py`

- [ ] **Step 1: Write failing tests**

```python
from audit_api.mock_service import AuditMockService


def test_create_analysis_returns_public_camel_case_contract() -> None:
    service = AuditMockService()
    project = service.create_project({"name": "Router", "classification": "internal"})
    sample = service.upload_sample({"projectId": project["id"], "filename": "fw.bin", "sha256": "0" * 64, "size": 128, "format": "Firmware"})

    analysis = service.create_analysis({"projectId": project["id"], "sampleIds": [sample["id"]], "scenario": "firmware"})

    assert analysis["projectId"] == project["id"]
    assert analysis["sampleIds"] == [sample["id"]]
    assert analysis["langgraphThreadId"].startswith("thread_")


def test_list_events_returns_mock_sse_ready_events() -> None:
    service = AuditMockService()
    project = service.create_project({"name": "Router", "classification": "internal"})
    sample = service.upload_sample({"projectId": project["id"], "filename": "fw.bin", "sha256": "0" * 64, "size": 128, "format": "Firmware"})
    analysis = service.create_analysis({"projectId": project["id"], "sampleIds": [sample["id"]], "scenario": "firmware"})

    events = service.list_events(analysis["id"])

    assert events[0]["type"] == "run.queued"
    assert events[0]["analysisId"] == analysis["id"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/audit-api && TEST=tests/test_mock_service.py make test`
Expected: FAIL with `ModuleNotFoundError: No module named 'audit_api.mock_service'`.

- [ ] **Step 3: Implement mock service**

Use internal snake_case dictionaries typed with `audit_common`, expose camelCase dictionaries from service methods, and create one `run.queued` event per analysis.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/audit-api && TEST=tests/test_mock_service.py make test`
Expected: PASS.

### Task 3: Optional HTTP Handler and Docs

**Files:**
- Create: `apps/audit-api/audit_api/server.py`
- Test: `apps/audit-api/tests/test_server.py`
- Modify: `docs/blueprints/implementation-progress.md`
- Modify: `docs/blueprints/feature-registry.md`
- Modify: `docs/blueprints/decision-log.md`
- Modify: `docs/blueprints/openapi-contract.md`

- [ ] **Step 1: Write server smoke test**

Test that `format_sse_event({"id": "evt_1", "type": "run.queued"})` returns `event: run.queued` and a JSON `data:` line.

- [ ] **Step 2: Implement server helper**

Create a stdlib helper for SSE formatting and a minimal `AuditApiHandler` shell for future local serving.

- [ ] **Step 3: Update docs**

Record official docs checked, duplicate check commands, files changed, validation, and decision to keep mock API product-owned and separate from Agent Server native routes.

- [ ] **Step 4: Run validation**

Run: `cd apps/audit-api && make format && make lint && make test` and rerun impacted `libs/audit-common` tests if schema files change.
Expected: all commands exit 0.
