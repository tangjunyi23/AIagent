"""Product-owned LangGraph state for binary audit agent runs."""

from __future__ import annotations

from typing import TypedDict

from audit_common.schemas import (
    Analysis,
    ApprovalRequest,
    ArtifactRef,
    AuditEvent,
    Finding,
    Scenario,
    ToolExecution,
)


class AuditAgentState(TypedDict):
    analysis: Analysis
    artifacts: list[ArtifactRef]
    findings: list[Finding]
    tool_executions: list[ToolExecution]
    approval_requests: list[ApprovalRequest]
    events: list[AuditEvent]


def create_initial_state(
    *,
    analysis_id: str,
    project_id: str,
    sample_ids: list[str],
    scenario: Scenario,
    thread_id: str,
) -> AuditAgentState:
    analysis: Analysis = {
        "id": analysis_id,
        "project_id": project_id,
        "sample_ids": sample_ids,
        "scenario": scenario,
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
        "langgraph_thread_id": thread_id,
        "langgraph_run_id": None,
        "created_at": "",
        "updated_at": "",
    }
    return {
        "analysis": analysis,
        "artifacts": [],
        "findings": [],
        "tool_executions": [],
        "approval_requests": [],
        "events": [],
    }
