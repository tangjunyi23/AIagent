# Audit API Artifacts and Findings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add mock artifact and finding query/update endpoints to the existing audit API.

**Architecture:** Extend the current in-memory `AuditMockService` and `AuditApiHandler`; keep public JSON camelCase and internal schemas snake_case. Seed deterministic evidence artifacts and findings during mock analysis creation so frontend views can consume stable contracts.

**Tech Stack:** Python standard library HTTP server, `unittest`, existing `audit_common` TypedDict contracts, existing `audit_api.casing` helpers.

---

## File Structure

- Modify `apps/audit-api/audit_api/mock_service.py`: add artifact/finding stores, query methods, patch method, event emission, and state sync.
- Modify `apps/audit-api/audit_api/server.py`: add `GET /api/artifacts/{artifactId}`, `GET /api/findings?analysisId=...`, and `PATCH /api/findings/{findingId}` dispatch.
- Modify `apps/audit-api/tests/test_mock_service.py`: add service-level tests for seeded artifact/finding and patch behavior.
- Modify `apps/audit-api/tests/test_server.py`: add route-level tests for artifact, finding list, and finding patch.
- Modify `docs/blueprints/*.md`: update progress, feature registry, decision log, and OpenAPI notes.

### Task 1: Service Contracts

- [ ] **Step 1: Write failing service tests**

Add tests asserting `get_artifact`, `list_findings`, and `patch_finding` behavior in `apps/audit-api/tests/test_mock_service.py`.

- [ ] **Step 2: Verify tests fail**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_mock_service.MockServiceTests.test_created_analysis_seeds_evidence_artifact tests.test_mock_service.MockServiceTests.test_list_findings_returns_analysis_findings tests.test_mock_service.MockServiceTests.test_patch_finding_updates_status_and_emits_event -v`

Expected: failures or errors because methods do not exist.

- [ ] **Step 3: Implement service methods**

Extend `AuditMockService` with `_artifacts`, `_findings`, `get_artifact`, `list_findings`, and `patch_finding`. Seed one `vuln.finding_evidence` artifact and one draft finding during `create_analysis`.

- [ ] **Step 4: Verify tests pass**

Run the same targeted unittest command. Expected: all targeted tests pass.

### Task 2: HTTP Routes

- [ ] **Step 1: Write failing route tests**

Add route tests in `apps/audit-api/tests/test_server.py` for artifact metadata, findings query, and finding patch.

- [ ] **Step 2: Verify tests fail**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common:../audit-agents python3 -m unittest tests.test_server.AuditApiHandlerRouteTests.test_get_artifact_detail_dispatches_to_service tests.test_server.AuditApiHandlerRouteTests.test_get_findings_filters_by_analysis tests.test_server.AuditApiHandlerRouteTests.test_patch_finding_dispatches_to_service -v`

Expected: `404 not_found` or unsupported method failures.

- [ ] **Step 3: Implement route dispatch**

Add `do_PATCH` and extend `do_GET` in `apps/audit-api/audit_api/server.py` using existing error handling and JSON response helpers.

- [ ] **Step 4: Verify tests pass**

Run the same targeted route unittest command. Expected: all targeted tests pass.

### Task 3: Blueprint Updates and Validation

- [ ] **Step 1: Update docs**

Update `docs/blueprints/feature-registry.md`, `docs/blueprints/decision-log.md`, `docs/blueprints/openapi-contract.md`, and `docs/blueprints/implementation-progress.md` with P10 scope, official docs conclusions, duplicate check, and validation evidence.

- [ ] **Step 2: Run minimal validation**

Run: `cd apps/audit-api && make format && make lint && make test`

Expected: format/lint compile commands exit 0 and API tests pass.

## Self-Review

- Spec coverage: artifacts, findings list, finding patch, docs, and validation are represented.
- Placeholder scan: no TBD/TODO/fill-in instructions remain.
- Type consistency: public methods use existing public camelCase `PublicResource` dictionaries and internal schema names remain snake_case.
