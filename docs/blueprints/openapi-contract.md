# 二进制审计平台 OpenAPI Contract

> Status: M0 draft. This document freezes the first business API surface for `apps/audit-api` and frontend mock development. Native LangGraph Agent Server endpoints remain behind the business API unless a debug-only route explicitly opts in.

## 1. Contract Principles

- Business APIs own tenant isolation, RBAC, audit logs, artifact authorization, and dangerous-action approval.
- LangGraph `/assistants`, `/threads`, `/runs`, and `/mcp` capabilities are integration targets, not directly exposed product APIs.
- Every high-risk action must create an `ApprovalRequest` and must be resumable through LangGraph interrupt semantics.
- Every high-confidence or high-severity `Finding` must reference at least one evidence `ArtifactRef`.
- Large logs, files, PCAPs, decompiler projects, Flag results, teaching PoCs, IoC reports, YARA rules, and reports are stored as artifacts or structured results; events carry references, not bulk payloads.

## 2. Resource Model

### 2.1 Common Enums

```yaml
Classification: [public, internal, confidential, restricted]
SampleFormat: [ELF, PE, MachO, APK, Firmware, Archive, Unknown]
Scenario: [ctf, risk, malware, firmware, code-audit, mobile]
AnalysisStatus: [queued, running, interrupted, succeeded, failed, cancelled]
RunStatus: [queued, running, interrupted, succeeded, failed, cancelled]
Severity: [info, low, medium, high, critical]
FindingStatus: [draft, needs-review, confirmed, false-positive, accepted-risk, fixed]
ApprovalStatus: [pending, approved, rejected, expired, cancelled]
ToolExecutionStatus: [queued, running, succeeded, failed, timed-out, cancelled, blocked]
NetworkPolicy: [none, allowlist, unrestricted]
SimulationMode: [skip, component, qemu-system, emba]
```

### 2.2 Project

```yaml
Project:
  id: string
  tenantId: string
  name: string
  classification: Classification
  createdAt: string
  updatedAt: string
```

### 2.3 Sample

```yaml
Sample:
  id: string
  projectId: string
  filename: string
  sha256: string
  size: integer
  format: SampleFormat
  arch: string | null
  mimeType: string | null
  magic: string | null
  uploadedAt: string
  artifactId: string
```

### 2.4 AuditPolicy

```yaml
AuditPolicy:
  allowDynamicExecution: boolean
  allowNetwork: boolean
  networkPolicy: NetworkPolicy
  networkAllowlist: string[]
  allowExploitVerification: boolean
  requireApprovalForDynamic: boolean
  requireApprovalForNetwork: boolean
  requireApprovalForExploit: boolean
  maxToolRuntimeSeconds: integer
  maxAgentRuntimeSeconds: integer
  maxCpuCores: number
  maxMemoryMb: integer
  secretRedaction: boolean
```

### 2.5 Analysis

```yaml
Analysis:
  id: string
  projectId: string
  sampleIds: string[]
  scenario: Scenario
  status: AnalysisStatus
  policy: AuditPolicy
  langgraphThreadId: string
  langgraphRunId: string | null
  createdAt: string
  updatedAt: string
```

### 2.6 ArtifactRef

```yaml
ArtifactRef:
  id: string
  analysisId: string
  projectId: string
  type: string
  name: string
  mediaType: string
  size: integer
  sha256: string | null
  uri: string
  producer:
    agent: string | null
    node: string | null
    toolExecutionId: string | null
  metadata: object
  createdAt: string
```

Initial artifact types:

```text
sample.original
sample.extracted
static.objdump
static.readelf
static.nm
static.strings
static.ghidra.project
static.ghidra.decompile
static.idat.export
static.jadx.project
static.joern.cpg
firmware.binwalk.tree
firmware.unblob.tree
firmware.emba.report
firmware.rootfs
firmware.qemu.snapshot
dynamic.pcap
dynamic.http_archive
dynamic.command_output
ctf.flag_result
exploit.teaching_poc
threat.ioc_report
threat.yara_rule
threat.behavior_chain
code.audit_summary
vuln.finding_evidence
report.markdown
report.html
report.pdf
```

### 2.7 Finding

```yaml
Finding:
  id: string
  analysisId: string
  projectId: string
  title: string
  description: string
  severity: Severity
  confidence: number
  status: FindingStatus
  cwe: string | null
  cve: string | null
  affectedComponent: string | null
  evidenceArtifactIds: string[]
  verification:
    status: pending | approved | blocked | verified | failed | skipped
    approvalId: string | null
    notes: string | null
  createdAt: string
  updatedAt: string
```

### 2.8 ToolExecution

```yaml
ToolExecution:
  id: string
  analysisId: string
  projectId: string
  tool: string
  adapter: string
  status: ToolExecutionStatus
  inputArtifactIds: string[]
  outputArtifactIds: string[]
  sanitizedArgs: object
  approvalId: string | null
  startedAt: string | null
  finishedAt: string | null
  exitCode: integer | null
  limits:
    wallTimeSeconds: integer
    cpuCores: number
    memoryMb: integer
    diskMb: integer
    networkPolicy: NetworkPolicy
  error: string | null
```

### 2.9 ApprovalRequest

```yaml
ApprovalRequest:
  id: string
  analysisId: string
  projectId: string
  interruptId: string
  action: dynamic-execution | network-enable | exploit-verification | firmware-emulation | artifact-export
  status: ApprovalStatus
  requestedByAgent: string
  reason: string
  riskSummary: string
  proposedParameters: object
  createdAt: string
  decidedAt: string | null
  decidedBy: string | null
  decisionReason: string | null
```

### 2.10 AuditLog

```yaml
AuditLog:
  id: string
  tenantId: string
  projectId: string
  analysisId: string | null
  actorId: string
  action: string
  resourceType: string
  resourceId: string
  outcome: allowed | denied
  reason: string | null
  metadata: object
  createdAt: string
```

Mock actions currently include `report.content.read`, `artifact.content.read`, `approval.approved`, and `approval.rejected`. Future production actions will cover sensitive artifact downloads, policy denials, analyst finding updates, and administrative changes.

### 2.11 StructuredResult

```yaml
StructuredResult:
  id: string
  analysisId: string
  projectId: string
  kind: flag-result | teaching-poc | ioc-report | yara-rule | vulnerability-finding | sbom | audit-summary
  status: draft | needs-review | verified | rejected
  title: string
  artifactIds: string[]
  findingIds: string[]
  confidence: number
  safetyNotes: string[]
  createdAt: string
  updatedAt: string
```

`StructuredResult` is the product-owned view model for outputs such as CTF Flag extraction, teaching PoC generation, IoC threat intelligence reports, YARA rules, SBOM summaries, and code-audit summaries. Content remains in artifacts; this resource keeps relationships, confidence, review status, and safety/export notes queryable.

## 3. API Endpoints

### 3.1 Projects

```http
POST /api/projects
GET /api/projects
GET /api/projects/{projectId}
```

`POST /api/projects` request:

```json
{
  "name": "router-firmware-audit",
  "classification": "confidential"
}
```

### 3.2 Samples

```http
POST /api/samples:upload
GET /api/samples/{sampleId}
```

`POST /api/samples:upload` accepts `multipart/form-data`:

- `projectId`: string
- `file`: binary
- `sourceLabel`: optional string
- `archivePassword`: optional string, stored only in secret-managed transient form

Response includes `Sample` plus pre-identification metadata.

### 3.3 Analyses and Runs

```http
POST /api/analyses
GET /api/analyses/{analysisId}
POST /api/analyses/{analysisId}/runs
POST /api/analyses/{analysisId}/runs:resume
GET /api/analyses/{analysisId}/events
GET /api/analyses/{analysisId}/state
POST /api/analyses/{analysisId}:cancel
POST /api/analyses/{analysisId}:branch
```

`POST /api/analyses` request:

```json
{
  "projectId": "proj_123",
  "sampleIds": ["sample_123"],
  "scenario": "firmware",
  "depth": "standard",
  "simulationMode": "component",
  "policy": {
    "allowDynamicExecution": false,
    "allowNetwork": false,
    "networkPolicy": "none",
    "networkAllowlist": [],
    "allowExploitVerification": false,
    "requireApprovalForDynamic": true,
    "requireApprovalForNetwork": true,
    "requireApprovalForExploit": true,
    "maxToolRuntimeSeconds": 1800,
    "maxAgentRuntimeSeconds": 600,
    "maxCpuCores": 2,
    "maxMemoryMb": 4096,
    "secretRedaction": true
  }
}
```

`GET /api/analyses/{analysisId}/events` is an SSE endpoint. It supports:

- `Last-Event-ID` header for replay.
- `?agent=` filter.
- `?node=` filter.
- `?severity=` filter for finding events.
- `?afterSequence=` filter for explicit replay.

### 3.4 Interrupts and Approvals

```http
GET /api/analyses/{analysisId}/interrupts
POST /api/analyses/{analysisId}/interrupts/{interruptId}:approve
POST /api/analyses/{analysisId}/interrupts/{interruptId}:reject
```

Approval request body:

```json
{
  "decisionReason": "Approved for isolated QEMU component emulation with no external network.",
  "parameterOverrides": {
    "networkPolicy": "none",
    "maxToolRuntimeSeconds": 900
  }
}
```

Mock implementation note: the in-memory API currently returns a deterministic pending `firmware-emulation` `ApprovalRequest` for each created analysis. Approve/reject routes update that request, append `approval.approved` or `approval.rejected` SSE events, and record an `AuditLog`, but do not yet resume a real LangGraph interrupt.

`GET /api/analyses/{analysisId}/state` mock response returns the latest public camelCase projection of the in-memory `AuditAgentState` created from `apps/audit-agents.create_initial_state`. The snapshot currently includes `analysis`, `artifacts`, `findings`, `toolExecutions`, `approvalRequests`, and `events`.

`POST /api/analyses/{analysisId}/runs` mock response returns the updated `Analysis`. It assigns a deterministic mock `langgraphRunId`, invokes the supervisor skeleton, emits `run.started`, `agent.started`, and `run.interrupted`, and keeps dangerous execution blocked behind the existing approval request. It does not call Agent Server or execute tools.

`POST /api/analyses/{analysisId}/runs:resume` mock response returns the updated `Analysis`. It requires an existing mock run and an approved `firmware-emulation` approval, emits `run.resumed` and `run.succeeded`, and completes the mock run without calling Agent Server, LangGraph `Command(resume=...)`, MCP, sandbox workers, or dangerous tools.

`POST /api/analyses/{analysisId}:cancel` mock response returns the updated `Analysis`. It marks queued, running, or interrupted mock analyses as `cancelled`, emits `run.cancelled`, synchronizes the state snapshot, and does not call Agent Server, MCP, sandbox workers, or dangerous tools.

`POST /api/analyses/{analysisId}:branch` mock response returns the newly created `Analysis`. It copies the source mock state snapshot into a new business analysis and new LangGraph thread lineage, emits `run.queued` plus `state.snapshot` only on the branch analysis, and leaves source analysis events unchanged. It does not call Agent Server checkpoint APIs, LangGraph time travel, MCP, workers, object storage, or dynamic tools.

`POST /api/analyses/{analysisId}:branch` request:

```json
{
  "checkpointId": "checkpoint_analysis_1_interrupt",
  "reason": "Compare alternate static-only path."
}
```

P21 mock status: branch artifacts, findings, approvals, and evidence links are copied with the new `analysisId`. `state.snapshot.payload.sourceAnalysisId` and `state.snapshot.payload.checkpointId` preserve branch lineage until real checkpoint-backed persistence is added.

Reject request body:

```json
{
  "decisionReason": "Exploit verification is outside the current authorization scope."
}
```

### 3.5 Tool Executions

```http
GET /api/tool-executions/{toolExecutionId}
POST /api/tool-executions/{toolExecutionId}:cancel
```

Tool execution creation is internal to agents/workers. User-facing clients can view and cancel authorized executions only.

### 3.6 Artifacts

```http
GET /api/artifacts/{artifactId}
GET /api/artifacts/{artifactId}/content
POST /api/artifacts/{artifactId}:request-export
```

P10 mock status: `GET /api/artifacts/{artifactId}` is implemented for in-memory metadata only.

P15 mock status: `GET /api/artifacts/{artifactId}/content` returns a redacted preview envelope for safe mock evidence artifacts only and records an `AuditLog` entry with action `artifact.content.read`. Report artifacts continue to use `GET /api/reports/{reportId}/content`. Original samples, PCAPs, decompiler projects, rootfs exports, credential-like artifacts, object storage downloads, Agent Server routes, and MCP exposure remain out of scope.

P16 mock status: `POST /api/artifacts/{artifactId}:request-export` creates or reuses a pending `ApprovalRequest` with action `artifact-export` and emits `approval.requested`. It does not return artifact bytes, produce signed URLs, call object storage, resume LangGraph, or expose MCP/Agent Server routes.

Artifact access must validate tenant, project, analysis, and user permission. Downloading original samples, PCAPs, decompiler projects, reports, or credential-like artifacts must create an audit log entry.

`GET /api/artifacts/{artifactId}/content` mock response:

```json
{
  "artifactId": "artifact_analysis_123_evidence",
  "analysisId": "analysis_123",
  "projectId": "project_123",
  "mediaType": "application/json",
  "filename": "mock-static-evidence.json",
  "encoding": "utf-8",
  "redacted": true,
  "auditLogId": "audit_1",
  "content": "{\"artifactId\":\"artifact_analysis_123_evidence\",\"artifactType\":\"vuln.finding_evidence\",\"redacted\":true,\"summary\":\"...\",\"title\":\"Mock artifact preview\"}"
}
```

`POST /api/artifacts/{artifactId}:request-export` request:

```json
{
  "reason": "Need offline evidence package for peer review."
}
```

Response is an `ApprovalRequest`:

```json
{
  "id": "approval_artifact_analysis_123_evidence_artifact_export",
  "analysisId": "analysis_123",
  "projectId": "project_123",
  "interruptId": "interrupt_artifact_analysis_123_evidence_artifact_export",
  "action": "artifact-export",
  "status": "pending",
  "requestedByAgent": "artifact_service",
  "reason": "Need offline evidence package for peer review.",
  "riskSummary": "Artifact export may disclose samples, credentials, exploit evidence, or other sensitive analysis outputs.",
  "proposedParameters": {
    "artifactId": "artifact_analysis_123_evidence",
    "artifactType": "vuln.finding_evidence",
    "mediaType": "application/json",
    "filename": "mock-static-evidence.json",
    "previewOnly": false
  },
  "createdAt": "2026-04-24T00:00:00Z",
  "decidedAt": null,
  "decidedBy": null,
  "decisionReason": null
}
```

### 3.7 Findings

```http
GET /api/findings?analysisId={analysisId}&projectId={projectId}&status={status}&severity={severity}&limit=50&offset=0
PATCH /api/findings/{findingId}
```

P10 mock status: `GET /api/findings?analysisId={analysisId}` and `PATCH /api/findings/{findingId}` are implemented against in-memory findings. Patching currently supports `status`, `severity`, and `description`, emits `finding.updated`, and synchronizes the mock state snapshot.

P14 mock status: `GET /api/findings` returns a paginated envelope and supports `analysisId`, `projectId`, `status`, `severity`, `limit`, and `offset`. At least one of `analysisId` or `projectId` is required for the mock query path.

`GET /api/findings` response:

```json
{
  "items": [
    {
      "id": "finding_analysis_123_static_strings",
      "analysisId": "analysis_123",
      "projectId": "project_123",
      "title": "Mock suspicious firmware string",
      "severity": "high",
      "confidence": 0.55,
      "status": "needs-review",
      "evidenceArtifactIds": ["artifact_analysis_123_evidence"]
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 50,
    "offset": 0,
    "nextOffset": null
  }
}
```

`PATCH /api/findings/{findingId}` request:

```json
{
  "status": "confirmed",
  "severity": "high",
  "analystNote": "Confirmed via static evidence. Dynamic verification intentionally skipped."
}
```

### 3.8 Structured Results

```http
GET /api/results?analysisId={analysisId}&kind={kind}&status={status}
```

This planned endpoint returns product-owned structured outputs for CTF, malware, code-audit, mobile, firmware, and risk workflows. It does not embed large content; clients fetch linked artifacts through artifact endpoints.

`GET /api/results` response:

```json
{
  "items": [
    {
      "id": "result_analysis_123_flag",
      "analysisId": "analysis_123",
      "projectId": "project_123",
      "kind": "flag-result",
      "status": "verified",
      "title": "Local CTF flag extraction",
      "artifactIds": ["artifact_analysis_123_flag_log"],
      "findingIds": [],
      "confidence": 0.98,
      "safetyNotes": ["authorized-local-target"],
      "createdAt": "2026-04-25T00:00:00Z",
      "updatedAt": "2026-04-25T00:00:00Z"
    }
  ]
}
```

P23 blueprint status: `GET /api/results` is reserved for future implementation. Until then, Flag results, teaching PoCs, IoC reports, YARA rules, and code-audit summaries remain represented as artifact types plus report sections.

### 3.9 Reports

```http
POST /api/reports
GET /api/reports/{reportId}
GET /api/reports/{reportId}/content
```

`POST /api/reports` request:

```json
{
  "analysisId": "analysis_123",
  "format": "markdown",
  "includeUnverifiedFindings": true,
  "redactionProfile": "default"
}
```

P11 mock status: `POST /api/reports` and `GET /api/reports/{reportId}` are implemented as in-memory report artifacts. Supported mock formats are `markdown`, `html`, and `pdf`; the response is an `ArtifactRef` with `type` set to `report.markdown`, `report.html`, or `report.pdf`. The mock emits `artifact.created` and updates `GET /api/analyses/{analysisId}/state`.

P13 mock status: repeated `POST /api/reports` calls for the same `analysisId` and `format` create versioned report artifacts instead of overwriting older artifacts. The first report keeps the compatibility ID `report_{analysisId}_{format}`; later reports use `report_{analysisId}_{format}_v{versionNumber}`. Report artifact metadata includes `versionNumber`, `previousReportId`, `latest`, and `supersededByReportId`.

P12 mock status: `GET /api/reports/{reportId}/content` returns a redacted mock content envelope for report artifacts only and records an `AuditLog` entry with action `report.content.read`. It does not read object storage, return original samples, expose PCAPs, expose decompiler projects, stream bulk tool output, call Agent Server, or expose MCP.

`GET /api/reports/{reportId}/content` response:

```json
{
  "reportId": "report_analysis_123_markdown",
  "artifactId": "report_analysis_123_markdown",
  "analysisId": "analysis_123",
  "projectId": "project_123",
  "mediaType": "text/markdown",
  "filename": "analysis_123-audit-report-v1.md",
  "encoding": "utf-8",
  "redacted": true,
  "auditLogId": "audit_1",
  "content": "# Mock Binary Audit Report\n\n..."
}
```

### 3.10 Audit Logs

```http
GET /api/audit-logs?analysisId={analysisId}
```

P12 mock status: `GET /api/audit-logs?analysisId={analysisId}` returns in-memory `AuditLog` records for the analysis. The mock records report content reads so frontend and later RBAC work can verify that sensitive content access has a structured audit trail.

P18 mock status: approval approve/reject decisions also create `AuditLog` records with actions `approval.approved` and `approval.rejected`, resource type `approval`, and metadata containing the interrupt ID and approval action.

### 3.11 Mock API Implementation Notes

The first `apps/audit-api` implementation is an in-memory mock for parallel frontend and agent development:

- Public service methods accept and return camelCase dictionaries matching this contract.
- Internal resources are stored with Python snake_case keys matching `libs/audit-common`.
- P17 mock status: `AuditMockService` stores resources through an injected `AuditRepository` boundary. The current implementation uses `InMemoryAuditRepository`; persistence, object storage, RBAC, Agent Server clients, MCP routes, and LangGraph checkpointer integration remain deferred.
- `POST /api/projects`, `GET /api/projects/{projectId}`, `POST /api/samples:upload`, `GET /api/samples/{sampleId}`, `POST /api/analyses`, `GET /api/analyses/{analysisId}`, `POST /api/analyses/{analysisId}/runs`, `POST /api/analyses/{analysisId}/runs:resume`, `POST /api/analyses/{analysisId}:cancel`, `GET /api/analyses/{analysisId}/state`, `GET /api/analyses/{analysisId}/events`, `GET /api/analyses/{analysisId}/interrupts`, `POST /api/analyses/{analysisId}/interrupts/{interruptId}:approve`, `POST /api/analyses/{analysisId}/interrupts/{interruptId}:reject`, `GET /api/artifacts/{artifactId}`, `GET /api/artifacts/{artifactId}/content`, `POST /api/artifacts/{artifactId}:request-export`, `GET /api/findings`, `PATCH /api/findings/{findingId}`, `POST /api/reports`, `GET /api/reports/{reportId}`, `GET /api/reports/{reportId}/content`, and `GET /api/audit-logs` have mock HTTP handler coverage. `GET /api/results` is reserved but not implemented in the mock handler yet.
- Mock `POST /api/samples:upload` accepts JSON sample metadata for frontend and agent parallel development; production multipart upload parsing remains deferred.
- SSE formatting is represented by `format_sse_event`; authentication, RBAC, persistent storage, native Agent Server run creation, and MCP exposure are intentionally deferred.
- P20 frontend status: `apps/audit-web` currently mirrors this API contract with local typed mock data in `src/lib/workbenchData.ts`. It renders analysis lifecycle, interrupts, artifact preview, findings, report metadata, and audit logs without requiring the Python mock API to run. The frontend must continue to call product `/api/*` routes when live API integration is added; it must not call Agent Server or MCP routes directly.
- P22 frontend status: the visible Audit Web copy is Chinese and branded as `思而听二进制漏洞审计平台`. This is a presentation-only change over the same typed mock data and does not add or rename OpenAPI resources, fields, or routes.

## 4. Error Envelope

All non-2xx responses use this shape:

```json
{
  "error": {
    "code": "approval_required",
    "message": "Dynamic execution requires human approval.",
    "requestId": "req_123",
    "details": {
      "approvalId": "approval_123"
    }
  }
}
```

Initial error codes:

```text
bad_request
unauthorized
forbidden
not_found
conflict
approval_required
policy_denied
tool_unavailable
quota_exceeded
validation_failed
internal_error
```

## 5. LangGraph Mapping

- `POST /api/analyses` creates business metadata and prepares a LangGraph thread.
- `POST /api/analyses/{analysisId}/runs` starts a LangGraph run for the selected assistant/graph.
- `GET /api/analyses/{analysisId}/events` merges LangGraph stream events, worker events, artifact events, approval events, and finding events into the SSE contract.
- Approval endpoints resume the interrupted run only after policy validation and audit logging.
- Branching copies the selected state snapshot into a new business `Analysis` and a new LangGraph thread/run lineage.
- `apps/audit-agents` owns the first Python `AuditAgentState` shape and maps `Analysis`, `ApprovalRequest`, and `AuditEvent` records from `libs/audit-common` into graph node updates.
- Until sandbox workers exist, dangerous-action graph nodes create `ApprovalRequest` placeholders and `approval.requested` events instead of launching tools.

## 6. Open Questions

- Decide whether `depth` should be an enum in `Analysis` or a profile resolved server-side.
- Decide whether report generation is an analysis sub-run or a separate report workflow.
- Decide storage URI format after object storage implementation is selected.
