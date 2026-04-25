# Audit API Approval Mock Flows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add mock approval list/approve/reject flows for pending interrupt gates on existing analysis resources.

**Architecture:** Extend the existing `AuditMockService` with in-memory `ApprovalRequest` storage and append product-owned approval events. Extend the existing stdlib `AuditApiHandler` to dispatch the already-reserved interrupt routes; do not expose LangGraph Agent Server or MCP directly and do not create a new route module.

**Tech Stack:** Python stdlib `http.server`, `json`, `unittest`, existing `audit_common.ApprovalRequest`, existing `AuditMockService`, existing `AuditApiHandler`.

---

### Task 1: Service-Level Approval Tests

**Files:**
- Modify: `apps/audit-api/tests/test_mock_service.py`
- Modify: `apps/audit-api/audit_api/mock_service.py`

- [ ] **Step 1: Write failing service tests**

Add tests that create a project, sample, and firmware analysis, then assert:

```python
approvals = service.list_approvals(analysis["id"])
self.assertEqual(approvals[0]["status"], "pending")
self.assertEqual(approvals[0]["interruptId"], "interrupt_analysis_1_firmware_emulation")

approved = service.decide_approval(
    analysis["id"],
    "interrupt_analysis_1_firmware_emulation",
    "approved",
    {"decidedBy": "analyst@example.com", "decisionReason": "Approved for isolated mock emulation."},
)
self.assertEqual(approved["status"], "approved")
self.assertEqual(approved["decidedBy"], "analyst@example.com")
self.assertEqual(service.list_events(analysis["id"])[-1]["type"], "approval.approved")
```

Add a separate rejection test for `status == "rejected"` and `approval.rejected`.

- [ ] **Step 2: Run service tests to verify red**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common python3 -m unittest tests.test_mock_service -v`

Expected: FAIL with `AttributeError` for missing approval service methods.

### Task 2: Mock Service Approval Implementation

**Files:**
- Modify: `apps/audit-api/audit_api/mock_service.py`

- [ ] **Step 1: Add approval storage**

Add `self._approvals: dict[str, list[ApprovalRequest]] = {}` in `AuditMockService.__init__`.

- [ ] **Step 2: Create pending approval on analysis creation**

After creating an analysis, store one pending firmware-emulation approval request and append an `approval.requested` event after `run.queued`.

- [ ] **Step 3: Add list and decide methods**

Implement:

```python
def list_approvals(self, analysis_id: str) -> list[PublicResource]: ...
def decide_approval(self, analysis_id: str, interrupt_id: str, status: str, payload: PublicResource) -> PublicResource: ...
```

Only accept `approved` and `rejected`; reject non-pending approvals with `ValueError`; append `approval.approved` or `approval.rejected` events.

- [ ] **Step 4: Run service tests to verify green**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common python3 -m unittest tests.test_mock_service -v`

Expected: PASS.

### Task 3: HTTP Approval Route Tests and Dispatch

**Files:**
- Modify: `apps/audit-api/tests/test_server.py`
- Modify: `apps/audit-api/audit_api/server.py`

- [ ] **Step 1: Write failing handler tests**

Add route tests for:

```text
GET /api/analyses/analysis_1/interrupts
POST /api/analyses/analysis_1/interrupts/interrupt_analysis_1_firmware_emulation:approve
POST /api/analyses/analysis_1/interrupts/interrupt_analysis_1_firmware_emulation:reject
```

Assert list returns the pending approval, approve/reject returns the decided approval, and events include `approval.approved` or `approval.rejected`.

- [ ] **Step 2: Run handler tests to verify red**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common python3 -m unittest tests.test_server -v`

Expected: FAIL with 404 for interrupt routes.

- [ ] **Step 3: Implement route parsing**

Extend `do_GET` for `/api/analyses/{analysis_id}/interrupts` and `do_POST` for approve/reject suffix routes. Return `200` for list and decisions; map invalid decision or missing IDs to mock errors.

- [ ] **Step 4: Run handler tests to verify green**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common python3 -m unittest tests.test_server -v`

Expected: PASS.

### Task 4: Documentation and Final Validation

**Files:**
- Modify: `docs/blueprints/implementation-progress.md`
- Modify: `docs/blueprints/feature-registry.md`
- Modify: `docs/blueprints/decision-log.md`
- Modify: `docs/blueprints/openapi-contract.md`
- Modify: `docs/blueprints/event-schema.md` only if event payload shape changes

- [ ] **Step 1: Update feature registry**

Mark interrupt routes and approval events as mock implemented, and register `list_approvals` / `decide_approval`.

- [ ] **Step 2: Update progress and decisions**

Record local docs read, official docs checked, duplicate checks, files changed, TDD evidence, and validation output.

- [ ] **Step 3: Run final validation**

Run: `cd apps/audit-api && make format && make lint && make test`

Expected: all API tests pass.

### Self-Review

- Spec coverage: covers approval list, approve, reject, event emission, and reserved API routes.
- Placeholder scan: no placeholder tasks; every route, method, and validation command is explicit.
- Type consistency: service returns public camelCase dictionaries while storing `ApprovalRequest` snake_case objects internally.
