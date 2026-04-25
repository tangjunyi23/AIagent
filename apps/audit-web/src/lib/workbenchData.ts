import type {
  ApprovalRequest,
  ApprovalStatus,
  ArtifactRef,
  AuditEvent,
  AuditEventType,
  AuditLog,
  AuditWorkbench,
  Finding,
  ReportArtifact
} from "./types";

const baseTimestamp = "2026-04-25T00:00:00Z";
const decisionTimestamp = "2026-04-25T01:00:00Z";

export function createMockWorkbench(): AuditWorkbench {
  const artifact: ArtifactRef = {
    id: "artifact_analysis_1_evidence",
    analysisId: "analysis_1",
    projectId: "project_1",
    type: "vuln.finding_evidence",
    name: "mock-static-evidence.json",
    mediaType: "application/json",
    size: 512,
    uri: "memory://artifacts/analysis_1/static-evidence",
    createdAt: baseTimestamp,
    redacted: true,
    preview:
      '{"artifactId":"artifact_analysis_1_evidence","artifactType":"vuln.finding_evidence","redacted":true,"summary":"脱敏静态证据显示固件字符串引用了 shell 执行路径。"}'
  };
  const finding: Finding = {
    id: "finding_analysis_1_static_strings",
    analysisId: "analysis_1",
    projectId: "project_1",
    title: "模拟固件命令执行风险",
    description:
      "静态证据发现命令执行相关字符串，需要审计员复核后才能进入动态验证。",
    severity: "high",
    confidence: 0.55,
    status: "needs-review",
    cwe: "CWE-78",
    cve: null,
    affectedComponent: "web/cgi-bin",
    evidenceArtifactIds: [artifact.id]
  };
  const approval: ApprovalRequest = {
    id: "approval_analysis_1_firmware_emulation",
    analysisId: "analysis_1",
    projectId: "project_1",
    interruptId: "interrupt_analysis_1_firmware_emulation",
    action: "firmware-emulation",
    status: "pending",
    requestedByAgent: "supervisor",
    reason: "QEMU 组件模拟可能暴露服务，必须保持人工审批。",
    riskSummary:
      "固件模拟可能执行不可信代码。除非显式批准，外连网络保持关闭。",
    proposedParameters: {
      simulationMode: "component",
      networkPolicy: "none",
      maxToolRuntimeSeconds: 900
    },
    createdAt: baseTimestamp,
    decidedAt: null,
    decidedBy: null,
    decisionReason: null
  };
  const report: ReportArtifact = {
    id: "report_analysis_1_markdown",
    type: "report.markdown",
    name: "analysis_1-audit-report-v1.md",
    versionNumber: 1,
    latest: true,
    redacted: true
  };

  return {
    analysis: {
      id: "analysis_1",
      projectId: "project_1",
      sampleIds: ["sample_1"],
      scenario: "firmware",
      status: "interrupted",
      langgraphThreadId: "thread_1",
      langgraphRunId: "run_analysis_1",
      updatedAt: baseTimestamp
    },
    state: {
      checkpointId: "checkpoint_analysis_1_interrupt",
      stateVersion: 3,
      artifactIds: [artifact.id],
      findingIds: [finding.id],
      approvalIds: [approval.id],
      nextActions: [
        "复核固件模拟审批",
        "检查脱敏证据文件",
        "报告导出前确认漏洞状态"
      ]
    },
    events: [
      createEvent(1, "run.queued", "api", "mock_run_queue", { status: "queued" }),
      createEvent(2, "agent.started", "supervisor", "triage", {
        status: "started",
        message: "Supervisor 已接收固件分析任务。"
      }),
      createEvent(3, "approval.requested", "supervisor", "approval_gate", {
        approvalId: approval.id,
        interruptId: approval.interruptId,
        action: approval.action,
        status: approval.status,
        riskSummary: approval.riskSummary,
        proposedParameters: approval.proposedParameters,
        decisionReason: null
      }),
      createEvent(4, "run.interrupted", "supervisor", "approval_gate", {
        status: "interrupted",
        checkpointId: "checkpoint_analysis_1_interrupt",
        message: "高风险固件模拟正在等待审计员审批。"
      })
    ],
    approvals: [approval],
    artifacts: [artifact],
    findings: [finding],
    reports: [report],
    auditLogs: [
      {
        id: "audit_1",
        projectId: "project_1",
        analysisId: "analysis_1",
        actorId: "mock_analyst",
        action: "artifact.content.read",
        resourceType: "artifact",
        resourceId: artifact.id,
        outcome: "allowed",
        reason: "工作台打开了脱敏证据预览。",
        createdAt: baseTimestamp
      }
    ]
  };
}

export function approveInterrupt(
  workbench: AuditWorkbench,
  interruptId: string,
  decisionReason: string
): AuditWorkbench {
  return decideInterrupt(workbench, interruptId, "approved", decisionReason);
}

export function rejectInterrupt(
  workbench: AuditWorkbench,
  interruptId: string,
  decisionReason: string
): AuditWorkbench {
  return decideInterrupt(workbench, interruptId, "rejected", decisionReason);
}

export function cancelRun(workbench: AuditWorkbench): AuditWorkbench {
  const event = createEvent(nextSequence(workbench.events), "run.cancelled", "api", "mock_cancel", {
    status: "cancelled",
    checkpointId: workbench.state.checkpointId,
    message: "分析已由审计员取消"
  });
  return {
    ...workbench,
    analysis: {
      ...workbench.analysis,
      status: "cancelled",
      updatedAt: decisionTimestamp
    },
    state: {
      ...workbench.state,
      stateVersion: workbench.state.stateVersion + 1,
      nextActions: ["分析已由审计员取消", "如需继续，请从最近检查点创建分支"]
    },
    events: [...workbench.events, event]
  };
}

export function branchFromCheckpoint(
  workbench: AuditWorkbench,
  checkpointId: string,
  reason: string
): AuditWorkbench {
  const sourceAnalysisId = workbench.analysis.id;
  const branchAnalysisId = "analysis_2";
  const artifactIdMap = new Map(
    workbench.artifacts.map((artifact) => [
      artifact.id,
      branchId(artifact.id, sourceAnalysisId, branchAnalysisId)
    ])
  );
  const artifacts = workbench.artifacts.map((artifact) => ({
    ...artifact,
    id: artifactIdMap.get(artifact.id) ?? artifact.id,
    analysisId: branchAnalysisId,
    uri: artifact.uri.replace(sourceAnalysisId, branchAnalysisId)
  }));
  const findings = workbench.findings.map((finding) => ({
    ...finding,
    id: branchId(finding.id, sourceAnalysisId, branchAnalysisId),
    analysisId: branchAnalysisId,
    evidenceArtifactIds: finding.evidenceArtifactIds.map(
      (artifactId) => artifactIdMap.get(artifactId) ?? artifactId
    )
  }));
  const approvals = workbench.approvals.map((approval) => ({
    ...approval,
    id: branchId(approval.id, sourceAnalysisId, branchAnalysisId),
    analysisId: branchAnalysisId,
    interruptId: branchId(approval.interruptId, sourceAnalysisId, branchAnalysisId),
    status: "pending" as const,
    decidedAt: null,
    decidedBy: null,
    decisionReason: null
  }));
  const events = [
    createBranchEvent(1, "run.queued", branchAnalysisId, "thread_2", {
      status: "queued",
      checkpointId
    }),
    createBranchEvent(2, "state.snapshot", branchAnalysisId, "thread_2", {
      checkpointId,
      stateVersion: 1,
      artifactIds: artifacts.map((artifact) => artifact.id),
      findingIds: findings.map((finding) => finding.id),
      approvalIds: approvals.map((approval) => approval.id),
      nextActions: ["检查分支检查点状态", "确认后启动新的分析运行"],
      sourceAnalysisId,
      reason
    })
  ];

  return {
    ...workbench,
    analysis: {
      ...workbench.analysis,
      id: branchAnalysisId,
      status: "queued",
      langgraphThreadId: "thread_2",
      langgraphRunId: null,
      updatedAt: decisionTimestamp
    },
    state: {
      checkpointId,
      stateVersion: 1,
      artifactIds: artifacts.map((artifact) => artifact.id),
      findingIds: findings.map((finding) => finding.id),
      approvalIds: approvals.map((approval) => approval.id),
      nextActions: ["检查分支检查点状态", "确认后启动新的分析运行"]
    },
    events,
    approvals,
    artifacts,
    findings,
    auditLogs: []
  };
}

function decideInterrupt(
  workbench: AuditWorkbench,
  interruptId: string,
  status: Extract<ApprovalStatus, "approved" | "rejected">,
  decisionReason: string
): AuditWorkbench {
  const approval = workbench.approvals.find((item) => item.interruptId === interruptId);
  if (approval === undefined) {
    return workbench;
  }
  const updatedApproval: ApprovalRequest = {
    ...approval,
    status,
    decidedAt: decisionTimestamp,
    decidedBy: "mock_analyst",
    decisionReason
  };
  const eventType: AuditEventType =
    status === "approved" ? "approval.approved" : "approval.rejected";
  const event = createEvent(nextSequence(workbench.events), eventType, "api", "approval_service", {
    approvalId: updatedApproval.id,
    interruptId: updatedApproval.interruptId,
    action: updatedApproval.action,
    status,
    riskSummary: updatedApproval.riskSummary,
    proposedParameters: updatedApproval.proposedParameters,
    decisionReason
  });
  const auditLog: AuditLog = {
    id: `audit_${workbench.auditLogs.length + 1}`,
    projectId: updatedApproval.projectId,
    analysisId: updatedApproval.analysisId,
    actorId: "mock_analyst",
    action: eventType,
    resourceType: "approval",
    resourceId: updatedApproval.id,
    outcome: "allowed",
    reason: decisionReason,
    createdAt: decisionTimestamp
  };
  return {
    ...workbench,
    approvals: workbench.approvals.map((item) =>
      item.interruptId === interruptId ? updatedApproval : item
    ),
    state: {
      ...workbench.state,
      stateVersion: workbench.state.stateVersion + 1
    },
    events: [...workbench.events, event],
    auditLogs: [...workbench.auditLogs, auditLog]
  };
}

function nextSequence(events: AuditEvent[]): number {
  return Math.max(0, ...events.map((event) => event.sequence)) + 1;
}

function createEvent(
  sequence: number,
  type: AuditEventType,
  agent: string | null,
  node: string | null,
  payload: Record<string, unknown>
): AuditEvent {
  return {
    id: `evt_${sequence}`,
    sequence,
    analysisId: "analysis_1",
    runId: "run_analysis_1",
    threadId: "thread_1",
    agent,
    node,
    type,
    payload,
    createdAt: baseTimestamp,
    traceId: "trace_mock_analysis_1"
  };
}

function createBranchEvent(
  sequence: number,
  type: AuditEventType,
  analysisId: string,
  threadId: string,
  payload: Record<string, unknown>
) {
  return {
    id: `evt_branch_${sequence}`,
    sequence,
    analysisId,
    runId: "",
    threadId,
    agent: type === "run.queued" ? "api" : null,
    node: type === "run.queued" ? "mock_branch" : "branch_from_checkpoint",
    type,
    payload,
    createdAt: decisionTimestamp,
    traceId: "trace_mock_analysis_2"
  };
}

function branchId(value: string, sourceAnalysisId: string, branchAnalysisId: string): string {
  return value.includes(sourceAnalysisId)
    ? value.replace(sourceAnalysisId, branchAnalysisId)
    : `${value}_branch_${branchAnalysisId}`;
}
