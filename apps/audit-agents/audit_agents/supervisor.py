"""Minimal supervisor graph and approval-gate nodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from audit_common.schemas import ApprovalRequest, AuditEvent

from audit_agents.state import AuditAgentState

Node = Callable[[AuditAgentState], AuditAgentState]


@dataclass(frozen=True)
class SupervisorGraphSpec:
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    compiled_graph: Any | None = None

    def invoke(self, state: AuditAgentState) -> AuditAgentState:
        next_state = triage_sample(state)
        return request_dangerous_action_approval(next_state)


def _copy_state(state: AuditAgentState) -> AuditAgentState:
    return {
        "analysis": dict(state["analysis"]),
        "artifacts": list(state["artifacts"]),
        "findings": list(state["findings"]),
        "tool_executions": list(state["tool_executions"]),
        "approval_requests": list(state["approval_requests"]),
        "events": list(state["events"]),
    }


def triage_sample(state: AuditAgentState) -> AuditAgentState:
    next_state = _copy_state(state)
    next_state["analysis"]["status"] = "running"
    event: AuditEvent = {
        "id": "evt_agent_started",
        "sequence": len(next_state["events"]) + 1,
        "analysis_id": next_state["analysis"]["id"],
        "run_id": next_state["analysis"]["langgraph_run_id"] or "",
        "thread_id": next_state["analysis"]["langgraph_thread_id"],
        "node": "triage",
        "agent": "supervisor",
        "type": "agent.started",
        "payload": {"scenario": next_state["analysis"]["scenario"]},
        "created_at": "",
        "trace_id": None,
    }
    next_state["events"].append(event)
    return next_state


def request_dangerous_action_approval(state: AuditAgentState) -> AuditAgentState:
    next_state = _copy_state(state)
    next_state["analysis"]["status"] = "interrupted"
    for existing_approval in next_state["approval_requests"]:
        if (
            existing_approval["action"] == "firmware-emulation"
            and existing_approval["status"] == "pending"
        ):
            return next_state
    approval: ApprovalRequest = {
        "id": "approval_firmware_emulation",
        "analysis_id": next_state["analysis"]["id"],
        "project_id": next_state["analysis"]["project_id"],
        "interrupt_id": "interrupt_firmware_emulation",
        "action": "firmware-emulation",
        "status": "pending",
        "requested_by_agent": "supervisor",
        "reason": "Firmware emulation is a dangerous dynamic action.",
        "risk_summary": "Execution is blocked until a human approves sandbox limits.",
        "proposed_parameters": {
            "network_policy": next_state["analysis"]["policy"]["network_policy"],
            "max_runtime_seconds": next_state["analysis"]["policy"]["max_agent_runtime_seconds"],
        },
        "created_at": "",
        "decided_at": None,
        "decided_by": None,
        "decision_reason": None,
    }
    event: AuditEvent = {
        "id": "evt_approval_requested",
        "sequence": len(next_state["events"]) + 1,
        "analysis_id": next_state["analysis"]["id"],
        "run_id": next_state["analysis"]["langgraph_run_id"] or "",
        "thread_id": next_state["analysis"]["langgraph_thread_id"],
        "node": "approval_gate",
        "agent": "supervisor",
        "type": "approval.requested",
        "payload": {
            "approval_id": approval["id"],
            "action": approval["action"],
            "status": approval["status"],
        },
        "created_at": "",
        "trace_id": None,
    }
    next_state["approval_requests"].append(approval)
    next_state["events"].append(event)
    return next_state


def build_supervisor_graph() -> SupervisorGraphSpec:
    compiled_graph = None
    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError:
        return SupervisorGraphSpec(
            nodes=("triage", "approval_gate"),
            edges=(("__start__", "triage"), ("triage", "approval_gate"), ("approval_gate", "__end__")),
        )

    graph = StateGraph(AuditAgentState)
    graph.add_node("triage", triage_sample)
    graph.add_node("approval_gate", request_dangerous_action_approval)
    graph.add_edge(START, "triage")
    graph.add_edge("triage", "approval_gate")
    graph.add_edge("approval_gate", END)
    compiled_graph = graph.compile()
    return SupervisorGraphSpec(
        nodes=("triage", "approval_gate"),
        edges=((START, "triage"), ("triage", "approval_gate"), ("approval_gate", END)),
        compiled_graph=compiled_graph,
    )
