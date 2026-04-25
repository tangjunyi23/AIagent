# Audit API POST Dispatch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tested POST route dispatch to the existing mock `AuditApiHandler` so the frozen business API contract can be exercised over HTTP.

**Architecture:** Extend the existing stdlib `BaseHTTPRequestHandler` shell in `apps/audit-api/audit_api/server.py`; do not introduce FastAPI or a second API module. Keep business behavior in `AuditMockService` and keep HTTP concerns in the handler: JSON parsing, route matching, casing conversion already delegated by the service, and SSE formatting via existing helpers.

**Tech Stack:** Python stdlib `http.server`, `json`, `unittest`, existing `audit_api.mock_service.AuditMockService`, existing `audit_api.server.format_sse_event`.

---

### Task 1: POST Route Dispatch Tests

**Files:**
- Modify: `apps/audit-api/tests/test_server.py`
- Read: `apps/audit-api/audit_api/server.py`
- Read: `apps/audit-api/audit_api/mock_service.py`

- [ ] **Step 1: Write failing tests for POST routes**

Add handler-level tests that instantiate a real local `HTTPServer` with `AuditApiHandler`, send JSON requests, and assert these paths dispatch to `AuditMockService`:

```python
class TestAuditApiHandlerRoutes(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AuditMockService(now=lambda: "2026-04-24T00:00:00Z")
        handler = AuditApiHandler.with_service(self.service)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()

    def post_json(self, path: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_post_projects_dispatches_to_service(self) -> None:
        status, payload = self.post_json("/api/projects", {"name": "Firmware Lab"})
        self.assertEqual(status, 201)
        self.assertEqual(payload["name"], "Firmware Lab")
        self.assertEqual(payload["id"], "project_1")

    def test_post_sample_upload_dispatches_to_service(self) -> None:
        self.post_json("/api/projects", {"name": "Firmware Lab"})
        status, payload = self.post_json(
            "/api/samples:upload",
            {
                "projectId": "project_1",
                "filename": "router.bin",
                "sizeBytes": 128,
                "sha256": "a" * 64,
                "format": "elf",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["projectId"], "project_1")
        self.assertEqual(payload["filename"], "router.bin")

    def test_post_analyses_dispatches_to_service(self) -> None:
        self.post_json("/api/projects", {"name": "Firmware Lab"})
        self.post_json(
            "/api/samples:upload",
            {
                "projectId": "project_1",
                "filename": "router.bin",
                "sizeBytes": 128,
                "sha256": "a" * 64,
                "format": "elf",
            },
        )
        status, payload = self.post_json(
            "/api/analyses",
            {"projectId": "project_1", "sampleIds": ["sample_1"], "scenario": "firmware"},
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["id"], "analysis_1")
        self.assertEqual(payload["status"], "queued")
        self.assertEqual(payload["langgraphThreadId"], "thread_analysis_1")
```

- [ ] **Step 2: Run tests to verify red**

Run: `cd apps/audit-api && PYTHONPATH=.:../../libs/audit-common python3 -m unittest tests.test_server -v`

Expected: route tests fail because `AuditApiHandler` does not implement `with_service` or POST dispatch.

### Task 2: Minimal POST Dispatch Implementation

**Files:**
- Modify: `apps/audit-api/audit_api/server.py`
- Test: `apps/audit-api/tests/test_server.py`

- [ ] **Step 1: Add handler factory and JSON helpers**

Implement `AuditApiHandler.with_service(service)`, `_read_json()`, `_write_json(status, payload)`, and `_write_error(status, code, message)` on the existing handler class.

- [ ] **Step 2: Add `do_POST` route matching**

Dispatch exact paths:

```text
POST /api/projects -> service.create_project(payload)
POST /api/samples:upload -> service.upload_sample(payload)
POST /api/analyses -> service.create_analysis(payload)
```

Return HTTP `201` for created resources. Return `404` for unknown paths and `400` for malformed JSON or service validation errors.

- [ ] **Step 3: Run targeted tests to verify green**

Run: `cd apps/audit-api && make test`

Expected: all API tests pass.

### Task 3: Blueprint Synchronization

**Files:**
- Modify: `docs/blueprints/implementation-progress.md`
- Modify: `docs/blueprints/feature-registry.md`
- Modify: `docs/blueprints/decision-log.md`
- Modify: `docs/blueprints/openapi-contract.md` if response status semantics need clarification

- [ ] **Step 1: Record duplicate check and files changed**

Append a `2026-04-24: P4 Audit API POST Dispatch` entry to progress with local docs read, official docs checked, duplicate search commands, files changed, and validation output.

- [ ] **Step 2: Update feature registry status**

Change `Audit API server helpers` from helper-only mock to implemented POST dispatch and record the duplicate search command.

- [ ] **Step 3: Record routing decision**

Append a decision that stdlib handler remains a mock/dev business API shell and does not expose Agent Server or MCP directly.

### Self-Review

- Spec coverage: P1 requires route dispatch tests for POST endpoints; Tasks 1 and 2 cover all existing mock POST service operations.
- Placeholder scan: no task uses open-ended placeholders; exact paths, status codes, and commands are listed.
- Type consistency: tests use public camelCase JSON and existing service resource IDs from `AuditMockService`.
