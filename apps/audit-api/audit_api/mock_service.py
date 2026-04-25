"""In-memory business API mock service."""

from __future__ import annotations

from typing import Any, cast

from audit_common import (
    Analysis,
    ApprovalRequest,
    ApprovalStatus,
    ArtifactRef,
    AuditEvent,
    AuditPolicy,
    Classification,
    Finding,
    FindingStatus,
    Project,
    Sample,
    Severity,
)
from audit_agents import AuditAgentState, build_supervisor_graph, create_initial_state

from audit_api.casing import to_camel, to_snake

PublicResource = dict[str, Any]


class AuditMockService:
    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._samples: dict[str, Sample] = {}
        self._analyses: dict[str, Analysis] = {}
        self._artifacts: dict[str, ArtifactRef] = {}
        self._findings: dict[str, Finding] = {}
        self._agent_states: dict[str, AuditAgentState] = {}
        self._approvals: dict[str, list[ApprovalRequest]] = {}
        self._events: dict[str, list[AuditEvent]] = {}
        self._next_project = 1
        self._next_sample = 1
        self._next_analysis = 1
        self._next_run = 1
        self._next_event = 1

    def create_project(self, payload: PublicResource) -> PublicResource:
        body = cast(dict[str, Any], to_snake(payload))
        project_id = self._allocate_id("project", self._next_project)
        self._next_project += 1
        project: Project = {
            "id": project_id,
            "tenant_id": str(body.get("tenant_id", "tenant_mock")),
            "name": str(body["name"]),
            "classification": cast(Classification, body.get("classification", "internal")),
            "created_at": self._timestamp(),
            "updated_at": self._timestamp(),
        }
        self._projects[project_id] = project
        return cast(PublicResource, to_camel(project))

    def list_projects(self) -> list[PublicResource]:
        return [cast(PublicResource, to_camel(project)) for project in self._projects.values()]

    def get_project(self, project_id: str) -> PublicResource:
        self._require_project(project_id)
        return cast(PublicResource, to_camel(self._projects[project_id]))

    def upload_sample(self, payload: PublicResource) -> PublicResource:
        body = cast(dict[str, Any], to_snake(payload))
        project_id = str(body["project_id"])
        self._require_project(project_id)
        sample_id = self._allocate_id("sample", self._next_sample)
        self._next_sample += 1
        sample: Sample = {
            "id": sample_id,
            "project_id": project_id,
            "filename": str(body["filename"]),
            "sha256": str(body["sha256"]),
            "size": int(body["size"]),
            "format": body.get("format", "Unknown"),
            "arch": body.get("arch"),
            "mime_type": body.get("mime_type"),
            "magic": body.get("magic"),
            "uploaded_at": self._timestamp(),
            "artifact_id": self._allocate_id("artifact", self._next_sample),
        }
        self._samples[sample_id] = sample
        return cast(PublicResource, to_camel(sample))

    def get_sample(self, sample_id: str) -> PublicResource:
        self._require_sample(sample_id)
        return cast(PublicResource, to_camel(self._samples[sample_id]))

    def create_analysis(self, payload: PublicResource) -> PublicResource:
        body = cast(dict[str, Any], to_snake(payload))
        project_id = str(body["project_id"])
        self._require_project(project_id)
        sample_ids = [str(sample_id) for sample_id in body["sample_ids"]]
        for sample_id in sample_ids:
            self._require_sample(sample_id)
        analysis_id = self._allocate_id("analysis", self._next_analysis)
        thread_id = self._allocate_id("thread", self._next_analysis)
        self._next_analysis += 1
        policy = self._policy_from_body(cast(dict[str, Any], body.get("policy", {})))
        analysis: Analysis = {
            "id": analysis_id,
            "project_id": project_id,
            "sample_ids": sample_ids,
            "scenario": body.get("scenario", "firmware"),
            "status": "queued",
            "policy": policy,
            "langgraph_thread_id": thread_id,
            "langgraph_run_id": None,
            "created_at": self._timestamp(),
            "updated_at": self._timestamp(),
        }
        self._analyses[analysis_id] = analysis
        artifact = self._create_mock_evidence_artifact(analysis)
        finding = self._create_mock_finding(analysis, artifact)
        self._artifacts[artifact["id"]] = artifact
        self._findings[finding["id"]] = finding
        approval = self._create_firmware_emulation_approval(analysis)
        self._approvals[analysis_id] = [approval]
        self._events[analysis_id] = []
        self._events[analysis_id].append(self._create_run_queued_event(analysis))
        self._events[analysis_id].append(
            self._create_approval_event(analysis, approval, "approval.requested")
        )
        self._agent_states[analysis_id] = create_initial_state(
            analysis_id=analysis_id,
            project_id=project_id,
            sample_ids=sample_ids,
            scenario=analysis["scenario"],
            thread_id=thread_id,
        )
        self._sync_agent_state(analysis_id)
        return cast(PublicResource, to_camel(analysis))

    def get_analysis(self, analysis_id: str) -> PublicResource:
        return cast(PublicResource, to_camel(self._analyses[analysis_id]))

    def get_artifact(self, artifact_id: str) -> PublicResource:
        if artifact_id not in self._artifacts:
            raise KeyError(f"unknown artifact: {artifact_id}")
        return cast(PublicResource, to_camel(self._artifacts[artifact_id]))

    def create_report(self, payload: PublicResource) -> PublicResource:
        body = cast(dict[str, Any], to_snake(payload))
        analysis_id = str(body["analysis_id"])
        self._require_analysis(analysis_id)
        analysis = self._analyses[analysis_id]
        report_format = str(body.get("format", "markdown"))
        artifact_type, media_type, extension = self._report_format_metadata(report_format)
        include_unverified = bool(body.get("include_unverified_findings", True))
        findings = [
            finding
            for finding in self._findings.values()
            if finding["analysis_id"] == analysis_id
            and (include_unverified or finding["verification"]["status"] == "verified")
        ]
        artifact: ArtifactRef = {
            "id": f"report_{analysis_id}_{report_format}",
            "analysis_id": analysis_id,
            "project_id": analysis["project_id"],
            "type": artifact_type,
            "name": f"{analysis_id}-audit-report.{extension}",
            "media_type": media_type,
            "size": 512,
            "sha256": None,
            "uri": f"memory://reports/{analysis_id}/{report_format}",
            "producer": {
                "agent": "report",
                "node": "mock_report_builder",
                "tool_execution_id": None,
            },
            "metadata": {
                "source": "mock-service",
                "format": report_format,
                "include_unverified_findings": include_unverified,
                "finding_count": len(findings),
                "redaction_profile": str(body.get("redaction_profile", "default")),
            },
            "created_at": self._timestamp(),
        }
        self._artifacts[artifact["id"]] = artifact
        self._events[analysis_id].append(self._create_artifact_event(artifact))
        self._sync_agent_state(analysis_id)
        return cast(PublicResource, to_camel(artifact))

    def get_report(self, report_id: str) -> PublicResource:
        if report_id not in self._artifacts:
            raise KeyError(f"unknown report: {report_id}")
        artifact = self._artifacts[report_id]
        if not artifact["type"].startswith("report."):
            raise KeyError(f"unknown report: {report_id}")
        return cast(PublicResource, to_camel(artifact))

    def list_findings(self, analysis_id: str) -> list[PublicResource]:
        self._require_analysis(analysis_id)
        findings = [
            finding
            for finding in self._findings.values()
            if finding["analysis_id"] == analysis_id
        ]
        return [cast(PublicResource, to_camel(finding)) for finding in findings]

    def patch_finding(self, finding_id: str, payload: PublicResource) -> PublicResource:
        if finding_id not in self._findings:
            raise KeyError(f"unknown finding: {finding_id}")
        body = cast(dict[str, Any], to_snake(payload))
        finding = self._findings[finding_id]
        if "status" in body:
            finding["status"] = cast(FindingStatus, body["status"])
        if "severity" in body:
            finding["severity"] = cast(Severity, body["severity"])
        if "description" in body:
            finding["description"] = str(body["description"])
        finding["updated_at"] = self._timestamp()
        analysis = self._analyses[finding["analysis_id"]]
        self._events[analysis["id"]].append(self._create_finding_event(finding))
        self._sync_agent_state(analysis["id"])
        return cast(PublicResource, to_camel(finding))

    def list_events(self, analysis_id: str) -> list[PublicResource]:
        return [cast(PublicResource, to_camel(event)) for event in self._events[analysis_id]]

    def list_approvals(self, analysis_id: str) -> list[PublicResource]:
        self._require_analysis(analysis_id)
        return [cast(PublicResource, to_camel(approval)) for approval in self._approvals[analysis_id]]

    def get_analysis_state(self, analysis_id: str) -> PublicResource:
        self._require_analysis(analysis_id)
        return cast(PublicResource, to_camel(self._agent_states[analysis_id]))

    def start_run(self, analysis_id: str) -> PublicResource:
        self._require_analysis(analysis_id)
        analysis = self._analyses[analysis_id]
        if analysis["langgraph_run_id"] is None:
            analysis["langgraph_run_id"] = self._allocate_id("run", self._next_run)
            self._next_run += 1
        analysis["status"] = "running"
        self._sync_agent_state(analysis_id)
        self._events[analysis_id].append(self._create_run_event(analysis, "run.started"))

        graph = build_supervisor_graph()
        graph_state = graph.invoke(self._agent_states[analysis_id])
        self._merge_graph_state(analysis_id, graph_state)
        self._events[analysis_id].append(self._create_run_event(analysis, "run.interrupted"))
        self._sync_agent_state(analysis_id)
        return cast(PublicResource, to_camel(analysis))

    def resume_run(self, analysis_id: str) -> PublicResource:
        self._require_analysis(analysis_id)
        analysis = self._analyses[analysis_id]
        if analysis["langgraph_run_id"] is None:
            raise ValueError(f"analysis has no run to resume: {analysis_id}")
        if analysis["status"] == "succeeded":
            return cast(PublicResource, to_camel(analysis))
        if not self._has_approved_dangerous_action(analysis_id):
            raise ValueError(f"analysis has no approved interrupt to resume: {analysis_id}")
        analysis["status"] = "running"
        self._events[analysis_id].append(self._create_run_event(analysis, "run.resumed"))
        analysis["status"] = "succeeded"
        self._events[analysis_id].append(self._create_run_event(analysis, "run.succeeded"))
        self._sync_agent_state(analysis_id)
        return cast(PublicResource, to_camel(analysis))

    def decide_approval(
        self,
        analysis_id: str,
        interrupt_id: str,
        status: str,
        payload: PublicResource,
    ) -> PublicResource:
        self._require_analysis(analysis_id)
        if status not in ("approved", "rejected"):
            raise ValueError(f"unsupported approval decision: {status}")
        approval = self._find_approval(analysis_id, interrupt_id)
        if approval["status"] != "pending":
            raise ValueError(f"approval is already decided: {interrupt_id}")
        body = cast(dict[str, Any], to_snake(payload))
        approval["status"] = cast(ApprovalStatus, status)
        approval["decided_at"] = self._timestamp()
        approval["decided_by"] = str(body.get("decided_by", "mock_analyst"))
        approval["decision_reason"] = str(body.get("decision_reason", ""))
        event_type = "approval.approved" if status == "approved" else "approval.rejected"
        self._events[analysis_id].append(
            self._create_approval_event(
                self._analyses[analysis_id],
                approval,
                event_type,
            )
        )
        self._sync_agent_state(analysis_id)
        return cast(PublicResource, to_camel(approval))

    def _create_run_queued_event(self, analysis: Analysis) -> AuditEvent:
        event_id = self._allocate_id("evt", self._next_event)
        self._next_event += 1
        return {
            "id": event_id,
            "sequence": 1,
            "analysis_id": analysis["id"],
            "run_id": analysis["langgraph_run_id"] or "",
            "thread_id": analysis["langgraph_thread_id"],
            "node": None,
            "agent": None,
            "type": "run.queued",
            "payload": {"status": "queued"},
            "created_at": self._timestamp(),
            "trace_id": None,
        }

    def _create_run_event(self, analysis: Analysis, event_type: str) -> AuditEvent:
        event_id = self._allocate_id("evt", self._next_event)
        self._next_event += 1
        return {
            "id": event_id,
            "sequence": len(self._events.get(analysis["id"], [])) + 1,
            "analysis_id": analysis["id"],
            "run_id": analysis["langgraph_run_id"] or "",
            "thread_id": analysis["langgraph_thread_id"],
            "node": None,
            "agent": None,
            "type": event_type,
            "payload": {"status": analysis["status"]},
            "created_at": self._timestamp(),
            "trace_id": None,
        }

    def _create_mock_evidence_artifact(self, analysis: Analysis) -> ArtifactRef:
        return {
            "id": f"artifact_{analysis['id']}_evidence",
            "analysis_id": analysis["id"],
            "project_id": analysis["project_id"],
            "type": "vuln.finding_evidence",
            "name": "mock-static-evidence.json",
            "media_type": "application/json",
            "size": 256,
            "sha256": None,
            "uri": f"memory://artifacts/{analysis['id']}/mock-static-evidence.json",
            "producer": {
                "agent": "triage",
                "node": "mock_static_review",
                "tool_execution_id": None,
            },
            "metadata": {
                "source": "mock-service",
                "summary": "Deterministic evidence for frontend contract development.",
            },
            "created_at": self._timestamp(),
        }

    def _create_mock_finding(
        self,
        analysis: Analysis,
        artifact: ArtifactRef,
    ) -> Finding:
        return {
            "id": f"finding_{analysis['id']}_static_strings",
            "analysis_id": analysis["id"],
            "project_id": analysis["project_id"],
            "title": "Mock suspicious firmware string",
            "description": "A deterministic mock finding for frontend finding workflows.",
            "severity": "low",
            "confidence": 0.55,
            "status": "draft",
            "cwe": None,
            "cve": None,
            "affected_component": "firmware-image",
            "evidence_artifact_ids": [artifact["id"]],
            "verification": {
                "status": "pending",
                "approval_id": None,
                "notes": "Mock finding has not been verified by a dynamic tool.",
            },
            "created_at": self._timestamp(),
            "updated_at": self._timestamp(),
        }

    def _create_finding_event(self, finding: Finding) -> AuditEvent:
        event_id = self._allocate_id("evt", self._next_event)
        self._next_event += 1
        return {
            "id": event_id,
            "sequence": len(self._events.get(finding["analysis_id"], [])) + 1,
            "analysis_id": finding["analysis_id"],
            "run_id": self._analyses[finding["analysis_id"]]["langgraph_run_id"] or "",
            "thread_id": self._analyses[finding["analysis_id"]]["langgraph_thread_id"],
            "node": "analyst_update",
            "agent": None,
            "type": "finding.updated",
            "payload": {
                "finding_id": finding["id"],
                "title": finding["title"],
                "severity": finding["severity"],
                "confidence": finding["confidence"],
                "status": finding["status"],
                "evidence_artifact_ids": finding["evidence_artifact_ids"],
            },
            "created_at": self._timestamp(),
            "trace_id": None,
        }

    def _create_artifact_event(self, artifact: ArtifactRef) -> AuditEvent:
        analysis = self._analyses[artifact["analysis_id"]]
        event_id = self._allocate_id("evt", self._next_event)
        self._next_event += 1
        return {
            "id": event_id,
            "sequence": len(self._events.get(artifact["analysis_id"], [])) + 1,
            "analysis_id": artifact["analysis_id"],
            "run_id": analysis["langgraph_run_id"] or "",
            "thread_id": analysis["langgraph_thread_id"],
            "node": artifact["producer"]["node"],
            "agent": artifact["producer"]["agent"],
            "type": "artifact.created",
            "payload": {
                "artifact_id": artifact["id"],
                "artifact_type": artifact["type"],
                "name": artifact["name"],
                "media_type": artifact["media_type"],
                "size": artifact["size"],
                "sha256": artifact["sha256"],
                "tool_execution_id": artifact["producer"]["tool_execution_id"],
            },
            "created_at": self._timestamp(),
            "trace_id": None,
        }

    def _create_firmware_emulation_approval(self, analysis: Analysis) -> ApprovalRequest:
        return {
            "id": f"approval_{analysis['id']}_firmware_emulation",
            "analysis_id": analysis["id"],
            "project_id": analysis["project_id"],
            "interrupt_id": f"interrupt_{analysis['id']}_firmware_emulation",
            "action": "firmware-emulation",
            "status": "pending",
            "requested_by_agent": "supervisor",
            "reason": "Firmware emulation is a dangerous dynamic action.",
            "risk_summary": "Execution is blocked until a human approves sandbox limits.",
            "proposed_parameters": {
                "network_policy": analysis["policy"]["network_policy"],
                "max_runtime_seconds": analysis["policy"]["max_agent_runtime_seconds"],
            },
            "created_at": self._timestamp(),
            "decided_at": None,
            "decided_by": None,
            "decision_reason": None,
        }

    def _create_approval_event(
        self,
        analysis: Analysis,
        approval: ApprovalRequest,
        event_type: str,
    ) -> AuditEvent:
        event_id = self._allocate_id("evt", self._next_event)
        self._next_event += 1
        return {
            "id": event_id,
            "sequence": len(self._events.get(analysis["id"], [])) + 1,
            "analysis_id": analysis["id"],
            "run_id": analysis["langgraph_run_id"] or "",
            "thread_id": analysis["langgraph_thread_id"],
            "node": "approval_gate",
            "agent": "supervisor",
            "type": event_type,
            "payload": {
                "approval_id": approval["id"],
                "interrupt_id": approval["interrupt_id"],
                "action": approval["action"],
                "status": approval["status"],
                "risk_summary": approval["risk_summary"],
                "proposed_parameters": approval["proposed_parameters"],
                "decision_reason": approval["decision_reason"],
            },
            "created_at": self._timestamp(),
            "trace_id": None,
        }

    def _policy_from_body(self, body: dict[str, Any]) -> AuditPolicy:
        return {
            "allow_dynamic_execution": bool(body.get("allow_dynamic_execution", False)),
            "allow_network": bool(body.get("allow_network", False)),
            "network_policy": body.get("network_policy", "none"),
            "network_allowlist": list(body.get("network_allowlist", [])),
            "allow_exploit_verification": bool(body.get("allow_exploit_verification", False)),
            "require_approval_for_dynamic": bool(body.get("require_approval_for_dynamic", True)),
            "require_approval_for_network": bool(body.get("require_approval_for_network", True)),
            "require_approval_for_exploit": bool(body.get("require_approval_for_exploit", True)),
            "max_tool_runtime_seconds": int(body.get("max_tool_runtime_seconds", 1800)),
            "max_agent_runtime_seconds": int(body.get("max_agent_runtime_seconds", 600)),
            "max_cpu_cores": float(body.get("max_cpu_cores", 2.0)),
            "max_memory_mb": int(body.get("max_memory_mb", 4096)),
            "secret_redaction": bool(body.get("secret_redaction", True)),
        }

    def _require_project(self, project_id: str) -> None:
        if project_id not in self._projects:
            raise KeyError(f"unknown project: {project_id}")

    def _require_sample(self, sample_id: str) -> None:
        if sample_id not in self._samples:
            raise KeyError(f"unknown sample: {sample_id}")

    def _require_analysis(self, analysis_id: str) -> None:
        if analysis_id not in self._analyses:
            raise KeyError(f"unknown analysis: {analysis_id}")

    @staticmethod
    def _report_format_metadata(report_format: str) -> tuple[str, str, str]:
        formats = {
            "markdown": ("report.markdown", "text/markdown", "md"),
            "html": ("report.html", "text/html", "html"),
            "pdf": ("report.pdf", "application/pdf", "pdf"),
        }
        if report_format not in formats:
            raise ValueError(f"unsupported report format: {report_format}")
        return formats[report_format]

    def _sync_agent_state(self, analysis_id: str) -> None:
        state = self._agent_states[analysis_id]
        state["analysis"] = dict(self._analyses[analysis_id])
        state["artifacts"] = [
            dict(artifact)
            for artifact in self._artifacts.values()
            if artifact["analysis_id"] == analysis_id
        ]
        state["findings"] = [
            dict(finding)
            for finding in self._findings.values()
            if finding["analysis_id"] == analysis_id
        ]
        state["approval_requests"] = [
            dict(approval) for approval in self._approvals[analysis_id]
        ]
        state["events"] = [dict(event) for event in self._events[analysis_id]]

    def _merge_graph_state(self, analysis_id: str, state: AuditAgentState) -> None:
        analysis = self._analyses[analysis_id]
        analysis.update(state["analysis"])
        self._approvals[analysis_id] = [
            cast(ApprovalRequest, dict(approval))
            for approval in state["approval_requests"]
        ]
        existing_event_ids = {event["id"] for event in self._events[analysis_id]}
        for event in state["events"]:
            if event["id"] in existing_event_ids:
                continue
            self._events[analysis_id].append(
                self._normalize_graph_event(analysis_id, event)
            )
            existing_event_ids.add(event["id"])

    def _normalize_graph_event(
        self,
        analysis_id: str,
        event: AuditEvent,
    ) -> AuditEvent:
        normalized = cast(AuditEvent, dict(event))
        normalized["id"] = self._allocate_id("evt", self._next_event)
        self._next_event += 1
        normalized["sequence"] = len(self._events[analysis_id]) + 1
        normalized["created_at"] = normalized["created_at"] or self._timestamp()
        normalized["run_id"] = self._analyses[analysis_id]["langgraph_run_id"] or ""
        normalized["thread_id"] = self._analyses[analysis_id]["langgraph_thread_id"]
        return normalized

    def _find_approval(self, analysis_id: str, interrupt_id: str) -> ApprovalRequest:
        for approval in self._approvals[analysis_id]:
            if approval["interrupt_id"] == interrupt_id:
                return approval
        raise KeyError(f"unknown interrupt: {interrupt_id}")

    def _has_approved_dangerous_action(self, analysis_id: str) -> bool:
        return any(
            approval["action"] == "firmware-emulation"
            and approval["status"] == "approved"
            for approval in self._approvals[analysis_id]
        )

    @staticmethod
    def _allocate_id(prefix: str, value: int) -> str:
        return f"{prefix}_{value}"

    @staticmethod
    def _timestamp() -> str:
        return "2026-04-24T00:00:00Z"
