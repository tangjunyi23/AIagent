"""In-memory business API mock service."""

from __future__ import annotations

import json
from typing import Any, cast

from audit_common import (
    Analysis,
    ApprovalRequest,
    ApprovalStatus,
    ArtifactRef,
    AuditEvent,
    AuditLog,
    AuditLogOutcome,
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
from audit_api.repository import AuditRepository, InMemoryAuditRepository

PublicResource = dict[str, Any]


class AuditMockService:
    def __init__(self, repository: AuditRepository | None = None) -> None:
        self.repository = repository or InMemoryAuditRepository()
        self._projects = self.repository.projects
        self._samples = self.repository.samples
        self._analyses = self.repository.analyses
        self._artifacts = self.repository.artifacts
        self._findings = self.repository.findings
        self._audit_logs = self.repository.audit_logs
        self._agent_states = self.repository.agent_states
        self._approvals = self.repository.approvals
        self._events = self.repository.events

    def create_project(self, payload: PublicResource) -> PublicResource:
        body = cast(dict[str, Any], to_snake(payload))
        project_id = self._allocate_id("project")
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
        sample_id = self._allocate_id("sample")
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
            "artifact_id": f"artifact_{int(sample_id.rsplit('_', 1)[1]) + 1}",
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
        analysis_id = self._allocate_id("analysis")
        thread_id = self._allocate_id("thread")
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

    def get_artifact_content(
        self,
        artifact_id: str,
        actor_id: str = "mock_analyst",
    ) -> PublicResource:
        if artifact_id not in self._artifacts:
            raise KeyError(f"unknown artifact: {artifact_id}")
        artifact = self._artifacts[artifact_id]
        if not self._is_previewable_artifact(artifact):
            raise ValueError(f"artifact content requires an explicit export path: {artifact_id}")
        analysis = self._analyses[artifact["analysis_id"]]
        encoding, content = self._render_artifact_content(artifact)
        audit_log = self._record_audit_log(
            analysis=analysis,
            actor_id=actor_id,
            action="artifact.content.read",
            resource_type="artifact",
            resource_id=artifact_id,
            outcome="allowed",
            reason="Mock artifact content preview.",
            metadata={
                "artifact_type": artifact["type"],
                "media_type": artifact["media_type"],
                "preview_only": True,
                "redacted": True,
            },
        )
        payload = {
            "artifact_id": artifact_id,
            "analysis_id": artifact["analysis_id"],
            "project_id": artifact["project_id"],
            "media_type": artifact["media_type"],
            "filename": artifact["name"],
            "encoding": encoding,
            "redacted": True,
            "audit_log_id": audit_log["id"],
            "content": content,
        }
        return cast(PublicResource, to_camel(payload))

    def request_artifact_export(
        self,
        artifact_id: str,
        payload: PublicResource,
    ) -> PublicResource:
        if artifact_id not in self._artifacts:
            raise KeyError(f"unknown artifact: {artifact_id}")
        artifact = self._artifacts[artifact_id]
        analysis = self._analyses[artifact["analysis_id"]]
        existing = self._find_pending_artifact_export_approval(analysis["id"], artifact_id)
        if existing is not None:
            return cast(PublicResource, to_camel(existing))

        body = cast(dict[str, Any], to_snake(payload))
        approval = self._create_artifact_export_approval(
            artifact,
            reason=str(
                body.get(
                    "reason",
                    "Artifact export requires approval before content leaves the platform.",
                )
            ),
        )
        self._approvals[analysis["id"]].append(approval)
        self._events[analysis["id"]].append(
            self._create_approval_event(analysis, approval, "approval.requested")
        )
        self._sync_agent_state(analysis["id"])
        return cast(PublicResource, to_camel(approval))

    def create_report(self, payload: PublicResource) -> PublicResource:
        body = cast(dict[str, Any], to_snake(payload))
        analysis_id = str(body["analysis_id"])
        self._require_analysis(analysis_id)
        analysis = self._analyses[analysis_id]
        report_format = str(body.get("format", "markdown"))
        artifact_type, media_type, extension = self._report_format_metadata(report_format)
        version_number = self._next_report_version(analysis_id, report_format)
        report_id = self._report_id(analysis_id, report_format, version_number)
        previous_report_id = (
            self._report_id(analysis_id, report_format, version_number - 1)
            if version_number > 1
            else None
        )
        if previous_report_id is not None and previous_report_id in self._artifacts:
            previous = self._artifacts[previous_report_id]
            previous["metadata"]["latest"] = False
            previous["metadata"]["superseded_by_report_id"] = report_id
        include_unverified = bool(body.get("include_unverified_findings", True))
        findings = [
            finding
            for finding in self._findings.values()
            if finding["analysis_id"] == analysis_id
            and (include_unverified or finding["verification"]["status"] == "verified")
        ]
        artifact: ArtifactRef = {
            "id": report_id,
            "analysis_id": analysis_id,
            "project_id": analysis["project_id"],
            "type": artifact_type,
            "name": f"{analysis_id}-audit-report-v{version_number}.{extension}",
            "media_type": media_type,
            "size": 512,
            "sha256": None,
            "uri": f"memory://reports/{analysis_id}/{report_format}/v{version_number}",
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
                "version_number": version_number,
                "previous_report_id": previous_report_id,
                "latest": True,
                "superseded_by_report_id": None,
            },
            "created_at": self._timestamp(),
        }
        self._artifacts[artifact["id"]] = artifact
        self._events[analysis_id].append(self._create_artifact_event(artifact))
        self._sync_agent_state(analysis_id)
        return cast(PublicResource, to_camel(artifact))

    def get_report(self, report_id: str) -> PublicResource:
        artifact = self._require_report_artifact(report_id)
        return cast(PublicResource, to_camel(artifact))

    def get_report_content(
        self,
        report_id: str,
        actor_id: str = "mock_analyst",
    ) -> PublicResource:
        artifact = self._require_report_artifact(report_id)
        analysis = self._analyses[artifact["analysis_id"]]
        encoding, content = self._render_report_content(artifact)
        audit_log = self._record_audit_log(
            analysis=analysis,
            actor_id=actor_id,
            action="report.content.read",
            resource_type="report",
            resource_id=report_id,
            outcome="allowed",
            reason="Mock report content read.",
            metadata={
                "artifact_type": artifact["type"],
                "media_type": artifact["media_type"],
                "redaction_profile": str(
                    artifact["metadata"].get("redaction_profile", "default")
                ),
            },
        )
        payload = {
            "report_id": report_id,
            "artifact_id": artifact["id"],
            "analysis_id": artifact["analysis_id"],
            "project_id": artifact["project_id"],
            "media_type": artifact["media_type"],
            "filename": artifact["name"],
            "encoding": encoding,
            "redacted": True,
            "audit_log_id": audit_log["id"],
            "content": content,
        }
        return cast(PublicResource, to_camel(payload))

    def list_audit_logs(self, analysis_id: str | None = None) -> list[PublicResource]:
        if analysis_id:
            self._require_analysis(analysis_id)
        logs = [
            log
            for log in self._audit_logs
            if analysis_id is None or log["analysis_id"] == analysis_id
        ]
        return [cast(PublicResource, to_camel(log)) for log in logs]

    def list_findings(
        self,
        filters: PublicResource | str | None = None,
    ) -> PublicResource:
        body = self._finding_query_body(filters)
        analysis_id = body.get("analysis_id")
        project_id = body.get("project_id")
        status = body.get("status")
        severity = body.get("severity")
        limit = self._positive_int(body.get("limit"), default=50, field="limit")
        offset = self._non_negative_int(body.get("offset"), default=0, field="offset")
        if analysis_id is None and project_id is None:
            raise ValueError("analysisId or projectId is required")
        if analysis_id is not None:
            self._require_analysis(str(analysis_id))
        if project_id is not None:
            self._require_project(str(project_id))
        findings = [
            finding
            for finding in self._findings.values()
            if (analysis_id is None or finding["analysis_id"] == str(analysis_id))
            and (project_id is None or finding["project_id"] == str(project_id))
            and (status is None or finding["status"] == str(status))
            and (severity is None or finding["severity"] == str(severity))
        ]
        findings = sorted(findings, key=lambda finding: finding["id"])
        total = len(findings)
        page = findings[offset : offset + limit]
        next_offset = offset + limit if offset + limit < total else None
        return {
            "items": [cast(PublicResource, to_camel(finding)) for finding in page],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "nextOffset": next_offset,
            },
        }

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
            analysis["langgraph_run_id"] = self._allocate_id("run")
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

    def cancel_analysis(self, analysis_id: str) -> PublicResource:
        self._require_analysis(analysis_id)
        analysis = self._analyses[analysis_id]
        if analysis["status"] == "cancelled":
            return cast(PublicResource, to_camel(analysis))
        if analysis["status"] == "succeeded":
            raise ValueError(f"analysis already succeeded: {analysis_id}")
        analysis["status"] = "cancelled"
        analysis["updated_at"] = self._timestamp()
        self._events[analysis_id].append(self._create_run_event(analysis, "run.cancelled"))
        self._sync_agent_state(analysis_id)
        return cast(PublicResource, to_camel(analysis))

    def branch_analysis(
        self,
        analysis_id: str,
        payload: PublicResource,
    ) -> PublicResource:
        self._require_analysis(analysis_id)
        body = cast(dict[str, Any], to_snake(payload))
        checkpoint_id = str(body.get("checkpoint_id", f"checkpoint_{analysis_id}_latest"))
        reason = str(body.get("reason", "Branch from checkpoint."))
        source = self._analyses[analysis_id]
        branch_id = self._allocate_id("analysis")
        thread_id = self._allocate_id("thread")
        branch: Analysis = {
            "id": branch_id,
            "project_id": source["project_id"],
            "sample_ids": list(source["sample_ids"]),
            "scenario": source["scenario"],
            "status": "queued",
            "policy": cast(AuditPolicy, dict(source["policy"])),
            "langgraph_thread_id": thread_id,
            "langgraph_run_id": None,
            "created_at": self._timestamp(),
            "updated_at": self._timestamp(),
        }
        self._analyses[branch_id] = branch
        artifact_id_map = self._copy_branch_artifacts(analysis_id, branch_id, checkpoint_id)
        self._copy_branch_findings(analysis_id, branch_id, artifact_id_map, checkpoint_id)
        self._approvals[branch_id] = self._copy_branch_approvals(
            analysis_id,
            branch_id,
            artifact_id_map,
            checkpoint_id,
        )
        self._events[branch_id] = [
            self._create_run_queued_event(branch),
            self._create_state_snapshot_event(
                branch,
                source_analysis_id=analysis_id,
                checkpoint_id=checkpoint_id,
                reason=reason,
            ),
        ]
        self._agent_states[branch_id] = create_initial_state(
            analysis_id=branch_id,
            project_id=branch["project_id"],
            sample_ids=branch["sample_ids"],
            scenario=branch["scenario"],
            thread_id=thread_id,
        )
        self._sync_agent_state(branch_id)
        return cast(PublicResource, to_camel(branch))

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
        analysis = self._analyses[analysis_id]
        self._record_audit_log(
            analysis=analysis,
            actor_id=approval["decided_by"],
            action=event_type,
            resource_type="approval",
            resource_id=approval["id"],
            outcome="allowed",
            reason=approval["decision_reason"],
            metadata={
                "interrupt_id": approval["interrupt_id"],
                "approval_action": approval["action"],
                "approval_status": approval["status"],
            },
        )
        self._events[analysis_id].append(
            self._create_approval_event(
                analysis,
                approval,
                event_type,
            )
        )
        self._sync_agent_state(analysis_id)
        return cast(PublicResource, to_camel(approval))

    def _create_run_queued_event(self, analysis: Analysis) -> AuditEvent:
        event_id = self._allocate_id("evt")
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
        event_id = self._allocate_id("evt")
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
        event_id = self._allocate_id("evt")
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
        event_id = self._allocate_id("evt")
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

    def _create_state_snapshot_event(
        self,
        analysis: Analysis,
        source_analysis_id: str,
        checkpoint_id: str,
        reason: str,
    ) -> AuditEvent:
        event_id = self._allocate_id("evt")
        artifacts = [
            artifact
            for artifact in self._artifacts.values()
            if artifact["analysis_id"] == analysis["id"]
        ]
        findings = [
            finding
            for finding in self._findings.values()
            if finding["analysis_id"] == analysis["id"]
        ]
        approvals = self._approvals.get(analysis["id"], [])
        return {
            "id": event_id,
            "sequence": len(self._events.get(analysis["id"], [])) + 1,
            "analysis_id": analysis["id"],
            "run_id": "",
            "thread_id": analysis["langgraph_thread_id"],
            "node": "branch_from_checkpoint",
            "agent": None,
            "type": "state.snapshot",
            "payload": {
                "checkpoint_id": checkpoint_id,
                "state_version": 1,
                "artifact_ids": [artifact["id"] for artifact in artifacts],
                "finding_ids": [finding["id"] for finding in findings],
                "approval_ids": [approval["id"] for approval in approvals],
                "next_actions": [
                    "Review branched checkpoint state.",
                    "Start a new run when ready.",
                ],
                "source_analysis_id": source_analysis_id,
                "reason": reason,
            },
            "created_at": self._timestamp(),
            "trace_id": None,
        }

    def _record_audit_log(
        self,
        analysis: Analysis,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: AuditLogOutcome,
        reason: str | None,
        metadata: dict[str, object],
    ) -> AuditLog:
        project = self._projects[analysis["project_id"]]
        log: AuditLog = {
            "id": self._allocate_id("audit"),
            "tenant_id": project["tenant_id"],
            "project_id": analysis["project_id"],
            "analysis_id": analysis["id"],
            "actor_id": actor_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "outcome": outcome,
            "reason": reason,
            "metadata": metadata,
            "created_at": self._timestamp(),
        }
        self._audit_logs.append(log)
        return log

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

    def _create_artifact_export_approval(
        self,
        artifact: ArtifactRef,
        reason: str,
    ) -> ApprovalRequest:
        return {
            "id": f"approval_{artifact['id']}_artifact_export",
            "analysis_id": artifact["analysis_id"],
            "project_id": artifact["project_id"],
            "interrupt_id": f"interrupt_{artifact['id']}_artifact_export",
            "action": "artifact-export",
            "status": "pending",
            "requested_by_agent": "artifact_service",
            "reason": reason,
            "risk_summary": (
                "Artifact export may disclose samples, credentials, exploit evidence, "
                "or other sensitive analysis outputs."
            ),
            "proposed_parameters": {
                "artifact_id": artifact["id"],
                "artifact_type": artifact["type"],
                "media_type": artifact["media_type"],
                "filename": artifact["name"],
                "preview_only": False,
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
        event_id = self._allocate_id("evt")
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

    def _require_report_artifact(self, report_id: str) -> ArtifactRef:
        if report_id not in self._artifacts:
            raise KeyError(f"unknown report: {report_id}")
        artifact = self._artifacts[report_id]
        if not artifact["type"].startswith("report."):
            raise KeyError(f"unknown report: {report_id}")
        return artifact

    @staticmethod
    def _finding_query_body(filters: PublicResource | str | None) -> dict[str, Any]:
        if filters is None:
            return {}
        if isinstance(filters, str):
            return {"analysis_id": filters}
        return cast(dict[str, Any], to_snake(filters))

    @staticmethod
    def _positive_int(value: object, default: int, field: str) -> int:
        if value in (None, ""):
            return default
        parsed = int(cast(str | int, value))
        if parsed < 1:
            raise ValueError(f"{field} must be greater than zero")
        return parsed

    @staticmethod
    def _non_negative_int(value: object, default: int, field: str) -> int:
        if value in (None, ""):
            return default
        parsed = int(cast(str | int, value))
        if parsed < 0:
            raise ValueError(f"{field} must be greater than or equal to zero")
        return parsed

    def _next_report_version(self, analysis_id: str, report_format: str) -> int:
        prefix = f"report_{analysis_id}_{report_format}"
        return (
            sum(
                1
                for artifact in self._artifacts.values()
                if artifact["id"] == prefix or artifact["id"].startswith(f"{prefix}_v")
            )
            + 1
        )

    @staticmethod
    def _report_id(analysis_id: str, report_format: str, version_number: int) -> str:
        base_id = f"report_{analysis_id}_{report_format}"
        if version_number == 1:
            return base_id
        return f"{base_id}_v{version_number}"

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

    @staticmethod
    def _render_report_content(artifact: ArtifactRef) -> tuple[str, str]:
        finding_count = artifact["metadata"].get("finding_count", 0)
        redaction_profile = artifact["metadata"].get("redaction_profile", "default")
        if artifact["type"] == "report.html":
            return (
                "utf-8",
                "<h1>Mock Binary Audit Report</h1>"
                f"<p>Analysis: {artifact['analysis_id']}</p>"
                f"<p>Findings included: {finding_count}</p>"
                f"<p>Redaction profile: {redaction_profile}</p>",
            )
        if artifact["type"] == "report.pdf":
            return ("base64", "JVBERi0xLjQKJSBtb2NrIHJlZGFjdGVkIHJlcG9ydAo=")
        return (
            "utf-8",
            "# Mock Binary Audit Report\n\n"
            f"Analysis: {artifact['analysis_id']}\n"
            f"Findings included: {finding_count}\n"
            f"Redaction profile: {redaction_profile}\n\n"
            "This mock content excludes raw samples, credentials, PCAP data, "
            "and bulk tool outputs.",
        )

    @staticmethod
    def _is_previewable_artifact(artifact: ArtifactRef) -> bool:
        return artifact["type"] == "vuln.finding_evidence"

    @staticmethod
    def _render_artifact_content(artifact: ArtifactRef) -> tuple[str, str]:
        preview = {
            "title": "Mock artifact preview",
            "artifactId": artifact["id"],
            "artifactType": artifact["type"],
            "summary": artifact["metadata"].get("summary"),
            "redacted": True,
        }
        return "utf-8", json.dumps(preview, sort_keys=True)

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
        normalized["id"] = self._allocate_id("evt")
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

    def _find_pending_artifact_export_approval(
        self,
        analysis_id: str,
        artifact_id: str,
    ) -> ApprovalRequest | None:
        for approval in self._approvals[analysis_id]:
            if (
                approval["action"] == "artifact-export"
                and approval["status"] == "pending"
                and approval["proposed_parameters"].get("artifact_id") == artifact_id
            ):
                return approval
        return None

    def _copy_branch_artifacts(
        self,
        source_analysis_id: str,
        branch_analysis_id: str,
        checkpoint_id: str,
    ) -> dict[str, str]:
        artifact_id_map: dict[str, str] = {}
        source_artifacts = [
            artifact
            for artifact in self._artifacts.values()
            if artifact["analysis_id"] == source_analysis_id
        ]
        for artifact in source_artifacts:
            branched_id = self._branch_id(artifact["id"], source_analysis_id, branch_analysis_id)
            artifact_id_map[artifact["id"]] = branched_id
            branched_artifact = cast(ArtifactRef, dict(artifact))
            branched_artifact["id"] = branched_id
            branched_artifact["analysis_id"] = branch_analysis_id
            branched_artifact["producer"] = dict(artifact["producer"])
            branched_artifact["metadata"] = {
                **dict(artifact["metadata"]),
                "branched_from_analysis_id": source_analysis_id,
                "branched_from_artifact_id": artifact["id"],
                "branched_from_checkpoint_id": checkpoint_id,
            }
            branched_artifact["created_at"] = self._timestamp()
            self._artifacts[branched_id] = branched_artifact
        return artifact_id_map

    def _copy_branch_findings(
        self,
        source_analysis_id: str,
        branch_analysis_id: str,
        artifact_id_map: dict[str, str],
        checkpoint_id: str,
    ) -> None:
        source_findings = [
            finding
            for finding in self._findings.values()
            if finding["analysis_id"] == source_analysis_id
        ]
        for finding in source_findings:
            branched_id = self._branch_id(finding["id"], source_analysis_id, branch_analysis_id)
            branched_finding = cast(Finding, dict(finding))
            branched_finding["id"] = branched_id
            branched_finding["analysis_id"] = branch_analysis_id
            branched_finding["evidence_artifact_ids"] = [
                artifact_id_map.get(artifact_id, artifact_id)
                for artifact_id in finding["evidence_artifact_ids"]
            ]
            branched_finding["verification"] = dict(finding["verification"])
            branched_finding["created_at"] = self._timestamp()
            branched_finding["updated_at"] = self._timestamp()
            branched_finding["verification"]["notes"] = (
                f"Branched from {source_analysis_id} at {checkpoint_id}."
            )
            self._findings[branched_id] = branched_finding

    def _copy_branch_approvals(
        self,
        source_analysis_id: str,
        branch_analysis_id: str,
        artifact_id_map: dict[str, str],
        checkpoint_id: str,
    ) -> list[ApprovalRequest]:
        branched_approvals: list[ApprovalRequest] = []
        for approval in self._approvals[source_analysis_id]:
            branched_approval = cast(ApprovalRequest, dict(approval))
            branched_approval["id"] = self._branch_id(
                approval["id"],
                source_analysis_id,
                branch_analysis_id,
            )
            branched_approval["analysis_id"] = branch_analysis_id
            branched_approval["interrupt_id"] = self._branch_id(
                approval["interrupt_id"],
                source_analysis_id,
                branch_analysis_id,
            )
            branched_approval["proposed_parameters"] = cast(
                dict[str, object],
                self._branch_value(
                    approval["proposed_parameters"],
                    source_analysis_id,
                    branch_analysis_id,
                    artifact_id_map,
                ),
            )
            branched_approval["reason"] = (
                f"{approval['reason']} Branched from {source_analysis_id} at {checkpoint_id}."
            )
            branched_approvals.append(branched_approval)
        return branched_approvals

    def _branch_id(
        self,
        value: str,
        source_analysis_id: str,
        branch_analysis_id: str,
    ) -> str:
        if source_analysis_id in value:
            return value.replace(source_analysis_id, branch_analysis_id)
        return f"{value}_branch_{branch_analysis_id}"

    def _branch_value(
        self,
        value: object,
        source_analysis_id: str,
        branch_analysis_id: str,
        artifact_id_map: dict[str, str],
    ) -> object:
        if isinstance(value, dict):
            return {
                key: self._branch_value(
                    item,
                    source_analysis_id,
                    branch_analysis_id,
                    artifact_id_map,
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                self._branch_value(
                    item,
                    source_analysis_id,
                    branch_analysis_id,
                    artifact_id_map,
                )
                for item in value
            ]
        if isinstance(value, str):
            if value in artifact_id_map:
                return artifact_id_map[value]
            return value.replace(source_analysis_id, branch_analysis_id)
        return value

    def _has_approved_dangerous_action(self, analysis_id: str) -> bool:
        return any(
            approval["action"] == "firmware-emulation"
            and approval["status"] == "approved"
            for approval in self._approvals[analysis_id]
        )

    def _allocate_id(self, prefix: str) -> str:
        return self.repository.allocate_id(prefix)

    @staticmethod
    def _timestamp() -> str:
        return "2026-04-24T00:00:00Z"
