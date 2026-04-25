import unittest

from audit_common import (
    ANALYSIS_STATUS_VALUES,
    AUDIT_EVENT_TYPE_VALUES,
    ARTIFACT_TYPE_VALUES,
    Analysis,
    ApprovalAction,
    ArtifactRef,
    AuditLog,
    AuditEvent,
    AuditPolicy,
    Finding,
    ToolExecution,
    is_dangerous_approval_action,
)


class SchemaTests(unittest.TestCase):
    def test_contract_exports_required_enum_values(self) -> None:
        self.assertIn("running", ANALYSIS_STATUS_VALUES)
        self.assertIn("artifact.created", AUDIT_EVENT_TYPE_VALUES)
        self.assertIn("approval.requested", AUDIT_EVENT_TYPE_VALUES)
        self.assertIn("firmware.rootfs", ARTIFACT_TYPE_VALUES)

    def test_artifact_ref_shape_matches_contract(self) -> None:
        artifact: ArtifactRef = {
            "id": "artifact_123",
            "analysis_id": "analysis_123",
            "project_id": "project_123",
            "type": "static.objdump",
            "name": "objdump.txt",
            "media_type": "text/plain",
            "size": 128,
            "sha256": None,
            "uri": "s3://bucket/artifact_123",
            "producer": {
                "agent": "reverse",
                "node": "reverse_static",
                "tool_execution_id": "tool_123",
            },
            "metadata": {"arch": "x86_64"},
            "created_at": "2026-04-24T16:00:00Z",
        }

        self.assertEqual(artifact["producer"]["tool_execution_id"], "tool_123")

    def test_finding_requires_evidence_artifact_ids(self) -> None:
        finding: Finding = {
            "id": "finding_123",
            "analysis_id": "analysis_123",
            "project_id": "project_123",
            "title": "Command injection candidate",
            "description": "User-controlled HTTP parameter reaches system.",
            "severity": "high",
            "confidence": 0.82,
            "status": "needs-review",
            "cwe": "CWE-78",
            "cve": None,
            "affected_component": "/www/cgi-bin/apply.cgi",
            "evidence_artifact_ids": ["artifact_123"],
            "verification": {
                "status": "pending",
                "approval_id": None,
                "notes": None,
            },
            "created_at": "2026-04-24T16:00:00Z",
            "updated_at": "2026-04-24T16:00:00Z",
        }

        self.assertEqual(finding["evidence_artifact_ids"], ["artifact_123"])

    def test_policy_and_tool_execution_capture_safety_limits(self) -> None:
        policy: AuditPolicy = {
            "allow_dynamic_execution": False,
            "allow_network": False,
            "network_policy": "none",
            "network_allowlist": [],
            "allow_exploit_verification": False,
            "require_approval_for_dynamic": True,
            "require_approval_for_network": True,
            "require_approval_for_exploit": True,
            "max_tool_runtime_seconds": 1800,
            "max_agent_runtime_seconds": 600,
            "max_cpu_cores": 2.0,
            "max_memory_mb": 4096,
            "secret_redaction": True,
        }
        execution: ToolExecution = {
            "id": "tool_123",
            "analysis_id": "analysis_123",
            "project_id": "project_123",
            "tool": "objdump",
            "adapter": "binutils",
            "status": "queued",
            "input_artifact_ids": ["artifact_input"],
            "output_artifact_ids": [],
            "sanitized_args": {"mode": "headers"},
            "approval_id": None,
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
            "limits": {
                "wall_time_seconds": policy["max_tool_runtime_seconds"],
                "cpu_cores": policy["max_cpu_cores"],
                "memory_mb": policy["max_memory_mb"],
                "disk_mb": 1024,
                "network_policy": policy["network_policy"],
            },
            "error": None,
        }

        self.assertEqual(execution["limits"]["network_policy"], "none")

    def test_analysis_captures_langgraph_thread_and_policy(self) -> None:
        analysis: Analysis = {
            "id": "analysis_123",
            "project_id": "project_123",
            "sample_ids": ["sample_123"],
            "scenario": "firmware",
            "status": "queued",
            "policy": {
                "allow_dynamic_execution": False,
                "allow_network": False,
                "network_policy": "none",
                "network_allowlist": [],
                "allow_exploit_verification": False,
                "require_approval_for_dynamic": True,
                "require_approval_for_network": True,
                "require_approval_for_exploit": True,
                "max_tool_runtime_seconds": 1800,
                "max_agent_runtime_seconds": 600,
                "max_cpu_cores": 2.0,
                "max_memory_mb": 4096,
                "secret_redaction": True,
            },
            "langgraph_thread_id": "thread_123",
            "langgraph_run_id": None,
            "created_at": "2026-04-24T16:00:00Z",
            "updated_at": "2026-04-24T16:00:00Z",
        }

        self.assertEqual(analysis["langgraph_thread_id"], "thread_123")
        self.assertEqual(analysis["policy"]["network_policy"], "none")

    def test_audit_event_envelope_uses_sequence_and_payload(self) -> None:
        event: AuditEvent = {
            "id": "evt_42",
            "sequence": 42,
            "analysis_id": "analysis_123",
            "run_id": "run_123",
            "thread_id": "thread_123",
            "node": "reverse_static",
            "agent": "reverse",
            "type": "artifact.created",
            "payload": {
                "artifact_id": "artifact_123",
                "artifact_type": "static.objdump",
                "name": "objdump.txt",
                "media_type": "text/plain",
                "size": 128,
                "sha256": None,
                "tool_execution_id": "tool_123",
            },
            "created_at": "2026-04-24T16:00:00Z",
            "trace_id": "trace_123",
        }

        self.assertEqual(event["sequence"], 42)
        self.assertEqual(event["payload"]["artifact_type"], "static.objdump")

    def test_audit_log_records_sensitive_resource_access(self) -> None:
        log: AuditLog = {
            "id": "audit_123",
            "tenant_id": "tenant_123",
            "project_id": "project_123",
            "analysis_id": "analysis_123",
            "actor_id": "analyst@example.com",
            "action": "report.content.read",
            "resource_type": "report",
            "resource_id": "report_123",
            "outcome": "allowed",
            "reason": "Mock report content read.",
            "metadata": {"redaction_profile": "default"},
            "created_at": "2026-04-24T16:00:00Z",
        }

        self.assertEqual(log["actor_id"], "analyst@example.com")
        self.assertEqual(log["resource_type"], "report")
        self.assertEqual(log["outcome"], "allowed")

    def test_dangerous_approval_actions_are_identified(self) -> None:
        dangerous_actions: list[ApprovalAction] = [
            "dynamic-execution",
            "network-enable",
            "exploit-verification",
            "firmware-emulation",
            "artifact-export",
        ]

        self.assertTrue(
            all(is_dangerous_approval_action(action) for action in dangerous_actions)
        )


if __name__ == "__main__":
    unittest.main()
