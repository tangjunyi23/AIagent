export type AnalysisStatus =
  | "queued"
  | "running"
  | "interrupted"
  | "succeeded"
  | "failed"
  | "cancelled";

export type ApprovalStatus = "pending" | "approved" | "rejected" | "expired" | "cancelled";

export type AuditEventType =
  | "run.queued"
  | "run.started"
  | "run.interrupted"
  | "run.resumed"
  | "run.succeeded"
  | "run.failed"
  | "run.cancelled"
  | "state.snapshot"
  | "agent.started"
  | "agent.heartbeat"
  | "agent.completed"
  | "agent.failed"
  | "token.delta"
  | "tool.queued"
  | "tool.started"
  | "tool.output_chunk"
  | "tool.completed"
  | "tool.failed"
  | "tool.cancelled"
  | "artifact.created"
  | "finding.created"
  | "finding.updated"
  | "approval.requested"
  | "approval.approved"
  | "approval.rejected"
  | "policy.denied"
  | "error.created";

export type Severity = "info" | "low" | "medium" | "high" | "critical";

export type FindingStatus =
  | "draft"
  | "needs-review"
  | "confirmed"
  | "false-positive"
  | "accepted-risk"
  | "fixed";

export type Analysis = {
  id: string;
  projectId: string;
  sampleIds: string[];
  scenario: "ctf" | "risk" | "malware" | "firmware" | "code-audit" | "mobile";
  status: AnalysisStatus;
  langgraphThreadId: string;
  langgraphRunId: string | null;
  updatedAt: string;
};

export type AuditEvent = {
  id: string;
  sequence: number;
  analysisId: string;
  runId: string;
  threadId: string | null;
  node: string | null;
  agent: string | null;
  type: AuditEventType;
  payload: Record<string, unknown>;
  createdAt: string;
  traceId: string | null;
};

export type ApprovalRequest = {
  id: string;
  analysisId: string;
  projectId: string;
  interruptId: string;
  action:
    | "dynamic-execution"
    | "network-enable"
    | "exploit-verification"
    | "firmware-emulation"
    | "artifact-export";
  status: ApprovalStatus;
  requestedByAgent: string;
  reason: string;
  riskSummary: string;
  proposedParameters: Record<string, unknown>;
  createdAt: string;
  decidedAt: string | null;
  decidedBy: string | null;
  decisionReason: string | null;
};

export type ArtifactRef = {
  id: string;
  analysisId: string;
  projectId: string;
  type: string;
  name: string;
  mediaType: string;
  size: number;
  uri: string;
  createdAt: string;
  preview: string;
  redacted: boolean;
};

export type Finding = {
  id: string;
  analysisId: string;
  projectId: string;
  title: string;
  description: string;
  severity: Severity;
  confidence: number;
  status: FindingStatus;
  cwe: string | null;
  cve: string | null;
  affectedComponent: string | null;
  evidenceArtifactIds: string[];
};

export type AuditLog = {
  id: string;
  projectId: string;
  analysisId: string | null;
  actorId: string;
  action: string;
  resourceType: string;
  resourceId: string;
  outcome: "allowed" | "denied";
  reason: string | null;
  createdAt: string;
};

export type ReportArtifact = {
  id: string;
  type: "report.markdown" | "report.html" | "report.pdf";
  name: string;
  versionNumber: number;
  latest: boolean;
  redacted: boolean;
};

export type WorkbenchState = {
  checkpointId: string;
  stateVersion: number;
  artifactIds: string[];
  findingIds: string[];
  approvalIds: string[];
  nextActions: string[];
};

export type AuditWorkbench = {
  analysis: Analysis;
  state: WorkbenchState;
  events: AuditEvent[];
  approvals: ApprovalRequest[];
  artifacts: ArtifactRef[];
  findings: Finding[];
  reports: ReportArtifact[];
  auditLogs: AuditLog[];
};
