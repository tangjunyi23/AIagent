import unittest

from audit_api.mock_service import AuditMockService


class MockServiceTests(unittest.TestCase):
    def create_firmware_analysis(self) -> tuple[AuditMockService, dict[str, object]]:
        service = AuditMockService()
        project = service.create_project(
            {"name": "Router", "classification": "internal"}
        )
        sample = service.upload_sample(
            {
                "projectId": project["id"],
                "filename": "fw.bin",
                "sha256": "0" * 64,
                "size": 128,
                "format": "Firmware",
            }
        )
        analysis = service.create_analysis(
            {
                "projectId": project["id"],
                "sampleIds": [sample["id"]],
                "scenario": "firmware",
            }
        )
        return service, analysis

    def test_create_analysis_returns_public_camel_case_contract(self) -> None:
        service = AuditMockService()
        project = service.create_project(
            {"name": "Router", "classification": "internal"}
        )
        sample = service.upload_sample(
            {
                "projectId": project["id"],
                "filename": "fw.bin",
                "sha256": "0" * 64,
                "size": 128,
                "format": "Firmware",
            }
        )

        analysis = service.create_analysis(
            {
                "projectId": project["id"],
                "sampleIds": [sample["id"]],
                "scenario": "firmware",
            }
        )

        self.assertEqual(analysis["projectId"], project["id"])
        self.assertEqual(analysis["sampleIds"], [sample["id"]])
        self.assertTrue(analysis["langgraphThreadId"].startswith("thread_"))

    def test_get_project_returns_public_project_detail(self) -> None:
        service = AuditMockService()
        service.create_project({"name": "Router", "classification": "restricted"})

        project = service.get_project("project_1")

        self.assertEqual(project["id"], "project_1")
        self.assertEqual(project["tenantId"], "tenant_mock")
        self.assertEqual(project["name"], "Router")
        self.assertEqual(project["classification"], "restricted")

    def test_get_sample_returns_public_sample_detail(self) -> None:
        service, _ = self.create_firmware_analysis()

        sample = service.get_sample("sample_1")

        self.assertEqual(sample["id"], "sample_1")
        self.assertEqual(sample["projectId"], "project_1")
        self.assertEqual(sample["filename"], "fw.bin")
        self.assertEqual(sample["artifactId"], "artifact_2")

    def test_get_analysis_returns_public_analysis_detail(self) -> None:
        service, _ = self.create_firmware_analysis()

        analysis = service.get_analysis("analysis_1")

        self.assertEqual(analysis["id"], "analysis_1")
        self.assertEqual(analysis["projectId"], "project_1")
        self.assertEqual(analysis["sampleIds"], ["sample_1"])
        self.assertEqual(analysis["langgraphThreadId"], "thread_1")

    def test_created_analysis_seeds_evidence_artifact(self) -> None:
        service, _ = self.create_firmware_analysis()

        artifact = service.get_artifact("artifact_analysis_1_evidence")
        state = service.get_analysis_state("analysis_1")

        self.assertEqual(artifact["id"], "artifact_analysis_1_evidence")
        self.assertEqual(artifact["analysisId"], "analysis_1")
        self.assertEqual(artifact["projectId"], "project_1")
        self.assertEqual(artifact["type"], "vuln.finding_evidence")
        self.assertEqual(state["artifacts"][0]["id"], "artifact_analysis_1_evidence")

    def test_list_findings_returns_analysis_findings(self) -> None:
        service, _ = self.create_firmware_analysis()

        result = service.list_findings({"analysisId": "analysis_1"})
        findings = result["items"]

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "finding_analysis_1_static_strings")
        self.assertEqual(findings[0]["analysisId"], "analysis_1")
        self.assertEqual(findings[0]["evidenceArtifactIds"], ["artifact_analysis_1_evidence"])
        self.assertEqual(
            result["pagination"],
            {"total": 1, "limit": 50, "offset": 0, "nextOffset": None},
        )

    def test_list_findings_filters_by_project_status_severity_and_paginates(self) -> None:
        service, first_analysis = self.create_firmware_analysis()
        project = service.create_project({"name": "Mobile Lab"})
        sample = service.upload_sample(
            {
                "projectId": project["id"],
                "filename": "app.apk",
                "sha256": "1" * 64,
                "size": 512,
                "format": "APK",
            }
        )
        second_analysis = service.create_analysis(
            {
                "projectId": project["id"],
                "sampleIds": [sample["id"]],
                "scenario": "mobile",
            }
        )
        service.patch_finding(
            "finding_analysis_2_static_strings",
            {"status": "needs-review", "severity": "high"},
        )

        first_page = service.list_findings(
            {"projectId": project["id"], "status": "needs-review", "limit": 1}
        )
        second_page = service.list_findings(
            {"projectId": project["id"], "severity": "high", "limit": 1, "offset": 1}
        )
        empty_project_page = service.list_findings({"projectId": first_analysis["projectId"]})

        self.assertEqual(first_page["items"][0]["analysisId"], second_analysis["id"])
        self.assertEqual(first_page["items"][0]["severity"], "high")
        self.assertEqual(first_page["pagination"]["total"], 1)
        self.assertIsNone(first_page["pagination"]["nextOffset"])
        self.assertEqual(second_page["items"], [])
        self.assertEqual(
            second_page["pagination"],
            {"total": 1, "limit": 1, "offset": 1, "nextOffset": None},
        )
        self.assertEqual(empty_project_page["pagination"]["total"], 1)

    def test_patch_finding_updates_status_and_emits_event(self) -> None:
        service, _ = self.create_firmware_analysis()

        finding = service.patch_finding(
            "finding_analysis_1_static_strings",
            {"status": "needs-review", "severity": "medium"},
        )

        self.assertEqual(finding["status"], "needs-review")
        self.assertEqual(finding["severity"], "medium")
        self.assertEqual(service.list_events("analysis_1")[-1]["type"], "finding.updated")
        state = service.get_analysis_state("analysis_1")
        self.assertEqual(state["findings"][0]["status"], "needs-review")

    def test_create_report_adds_markdown_artifact_and_event(self) -> None:
        service, analysis = self.create_firmware_analysis()

        report = service.create_report(
            {
                "analysisId": analysis["id"],
                "format": "markdown",
                "includeUnverifiedFindings": True,
                "redactionProfile": "default",
            }
        )

        self.assertEqual(report["id"], "report_analysis_1_markdown")
        self.assertEqual(report["analysisId"], analysis["id"])
        self.assertEqual(report["type"], "report.markdown")
        self.assertEqual(report["metadata"]["redactionProfile"], "default")
        self.assertEqual(service.get_report("report_analysis_1_markdown"), report)
        self.assertEqual(service.list_events(str(analysis["id"]))[-1]["type"], "artifact.created")
        state = service.get_analysis_state(str(analysis["id"]))
        self.assertIn("report_analysis_1_markdown", [item["id"] for item in state["artifacts"]])

    def test_create_report_versions_repeated_generation(self) -> None:
        service, analysis = self.create_firmware_analysis()

        first = service.create_report(
            {
                "analysisId": analysis["id"],
                "format": "markdown",
                "includeUnverifiedFindings": True,
            }
        )
        second = service.create_report(
            {
                "analysisId": analysis["id"],
                "format": "markdown",
                "includeUnverifiedFindings": False,
            }
        )

        self.assertEqual(first["id"], "report_analysis_1_markdown")
        self.assertEqual(first["metadata"]["versionNumber"], 1)
        self.assertEqual(second["id"], "report_analysis_1_markdown_v2")
        self.assertEqual(second["metadata"]["versionNumber"], 2)
        self.assertEqual(second["metadata"]["previousReportId"], first["id"])
        self.assertTrue(second["metadata"]["latest"])

        refreshed_first = service.get_report("report_analysis_1_markdown")
        self.assertFalse(refreshed_first["metadata"]["latest"])
        self.assertEqual(
            refreshed_first["metadata"]["supersededByReportId"],
            "report_analysis_1_markdown_v2",
        )
        state = service.get_analysis_state(str(analysis["id"]))
        self.assertIn("report_analysis_1_markdown_v2", [item["id"] for item in state["artifacts"]])

    def test_get_report_content_returns_redacted_payload_and_audit_log(self) -> None:
        service, analysis = self.create_firmware_analysis()
        service.create_report(
            {
                "analysisId": analysis["id"],
                "format": "markdown",
                "includeUnverifiedFindings": True,
                "redactionProfile": "default",
            }
        )

        content = service.get_report_content(
            "report_analysis_1_markdown",
            actor_id="analyst@example.com",
        )

        self.assertEqual(content["reportId"], "report_analysis_1_markdown")
        self.assertEqual(content["artifactId"], "report_analysis_1_markdown")
        self.assertEqual(content["analysisId"], analysis["id"])
        self.assertEqual(content["mediaType"], "text/markdown")
        self.assertEqual(content["encoding"], "utf-8")
        self.assertTrue(content["redacted"])
        self.assertIn("Mock Binary Audit Report", str(content["content"]))
        self.assertEqual(content["auditLogId"], "audit_1")

        logs = service.list_audit_logs(str(analysis["id"]))
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["id"], "audit_1")
        self.assertEqual(logs[0]["actorId"], "analyst@example.com")
        self.assertEqual(logs[0]["action"], "report.content.read")
        self.assertEqual(logs[0]["resourceType"], "report")
        self.assertEqual(logs[0]["resourceId"], "report_analysis_1_markdown")
        self.assertEqual(logs[0]["outcome"], "allowed")

    def test_get_report_content_rejects_non_report_artifact(self) -> None:
        service, _ = self.create_firmware_analysis()

        with self.assertRaises(KeyError):
            service.get_report_content("artifact_analysis_1_evidence")

    def test_list_events_returns_mock_sse_ready_events(self) -> None:
        service = AuditMockService()
        project = service.create_project(
            {"name": "Router", "classification": "internal"}
        )
        sample = service.upload_sample(
            {
                "projectId": project["id"],
                "filename": "fw.bin",
                "sha256": "0" * 64,
                "size": 128,
                "format": "Firmware",
            }
        )
        analysis = service.create_analysis(
            {
                "projectId": project["id"],
                "sampleIds": [sample["id"]],
                "scenario": "firmware",
            }
        )

        events = service.list_events(analysis["id"])

        self.assertEqual(events[0]["type"], "run.queued")
        self.assertEqual(events[0]["analysisId"], analysis["id"])

    def test_analysis_events_have_monotonic_sequences(self) -> None:
        service, analysis = self.create_firmware_analysis()

        events = service.list_events(str(analysis["id"]))

        self.assertEqual([event["sequence"] for event in events], [1, 2])

    def test_list_approvals_returns_pending_interrupt_gate(self) -> None:
        service, analysis = self.create_firmware_analysis()

        approvals = service.list_approvals(str(analysis["id"]))

        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0]["status"], "pending")
        self.assertEqual(
            approvals[0]["interruptId"], "interrupt_analysis_1_firmware_emulation"
        )
        self.assertEqual(approvals[0]["action"], "firmware-emulation")

    def test_approve_interrupt_updates_request_and_appends_event(self) -> None:
        service, analysis = self.create_firmware_analysis()

        approval = service.decide_approval(
            str(analysis["id"]),
            "interrupt_analysis_1_firmware_emulation",
            "approved",
            {
                "decidedBy": "analyst@example.com",
                "decisionReason": "Approved for isolated mock emulation.",
            },
        )

        self.assertEqual(approval["status"], "approved")
        self.assertEqual(approval["decidedBy"], "analyst@example.com")
        self.assertEqual(
            approval["decisionReason"], "Approved for isolated mock emulation."
        )
        self.assertEqual(service.list_events(str(analysis["id"]))[-1]["type"], "approval.approved")

    def test_reject_interrupt_updates_request_and_appends_event(self) -> None:
        service, analysis = self.create_firmware_analysis()

        approval = service.decide_approval(
            str(analysis["id"]),
            "interrupt_analysis_1_firmware_emulation",
            "rejected",
            {
                "decidedBy": "analyst@example.com",
                "decisionReason": "Reject until sample owner approves emulation.",
            },
        )

        self.assertEqual(approval["status"], "rejected")
        self.assertEqual(approval["decidedBy"], "analyst@example.com")
        self.assertEqual(service.list_events(str(analysis["id"]))[-1]["type"], "approval.rejected")

    def test_create_analysis_stores_agent_initial_state(self) -> None:
        service, analysis = self.create_firmware_analysis()

        state = service.get_analysis_state(str(analysis["id"]))

        self.assertEqual(state["analysis"]["id"], analysis["id"])
        self.assertEqual(
            state["analysis"]["langgraphThreadId"], analysis["langgraphThreadId"]
        )
        self.assertEqual(state["analysis"]["policy"], analysis["policy"])
        self.assertEqual(state["artifacts"][0]["id"], "artifact_analysis_1_evidence")
        self.assertEqual(state["findings"][0]["id"], "finding_analysis_1_static_strings")
        self.assertEqual(state["toolExecutions"], [])
        self.assertEqual(
            state["approvalRequests"][0]["interruptId"],
            "interrupt_analysis_1_firmware_emulation",
        )

    def test_decide_approval_updates_agent_state(self) -> None:
        service, analysis = self.create_firmware_analysis()

        service.decide_approval(
            str(analysis["id"]),
            "interrupt_analysis_1_firmware_emulation",
            "approved",
            {"decidedBy": "analyst@example.com"},
        )
        state = service.get_analysis_state(str(analysis["id"]))

        self.assertEqual(state["approvalRequests"][0]["status"], "approved")
        self.assertEqual(state["events"][-1]["type"], "approval.approved")

    def test_start_run_invokes_supervisor_and_interrupts_safely(self) -> None:
        service, analysis = self.create_firmware_analysis()

        run = service.start_run(str(analysis["id"]))

        self.assertEqual(run["id"], "analysis_1")
        self.assertEqual(run["langgraphRunId"], "run_1")
        self.assertEqual(run["status"], "interrupted")
        events = service.list_events(str(analysis["id"]))
        self.assertIn("run.started", [event["type"] for event in events])
        self.assertIn("agent.started", [event["type"] for event in events])
        self.assertEqual(events[-1]["type"], "run.interrupted")
        self.assertEqual(len(service.list_approvals(str(analysis["id"]))), 1)

    def test_start_run_updates_agent_state(self) -> None:
        service, analysis = self.create_firmware_analysis()

        service.start_run(str(analysis["id"]))
        state = service.get_analysis_state(str(analysis["id"]))

        self.assertEqual(state["analysis"]["status"], "interrupted")
        self.assertEqual(state["analysis"]["langgraphRunId"], "run_1")
        self.assertEqual(state["events"][-1]["type"], "run.interrupted")

    def test_resume_run_after_approval_completes_without_tool_execution(self) -> None:
        service, analysis = self.create_firmware_analysis()
        service.start_run(str(analysis["id"]))
        service.decide_approval(
            str(analysis["id"]),
            "interrupt_analysis_1_firmware_emulation",
            "approved",
            {"decisionReason": "Approved for isolated mock emulation."},
        )

        resumed = service.resume_run(str(analysis["id"]))

        self.assertEqual(resumed["status"], "succeeded")
        self.assertEqual(resumed["langgraphRunId"], "run_1")
        events = service.list_events(str(analysis["id"]))
        self.assertEqual(events[-2]["type"], "run.resumed")
        self.assertEqual(events[-1]["type"], "run.succeeded")
        self.assertNotIn("tool.started", [event["type"] for event in events])

    def test_resume_run_requires_approved_approval(self) -> None:
        service, analysis = self.create_firmware_analysis()
        service.start_run(str(analysis["id"]))

        with self.assertRaises(ValueError):
            service.resume_run(str(analysis["id"]))


if __name__ == "__main__":
    unittest.main()
