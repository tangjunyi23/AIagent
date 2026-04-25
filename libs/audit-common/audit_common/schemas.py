"""Typed schema contracts shared by audit API, agents, workers, and web clients."""

from __future__ import annotations

from typing import Literal, TypeAlias, TypedDict

Classification: TypeAlias = Literal[
    "public", "internal", "confidential", "restricted"
]
SampleFormat: TypeAlias = Literal[
    "ELF", "PE", "MachO", "APK", "Firmware", "Archive", "Unknown"
]
Scenario: TypeAlias = Literal[
    "ctf", "risk", "malware", "firmware", "code-audit", "mobile"
]
RunStatus: TypeAlias = Literal[
    "queued", "running", "interrupted", "succeeded", "failed", "cancelled"
]
AnalysisStatus: TypeAlias = RunStatus
Severity: TypeAlias = Literal["info", "low", "medium", "high", "critical"]
FindingStatus: TypeAlias = Literal[
    "draft", "needs-review", "confirmed", "false-positive", "accepted-risk", "fixed"
]
ApprovalStatus: TypeAlias = Literal[
    "pending", "approved", "rejected", "expired", "cancelled"
]
ToolExecutionStatus: TypeAlias = Literal[
    "queued", "running", "succeeded", "failed", "timed-out", "cancelled", "blocked"
]
NetworkPolicy: TypeAlias = Literal["none", "allowlist", "unrestricted"]
SimulationMode: TypeAlias = Literal["skip", "component", "qemu-system", "emba"]
ApprovalAction: TypeAlias = Literal[
    "dynamic-execution",
    "network-enable",
    "exploit-verification",
    "firmware-emulation",
    "artifact-export",
]
AuditEventType: TypeAlias = Literal[
    "run.queued",
    "run.started",
    "run.interrupted",
    "run.resumed",
    "run.succeeded",
    "run.failed",
    "run.cancelled",
    "state.snapshot",
    "agent.started",
    "agent.heartbeat",
    "agent.completed",
    "agent.failed",
    "token.delta",
    "tool.queued",
    "tool.started",
    "tool.output_chunk",
    "tool.completed",
    "tool.failed",
    "tool.cancelled",
    "artifact.created",
    "finding.created",
    "finding.updated",
    "approval.requested",
    "approval.approved",
    "approval.rejected",
    "policy.denied",
    "error.created",
]

SAMPLE_FORMAT_VALUES: tuple[str, ...] = (
    "ELF",
    "PE",
    "MachO",
    "APK",
    "Firmware",
    "Archive",
    "Unknown",
)
RUN_STATUS_VALUES: tuple[str, ...] = (
    "queued",
    "running",
    "interrupted",
    "succeeded",
    "failed",
    "cancelled",
)
ANALYSIS_STATUS_VALUES = RUN_STATUS_VALUES
SEVERITY_VALUES: tuple[str, ...] = ("info", "low", "medium", "high", "critical")
FINDING_STATUS_VALUES: tuple[str, ...] = (
    "draft",
    "needs-review",
    "confirmed",
    "false-positive",
    "accepted-risk",
    "fixed",
)
TOOL_EXECUTION_STATUS_VALUES: tuple[str, ...] = (
    "queued",
    "running",
    "succeeded",
    "failed",
    "timed-out",
    "cancelled",
    "blocked",
)
NETWORK_POLICY_VALUES: tuple[str, ...] = ("none", "allowlist", "unrestricted")
SIMULATION_MODE_VALUES: tuple[str, ...] = ("skip", "component", "qemu-system", "emba")
APPROVAL_ACTION_VALUES: tuple[str, ...] = (
    "dynamic-execution",
    "network-enable",
    "exploit-verification",
    "firmware-emulation",
    "artifact-export",
)
AUDIT_EVENT_TYPE_VALUES: tuple[str, ...] = (
    "run.queued",
    "run.started",
    "run.interrupted",
    "run.resumed",
    "run.succeeded",
    "run.failed",
    "run.cancelled",
    "state.snapshot",
    "agent.started",
    "agent.heartbeat",
    "agent.completed",
    "agent.failed",
    "token.delta",
    "tool.queued",
    "tool.started",
    "tool.output_chunk",
    "tool.completed",
    "tool.failed",
    "tool.cancelled",
    "artifact.created",
    "finding.created",
    "finding.updated",
    "approval.requested",
    "approval.approved",
    "approval.rejected",
    "policy.denied",
    "error.created",
)
ARTIFACT_TYPE_VALUES: tuple[str, ...] = (
    "sample.original",
    "sample.extracted",
    "static.objdump",
    "static.readelf",
    "static.nm",
    "static.strings",
    "static.ghidra.project",
    "static.ghidra.decompile",
    "static.idat.export",
    "static.jadx.project",
    "static.joern.cpg",
    "firmware.binwalk.tree",
    "firmware.unblob.tree",
    "firmware.emba.report",
    "firmware.rootfs",
    "firmware.qemu.snapshot",
    "dynamic.pcap",
    "dynamic.http_archive",
    "dynamic.command_output",
    "vuln.finding_evidence",
    "report.markdown",
    "report.html",
    "report.pdf",
)
DANGEROUS_APPROVAL_ACTIONS: frozenset[ApprovalAction] = frozenset(
    (
        "dynamic-execution",
        "network-enable",
        "exploit-verification",
        "firmware-emulation",
    )
)


class Project(TypedDict):
    id: str
    tenant_id: str
    name: str
    classification: Classification
    created_at: str
    updated_at: str


class Sample(TypedDict):
    id: str
    project_id: str
    filename: str
    sha256: str
    size: int
    format: SampleFormat
    arch: str | None
    mime_type: str | None
    magic: str | None
    uploaded_at: str
    artifact_id: str


class AuditPolicy(TypedDict):
    allow_dynamic_execution: bool
    allow_network: bool
    network_policy: NetworkPolicy
    network_allowlist: list[str]
    allow_exploit_verification: bool
    require_approval_for_dynamic: bool
    require_approval_for_network: bool
    require_approval_for_exploit: bool
    max_tool_runtime_seconds: int
    max_agent_runtime_seconds: int
    max_cpu_cores: float
    max_memory_mb: int
    secret_redaction: bool


DynamicExecutionPolicy = AuditPolicy


class Analysis(TypedDict):
    id: str
    project_id: str
    sample_ids: list[str]
    scenario: Scenario
    status: AnalysisStatus
    policy: AuditPolicy
    langgraph_thread_id: str
    langgraph_run_id: str | None
    created_at: str
    updated_at: str


class ArtifactProducer(TypedDict):
    agent: str | None
    node: str | None
    tool_execution_id: str | None


class ArtifactRef(TypedDict):
    id: str
    analysis_id: str
    project_id: str
    type: str
    name: str
    media_type: str
    size: int
    sha256: str | None
    uri: str
    producer: ArtifactProducer
    metadata: dict[str, object]
    created_at: str


class FindingVerification(TypedDict):
    status: Literal["pending", "approved", "blocked", "verified", "failed", "skipped"]
    approval_id: str | None
    notes: str | None


class Finding(TypedDict):
    id: str
    analysis_id: str
    project_id: str
    title: str
    description: str
    severity: Severity
    confidence: float
    status: FindingStatus
    cwe: str | None
    cve: str | None
    affected_component: str | None
    evidence_artifact_ids: list[str]
    verification: FindingVerification
    created_at: str
    updated_at: str


class ToolExecutionLimits(TypedDict):
    wall_time_seconds: int
    cpu_cores: float
    memory_mb: int
    disk_mb: int
    network_policy: NetworkPolicy


class ToolExecution(TypedDict):
    id: str
    analysis_id: str
    project_id: str
    tool: str
    adapter: str
    status: ToolExecutionStatus
    input_artifact_ids: list[str]
    output_artifact_ids: list[str]
    sanitized_args: dict[str, object]
    approval_id: str | None
    started_at: str | None
    finished_at: str | None
    exit_code: int | None
    limits: ToolExecutionLimits
    error: str | None


class ApprovalRequest(TypedDict):
    id: str
    analysis_id: str
    project_id: str
    interrupt_id: str
    action: ApprovalAction
    status: ApprovalStatus
    requested_by_agent: str
    reason: str
    risk_summary: str
    proposed_parameters: dict[str, object]
    created_at: str
    decided_at: str | None
    decided_by: str | None
    decision_reason: str | None


class AuditEvent(TypedDict):
    id: str
    sequence: int
    analysis_id: str
    run_id: str
    thread_id: str | None
    node: str | None
    agent: str | None
    type: AuditEventType
    payload: dict[str, object]
    created_at: str
    trace_id: str | None


class ErrorEnvelope(TypedDict):
    code: str
    message: str
    request_id: str
    details: dict[str, object]


def is_dangerous_approval_action(action: ApprovalAction) -> bool:
    """Return whether an approval action gates dangerous execution."""

    return action in DANGEROUS_APPROVAL_ACTIONS
