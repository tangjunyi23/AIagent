import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from audit_api.mock_service import AuditMockService
from audit_api.server import AuditApiHandler, format_sse_event


class ServerTests(unittest.TestCase):
    def test_format_sse_event_uses_event_type_and_json_data(self) -> None:
        rendered = format_sse_event({"id": "evt_1", "type": "run.queued"})

        self.assertTrue(rendered.startswith("event: run.queued\n"))
        data_line = rendered.splitlines()[1]
        self.assertTrue(data_line.startswith("data: "))
        self.assertEqual(json.loads(data_line.removeprefix("data: "))["id"], "evt_1")


class AuditApiHandlerRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        handler = AuditApiHandler.with_service(AuditMockService())
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

    def patch_json(self, path: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="PATCH",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def get_text(self, path: str) -> tuple[int, str, str]:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=5) as response:
            return (
                response.status,
                response.headers.get("content-type", ""),
                response.read().decode("utf-8"),
            )

    def get_json(self, path: str) -> tuple[int, object]:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def create_firmware_analysis(self) -> None:
        self.post_json("/api/projects", {"name": "Firmware Lab"})
        self.post_json(
            "/api/samples:upload",
            {
                "projectId": "project_1",
                "filename": "router.bin",
                "size": 128,
                "sha256": "a" * 64,
                "format": "Firmware",
            },
        )
        self.post_json(
            "/api/analyses",
            {
                "projectId": "project_1",
                "sampleIds": ["sample_1"],
                "scenario": "firmware",
            },
        )

    def test_post_projects_dispatches_to_service(self) -> None:
        status, payload = self.post_json("/api/projects", {"name": "Firmware Lab"})

        self.assertEqual(status, 201)
        self.assertEqual(payload["id"], "project_1")
        self.assertEqual(payload["name"], "Firmware Lab")

    def test_get_project_detail_dispatches_to_service(self) -> None:
        self.post_json("/api/projects", {"name": "Firmware Lab"})

        status, payload = self.get_json("/api/projects/project_1")

        self.assertEqual(status, 200)
        self.assertEqual(payload["id"], "project_1")
        self.assertEqual(payload["name"], "Firmware Lab")

    def test_post_sample_upload_dispatches_to_service(self) -> None:
        self.post_json("/api/projects", {"name": "Firmware Lab"})

        status, payload = self.post_json(
            "/api/samples:upload",
            {
                "projectId": "project_1",
                "filename": "router.bin",
                "size": 128,
                "sha256": "a" * 64,
                "format": "Firmware",
            },
        )

        self.assertEqual(status, 201)
        self.assertEqual(payload["id"], "sample_1")
        self.assertEqual(payload["projectId"], "project_1")
        self.assertEqual(payload["filename"], "router.bin")

    def test_get_sample_detail_dispatches_to_service(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.get_json("/api/samples/sample_1")

        self.assertEqual(status, 200)
        self.assertEqual(payload["id"], "sample_1")
        self.assertEqual(payload["filename"], "router.bin")

    def test_post_analyses_dispatches_to_service(self) -> None:
        self.post_json("/api/projects", {"name": "Firmware Lab"})
        self.post_json(
            "/api/samples:upload",
            {
                "projectId": "project_1",
                "filename": "router.bin",
                "size": 128,
                "sha256": "a" * 64,
                "format": "Firmware",
            },
        )

        status, payload = self.post_json(
            "/api/analyses",
            {
                "projectId": "project_1",
                "sampleIds": ["sample_1"],
                "scenario": "firmware",
            },
        )

        self.assertEqual(status, 201)
        self.assertEqual(payload["id"], "analysis_1")
        self.assertEqual(payload["status"], "queued")
        self.assertEqual(payload["langgraphThreadId"], "thread_1")

    def test_get_analysis_detail_dispatches_to_service(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.get_json("/api/analyses/analysis_1")

        self.assertEqual(status, 200)
        self.assertEqual(payload["id"], "analysis_1")
        self.assertEqual(payload["projectId"], "project_1")
        self.assertEqual(payload["sampleIds"], ["sample_1"])

    def test_get_artifact_detail_dispatches_to_service(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.get_json("/api/artifacts/artifact_analysis_1_evidence")

        self.assertEqual(status, 200)
        self.assertEqual(payload["id"], "artifact_analysis_1_evidence")
        self.assertEqual(payload["analysisId"], "analysis_1")
        self.assertEqual(payload["type"], "vuln.finding_evidence")

    def test_get_findings_filters_by_analysis(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.get_json("/api/findings?analysisId=analysis_1")

        self.assertEqual(status, 200)
        result = dict(payload)
        findings = list(result["items"])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "finding_analysis_1_static_strings")
        self.assertEqual(findings[0]["evidenceArtifactIds"], ["artifact_analysis_1_evidence"])
        self.assertEqual(
            result["pagination"],
            {"total": 1, "limit": 50, "offset": 0, "nextOffset": None},
        )

    def test_get_findings_supports_project_filters_and_pagination(self) -> None:
        self.create_firmware_analysis()
        self.post_json("/api/projects", {"name": "Mobile Lab"})
        self.post_json(
            "/api/samples:upload",
            {
                "projectId": "project_2",
                "filename": "app.apk",
                "size": 256,
                "sha256": "b" * 64,
                "format": "APK",
            },
        )
        self.post_json(
            "/api/analyses",
            {
                "projectId": "project_2",
                "sampleIds": ["sample_2"],
                "scenario": "mobile",
            },
        )
        self.patch_json(
            "/api/findings/finding_analysis_2_static_strings",
            {"status": "needs-review", "severity": "high"},
        )

        status, payload = self.get_json(
            "/api/findings?projectId=project_2&status=needs-review&severity=high&limit=1&offset=0"
        )

        self.assertEqual(status, 200)
        result = dict(payload)
        findings = list(result["items"])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["analysisId"], "analysis_2")
        self.assertEqual(findings[0]["projectId"], "project_2")
        self.assertEqual(findings[0]["status"], "needs-review")
        self.assertEqual(findings[0]["severity"], "high")
        self.assertEqual(
            result["pagination"],
            {"total": 1, "limit": 1, "offset": 0, "nextOffset": None},
        )

    def test_patch_finding_dispatches_to_service(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.patch_json(
            "/api/findings/finding_analysis_1_static_strings",
            {"status": "needs-review", "severity": "medium"},
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "needs-review")
        self.assertEqual(payload["severity"], "medium")
        _, _, events = self.get_text("/api/analyses/analysis_1/events")
        self.assertIn("event: finding.updated\n", events)

    def test_post_reports_generates_report_artifact(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.post_json(
            "/api/reports",
            {
                "analysisId": "analysis_1",
                "format": "markdown",
                "includeUnverifiedFindings": True,
                "redactionProfile": "default",
            },
        )

        self.assertEqual(status, 201)
        self.assertEqual(payload["id"], "report_analysis_1_markdown")
        self.assertEqual(payload["type"], "report.markdown")
        self.assertEqual(payload["metadata"]["findingCount"], 1)
        _, _, events = self.get_text("/api/analyses/analysis_1/events")
        self.assertIn("event: artifact.created\n", events)

    def test_post_reports_generates_versioned_report_artifacts(self) -> None:
        self.create_firmware_analysis()
        self.post_json(
            "/api/reports",
            {
                "analysisId": "analysis_1",
                "format": "markdown",
                "includeUnverifiedFindings": True,
            },
        )

        status, payload = self.post_json(
            "/api/reports",
            {
                "analysisId": "analysis_1",
                "format": "markdown",
                "includeUnverifiedFindings": False,
            },
        )

        self.assertEqual(status, 201)
        self.assertEqual(payload["id"], "report_analysis_1_markdown_v2")
        self.assertEqual(payload["metadata"]["versionNumber"], 2)
        self.assertEqual(
            payload["metadata"]["previousReportId"],
            "report_analysis_1_markdown",
        )
        _, first = self.get_json("/api/reports/report_analysis_1_markdown")
        self.assertFalse(first["metadata"]["latest"])

    def test_get_report_detail_dispatches_to_service(self) -> None:
        self.create_firmware_analysis()
        self.post_json(
            "/api/reports",
            {
                "analysisId": "analysis_1",
                "format": "markdown",
                "includeUnverifiedFindings": True,
                "redactionProfile": "default",
            },
        )

        status, payload = self.get_json("/api/reports/report_analysis_1_markdown")

        self.assertEqual(status, 200)
        self.assertEqual(payload["id"], "report_analysis_1_markdown")
        self.assertEqual(payload["analysisId"], "analysis_1")

    def test_get_report_content_dispatches_and_records_audit_log(self) -> None:
        self.create_firmware_analysis()
        self.post_json(
            "/api/reports",
            {
                "analysisId": "analysis_1",
                "format": "markdown",
                "includeUnverifiedFindings": True,
                "redactionProfile": "default",
            },
        )

        status, payload = self.get_json("/api/reports/report_analysis_1_markdown/content")

        self.assertEqual(status, 200)
        self.assertEqual(payload["reportId"], "report_analysis_1_markdown")
        self.assertEqual(payload["mediaType"], "text/markdown")
        self.assertTrue(payload["redacted"])
        self.assertIn("Mock Binary Audit Report", payload["content"])
        self.assertEqual(payload["auditLogId"], "audit_1")

        _, logs = self.get_json("/api/audit-logs?analysisId=analysis_1")
        audit_logs = list(logs)
        self.assertEqual(len(audit_logs), 1)
        self.assertEqual(audit_logs[0]["action"], "report.content.read")
        self.assertEqual(audit_logs[0]["resourceId"], "report_analysis_1_markdown")

    def test_get_analysis_events_returns_sse_frames(self) -> None:
        self.create_firmware_analysis()

        status, content_type, body = self.get_text("/api/analyses/analysis_1/events")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "text/event-stream")
        self.assertIn("event: run.queued\n", body)
        self.assertIn('"analysisId": "analysis_1"', body)

    def test_get_interrupts_lists_pending_approval(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.get_json("/api/analyses/analysis_1/interrupts")

        self.assertEqual(status, 200)
        self.assertIsInstance(payload, list)
        approvals = list(payload)
        self.assertEqual(approvals[0]["status"], "pending")
        self.assertEqual(
            approvals[0]["interruptId"], "interrupt_analysis_1_firmware_emulation"
        )

    def test_get_analysis_state_returns_agent_state_snapshot(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.get_json("/api/analyses/analysis_1/state")

        self.assertEqual(status, 200)
        self.assertIsInstance(payload, dict)
        state = dict(payload)
        self.assertEqual(state["analysis"]["id"], "analysis_1")
        self.assertEqual(state["analysis"]["langgraphThreadId"], "thread_1")
        self.assertEqual(state["artifacts"][0]["id"], "artifact_analysis_1_evidence")
        self.assertEqual(state["findings"][0]["id"], "finding_analysis_1_static_strings")
        self.assertEqual(state["toolExecutions"], [])
        self.assertEqual(
            state["approvalRequests"][0]["interruptId"],
            "interrupt_analysis_1_firmware_emulation",
        )

    def test_post_analysis_runs_starts_mock_supervisor_run(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.post_json("/api/analyses/analysis_1/runs", {})

        self.assertEqual(status, 200)
        self.assertEqual(payload["langgraphRunId"], "run_1")
        self.assertEqual(payload["status"], "interrupted")
        _, _, events = self.get_text("/api/analyses/analysis_1/events")
        self.assertIn("event: run.started\n", events)
        self.assertIn("event: agent.started\n", events)
        self.assertIn("event: run.interrupted\n", events)

    def test_post_analysis_runs_resume_completes_mock_run(self) -> None:
        self.create_firmware_analysis()
        self.post_json("/api/analyses/analysis_1/runs", {})
        self.post_json(
            "/api/analyses/analysis_1/interrupts/interrupt_analysis_1_firmware_emulation:approve",
            {"decisionReason": "Approved for isolated mock emulation."},
        )

        status, payload = self.post_json("/api/analyses/analysis_1/runs:resume", {})

        self.assertEqual(status, 200)
        self.assertEqual(payload["langgraphRunId"], "run_1")
        self.assertEqual(payload["status"], "succeeded")
        _, _, events = self.get_text("/api/analyses/analysis_1/events")
        self.assertIn("event: run.resumed\n", events)
        self.assertIn("event: run.succeeded\n", events)

    def test_post_interrupt_approve_decides_approval(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.post_json(
            "/api/analyses/analysis_1/interrupts/interrupt_analysis_1_firmware_emulation:approve",
            {
                "decidedBy": "analyst@example.com",
                "decisionReason": "Approved for isolated mock emulation.",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "approved")
        self.assertEqual(payload["decidedBy"], "analyst@example.com")
        _, _, events = self.get_text("/api/analyses/analysis_1/events")
        self.assertIn("event: approval.approved\n", events)

    def test_post_interrupt_reject_decides_approval(self) -> None:
        self.create_firmware_analysis()

        status, payload = self.post_json(
            "/api/analyses/analysis_1/interrupts/interrupt_analysis_1_firmware_emulation:reject",
            {
                "decidedBy": "analyst@example.com",
                "decisionReason": "Reject until sample owner approves emulation.",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "rejected")
        self.assertEqual(payload["decidedBy"], "analyst@example.com")
        _, _, events = self.get_text("/api/analyses/analysis_1/events")
        self.assertIn("event: approval.rejected\n", events)


if __name__ == "__main__":
    unittest.main()
