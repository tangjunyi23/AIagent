# 二进制审计平台 SSE Event Schema

> Status: M0 draft. This document freezes the first event envelope for frontend timeline, agent DAG, artifact viewer, human gate, finding board, and report builder development.

## 1. Stream Contract

Endpoint:

```http
GET /api/analyses/{analysisId}/events
```

Transport:

- Server-Sent Events is the default run event stream.
- `id` is set to the numeric `sequence` as a string.
- `event` is set to the event `type`.
- `data` is a JSON object matching the envelope below.
- Clients resume with `Last-Event-ID` or `?afterSequence=`.

SSE frame example:

```text
id: 42
event: artifact.created
data: {"id":"evt_42","sequence":42,"analysisId":"analysis_123","runId":"run_123","type":"artifact.created","createdAt":"2026-04-24T16:00:00Z","node":"reverse_static","agent":"reverse","payload":{"artifactId":"artifact_123","artifactType":"static.objdump","name":"objdump.txt"}}
```

## 2. Event Envelope

```yaml
AuditEvent:
  id: string
  sequence: integer
  analysisId: string
  runId: string
  threadId: string | null
  node: string | null
  agent: string | null
  type: AuditEventType
  payload: object
  createdAt: string
  traceId: string | null
```

Rules:

- `sequence` is strictly increasing per analysis.
- `createdAt` is UTC ISO 8601.
- `payload` must be schema-validated before emission.
- Bulk data is stored as artifacts or log chunks and referenced by ID.
- Sensitive values are redacted before the event is persisted or streamed.

## 3. Event Types

```yaml
AuditEventType:
  - run.queued
  - run.started
  - run.interrupted
  - run.resumed
  - run.succeeded
  - run.failed
  - run.cancelled
  - state.snapshot
  - agent.started
  - agent.heartbeat
  - agent.completed
  - agent.failed
  - token.delta
  - tool.queued
  - tool.started
  - tool.output_chunk
  - tool.completed
  - tool.failed
  - tool.cancelled
  - artifact.created
  - finding.created
  - finding.updated
  - approval.requested
  - approval.approved
  - approval.rejected
  - policy.denied
  - error.created
```

## 4. Payload Schemas

### 4.1 Run Events

```yaml
RunPayload:
  status: queued | running | interrupted | succeeded | failed | cancelled
  message: string | null
  checkpointId: string | null
```

Used by `run.queued`, `run.started`, `run.interrupted`, `run.resumed`, `run.succeeded`, `run.failed`, and `run.cancelled`.

### 4.2 State Snapshot

```yaml
StateSnapshotPayload:
  checkpointId: string
  stateVersion: integer
  artifactIds: string[]
  findingIds: string[]
  approvalIds: string[]
  nextActions: string[]
```

State snapshots are summary events. The full state is fetched from `GET /api/analyses/{analysisId}/state`.

### 4.3 Agent Events

```yaml
AgentPayload:
  status: started | heartbeat | completed | failed
  message: string | null
  progress:
    currentStep: string | null
    percent: number | null
  error: string | null
```

Used by `agent.started`, `agent.heartbeat`, `agent.completed`, and `agent.failed`.

### 4.4 Token Delta

```yaml
TokenDeltaPayload:
  channel: reasoning | summary | report
  text: string
  redacted: boolean
```

Token deltas are optional UX hints. Durable conclusions must still be written as artifacts, findings, approvals, or state updates.

### 4.5 Tool Events

```yaml
ToolPayload:
  toolExecutionId: string
  tool: string
  status: queued | running | succeeded | failed | timed-out | cancelled | blocked
  message: string | null
  outputArtifactId: string | null
  logArtifactId: string | null
  exitCode: integer | null
  error: string | null
```

Used by `tool.queued`, `tool.started`, `tool.completed`, `tool.failed`, and `tool.cancelled`.

### 4.6 Tool Output Chunk

```yaml
ToolOutputChunkPayload:
  toolExecutionId: string
  stream: stdout | stderr | log
  chunkId: string
  text: string
  redacted: boolean
  artifactId: string | null
```

Chunks are size-limited and may be omitted entirely when output is too large; in that case the event points to a log artifact.

### 4.7 Artifact Created

```yaml
ArtifactCreatedPayload:
  artifactId: string
  artifactType: string
  name: string
  mediaType: string
  size: integer
  sha256: string | null
  toolExecutionId: string | null
```

P11 mock status: `POST /api/reports` emits `artifact.created` for report artifacts. The payload references report metadata only; content download remains outside the mock event payload.

### 4.8 Finding Events

```yaml
FindingPayload:
  findingId: string
  title: string
  severity: info | low | medium | high | critical
  confidence: number
  status: draft | needs-review | confirmed | false-positive | accepted-risk | fixed
  evidenceArtifactIds: string[]
```

Used by `finding.created` and `finding.updated`.

P10 mock status: `PATCH /api/findings/{findingId}` emits `finding.updated` with the finding ID, title, severity, confidence, status, and evidence artifact IDs. Worker-produced `finding.created` remains draft until real normalizers/verifiers exist.

### 4.9 Approval Events

```yaml
ApprovalPayload:
  approvalId: string
  interruptId: string
  action: dynamic-execution | network-enable | exploit-verification | firmware-emulation | artifact-export
  status: pending | approved | rejected | expired | cancelled
  riskSummary: string
  proposedParameters: object
  decisionReason: string | null
```

Used by `approval.requested`, `approval.approved`, and `approval.rejected`.

### 4.10 Policy Denied

```yaml
PolicyDeniedPayload:
  policyRule: string
  action: string
  reason: string
  approvalPossible: boolean
```

### 4.11 Error Created

```yaml
ErrorPayload:
  code: string
  message: string
  retryable: boolean
  details: object
```

## 5. Frontend Mapping

- `AnalysisTimeline`: consumes every event ordered by `sequence`.
- `AgentGraphViewer`: consumes `agent.*`, `tool.*`, `run.*`, and `state.snapshot`.
- `HumanGateCard`: consumes `approval.requested`, `approval.approved`, and `approval.rejected`.
- `ArtifactViewer`: refreshes on `artifact.created`.
- `FindingBoard`: refreshes on `finding.created` and `finding.updated`.
- `ToolConsole`: consumes `tool.output_chunk` and falls back to log artifacts.

## 6. LangGraph Mapping

- LangGraph stream state updates are normalized into `state.snapshot`, `agent.*`, and `token.delta` events.
- LangGraph interrupts are normalized into `run.interrupted` plus `approval.requested` when the interruption represents a dangerous action gate.
- Worker lifecycle updates are normalized into `tool.*` events.
- Artifact and finding writes are normalized into `artifact.created` and `finding.*` events.
