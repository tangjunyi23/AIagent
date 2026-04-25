"""Repository boundary for audit API resource storage."""

from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from audit_agents import AuditAgentState
from audit_common import (
    Analysis,
    ApprovalRequest,
    ArtifactRef,
    AuditEvent,
    AuditLog,
    Finding,
    Project,
    Sample,
)


class AuditRepository(Protocol):
    projects: dict[str, Project]
    samples: dict[str, Sample]
    analyses: dict[str, Analysis]
    artifacts: dict[str, ArtifactRef]
    findings: dict[str, Finding]
    audit_logs: list[AuditLog]
    agent_states: dict[str, AuditAgentState]
    approvals: dict[str, list[ApprovalRequest]]
    events: dict[str, list[AuditEvent]]

    def allocate_id(self, prefix: str) -> str:
        """Allocate the next deterministic ID for a resource prefix."""
        ...


class InMemoryAuditRepository:
    """In-memory repository used by the mock API service."""

    def __init__(self) -> None:
        self.projects: dict[str, Project] = {}
        self.samples: dict[str, Sample] = {}
        self.analyses: dict[str, Analysis] = {}
        self.artifacts: dict[str, ArtifactRef] = {}
        self.findings: dict[str, Finding] = {}
        self.audit_logs: list[AuditLog] = []
        self.agent_states: dict[str, AuditAgentState] = {}
        self.approvals: dict[str, list[ApprovalRequest]] = {}
        self.events: dict[str, list[AuditEvent]] = {}
        self._next_ids: defaultdict[str, int] = defaultdict(lambda: 1)

    def allocate_id(self, prefix: str) -> str:
        value = self._next_ids[prefix]
        self._next_ids[prefix] += 1
        return f"{prefix}_{value}"
