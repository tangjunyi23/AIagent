# 二进制审计平台 Decision Log

> Purpose: record architecture decisions, official documentation alignment, and reasons for deviations from local blueprints.

## 2026-04-24: Product APIs Wrap Native LangGraph APIs

- Decision: expose binary-audit business APIs under `/api/*` and keep native LangGraph `/assistants`, `/threads`, `/runs`, and `/mcp` behind the platform layer by default.
- Reason: the platform must enforce tenant/project isolation, RBAC, audit logging, approval gates, artifact authorization, and sensitive-data redaction.
- Official docs: LangGraph Platform and Agent Server provide assistants, threads, runs, streaming, and MCP integration capabilities, but product-specific authorization belongs in the application layer.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/langgraph-platform
  - https://docs.langchain.com/langsmith/server-mcp

## 2026-04-24: Use LangGraph Interrupts for Dangerous Action Gates

- Decision: dynamic execution, network enablement, exploit verification, firmware emulation, and sensitive artifact export require `ApprovalRequest` records and resume through interrupt approval endpoints.
- Reason: the platform safety boundary requires human-in-the-loop before dangerous or potentially policy-sensitive execution.
- Official docs: LangGraph interrupts support human review and resuming execution after external input.
- Links:
  - https://docs.langchain.com/oss/python/langgraph/interrupts

## 2026-04-24: SSE Event Envelope Is Product-Owned

- Decision: frontend uses `GET /api/analyses/{analysisId}/events` with product `AuditEvent` events, not raw provider-specific stream payloads.
- Reason: the UI needs stable event names across LangGraph runs, workers, artifacts, findings, and approvals; raw events are normalized by the business API.
- Official docs: LangGraph streaming supports streaming graph execution updates; this platform maps those updates into product timeline and artifact/finding events.
- Links:
  - https://docs.langchain.com/oss/python/langgraph/streaming

## 2026-04-24: State and Evidence Stay Structured

- Decision: agent outputs must update structured state, artifacts, findings, approvals, or reports. Token streams are UX hints only and cannot be the sole record of evidence.
- Reason: audit reports and high-risk findings need reproducible evidence chains and artifact references.
- Official docs: LangGraph state and persistence support durable state snapshots and recovery, which match the platform evidence-first workflow.
- Links:
  - https://docs.langchain.com/oss/python/langgraph/overview
  - https://docs.langchain.com/oss/python/langgraph/durable-execution
  - https://docs.langchain.com/oss/python/langgraph/persistence

## 2026-04-24: Prefer Product-Layer Extension Over Core LangGraph Changes

- Decision: initial implementation will create `apps/audit-*` and `libs/audit-common` rather than modifying LangGraph core scheduling semantics.
- Reason: the local backend blueprint says to avoid core changes unless required; official LangGraph primitives already cover state graphs, durable execution, streaming, subgraphs, and interrupts.
- Official docs:
  - https://docs.langchain.com/oss/python/langgraph/overview
  - https://docs.langchain.com/oss/python/langgraph/subgraphs
  - https://docs.langchain.com/oss/python/langgraph/multi-agent

## 2026-04-24: Python Shared Schemas Use Snake Case Keys

- Decision: `libs/audit-common` exposes Python `TypedDict` schemas with snake case keys, while `openapi-contract.md` keeps HTTP JSON examples in camel case where already drafted.
- Reason: Python agent, API, and worker code should follow idiomatic Python field naming; API serialization can map to the public JSON contract in `apps/audit-api`.
- Official docs: LangGraph state is application-defined Python data, so the platform can use Python-native state keys while normalizing external API payloads at the boundary.
- Links:
  - https://docs.langchain.com/oss/python/langgraph/overview
  - https://docs.langchain.com/oss/python/langgraph/persistence

## 2026-04-24: Start Agent Implementation With Approval Placeholders

- Decision: `apps/audit-agents` starts with a minimal supervisor graph skeleton and deterministic approval placeholder nodes before adding real sandbox, dynamic execution, or worker adapters.
- Reason: firmware emulation, dynamic execution, network enablement, and exploit verification are dangerous actions; the platform must prove approval state and event contracts before any tool can execute.
- Official docs: LangGraph state graphs are application-defined, Agent Server can expose graph runs and MCP integration later, and interrupts are the correct human gate for dangerous actions.
- Links:
  - https://docs.langchain.com/oss/python/langgraph/overview
  - https://docs.langchain.com/oss/python/langgraph/interrupts
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/server-mcp


## 2026-04-24: Mock Business API Owns JSON Boundary

- Decision: `apps/audit-api` starts as a stdlib in-memory mock service that accepts and returns public camelCase JSON dictionaries while storing internal resources with `audit-common` snake_case schema keys.
- Reason: frontend and agent development need a stable product API boundary before RBAC, persistence, object storage, and native Agent Server integration exist.
- Official docs: Agent Server and MCP capabilities are integration targets, but tenant isolation, artifact authorization, dangerous-action approval, and event normalization remain product-layer responsibilities.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/server-mcp
  - https://docs.langchain.com/langsmith/langgraph-platform
  - https://docs.langchain.com/oss/python/langgraph/streaming

## 2026-04-24: Mock HTTP Handler Extends Existing Business API Shell

- Decision: `AuditApiHandler` now dispatches mock `POST /api/projects`, `POST /api/samples:upload`, `POST /api/analyses`, and `GET /api/analyses/{analysisId}/events` to `AuditMockService` instead of introducing a second web framework or parallel API module.
- Reason: P1 needs route-level contract tests for frontend and agent integration while preserving the product API as the authorization/audit boundary. Real RBAC, persistence, multipart upload parsing, Agent Server run creation, and interrupt resume remain later work.
- Official docs: LangGraph/LangSmith Agent Server and MCP are integration targets behind the business API; LangGraph streaming output is normalized into product-owned SSE `AuditEvent` frames.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/langgraph-platform
  - https://docs.langchain.com/langsmith/server-mcp
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langgraph/interrupts

## 2026-04-24: Mock Approval Decisions Do Not Resume LangGraph Yet

- Decision: `apps/audit-api` now models approval list/approve/reject as in-memory `ApprovalRequest` transitions and product `approval.*` events, but it does not call native LangGraph `Command(resume=...)` or Agent Server run resume APIs yet.
- Reason: the platform needs stable frontend/API contracts and audit events before wiring real interrupt IDs, persistence, RBAC, and Agent Server resume behavior. This keeps dangerous action approval visible while preventing accidental dynamic execution.
- Official docs: LangGraph interrupts are the target human-in-the-loop primitive; MCP and Agent Server remain behind product authorization boundaries.
- Links:
  - https://docs.langchain.com/oss/python/langgraph/interrupts
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/langgraph-platform

## 2026-04-24: Mock API State Uses Audit Agent State Constructor

- Decision: `AuditMockService.create_analysis` now calls `apps/audit-agents.create_initial_state` and stores one in-memory `AuditAgentState` per analysis, exposed through `GET /api/analyses/{analysisId}/state` as public camelCase JSON.
- Reason: frontend and API development need a stable state snapshot contract while preserving `apps/audit-agents` ownership of agent state construction. The mock still avoids Agent Server runs, checkpoints, persistence, and dynamic execution.
- Official docs: LangGraph state is application-defined, while persistence/checkpoints and Agent Server threads/runs are later integration boundaries behind the product API.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/oss/python/langgraph/overview
  - https://docs.langchain.com/oss/python/langgraph/persistence
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/langsmith/langgraph-platform

## 2026-04-24: Mock Run Start Invokes Supervisor Skeleton Only

- Decision: `POST /api/analyses/{analysisId}/runs` now starts an in-memory mock run by assigning a deterministic run ID, invoking `build_supervisor_graph().invoke`, and normalizing resulting run/agent events into product `AuditEvent` SSE frames.
- Reason: the frontend needs a runnable analysis lifecycle before real Agent Server, persistence, and workers are integrated. The supervisor approval gate remains idempotent and dangerous firmware emulation stays blocked behind human approval.
- Official docs: LangGraph `StateGraph` invocation and streaming/state updates are the target runtime model; Agent Server threads/runs and MCP remain later integration surfaces behind product authorization.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/oss/python/langgraph/overview
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langgraph/interrupts
  - https://docs.langchain.com/langsmith/langgraph-platform

## 2026-04-24: Mock Resource Detail Routes Extend Business API

- Decision: `apps/audit-api` now serves mock project, sample, and analysis detail reads through `GET /api/projects/{projectId}`, `GET /api/samples/{sampleId}`, and `GET /api/analyses/{analysisId}` by extending `AuditMockService` and `AuditApiHandler`.
- Reason: frontend and agent work need stable resource detail endpoints before persistence, RBAC, object storage, and Agent Server integration exist. The implementation reuses in-memory product resources and does not create a parallel API module.
- Official docs: LangGraph/LangSmith Agent Server and MCP remain integration targets behind the business API; product resource authorization and audit boundaries stay in `apps/audit-api`.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/oss/python/langgraph/overview
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langgraph/interrupts
  - https://docs.langchain.com/langsmith/langgraph-platform

## 2026-04-24: Mock Resume Completes Without Dangerous Execution

- Decision: `POST /api/analyses/{analysisId}/runs:resume` now resumes only approved mock runs, emits `run.resumed` and `run.succeeded`, and completes the in-memory analysis without launching sandbox workers or dynamic tools.
- Reason: frontend and workflow development need a visible post-approval lifecycle, but real LangGraph interrupt resume, checkpoint persistence, RBAC, audit logging, and sandbox execution are not ready. The mock acknowledges approval while preserving the no-dangerous-execution boundary.
- Official docs: LangGraph interrupts and Agent Server run resume remain the target integration model; MCP stays behind product authorization and is not exposed as the business API.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/oss/python/langgraph/interrupts
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/langsmith/langgraph-platform

## 2026-04-24: Mock Artifact and Finding APIs Stay Product-Owned

- Decision: `GET /api/artifacts/{artifactId}`, `GET /api/findings?analysisId=...`, and `PATCH /api/findings/{findingId}` are implemented in the existing product API mock service instead of adding a parallel artifact/finding module or exposing Agent Server/MCP routes.
- Reason: frontend ArtifactViewer and FindingBoard work needs stable business contracts, but tenant authorization, RBAC, object storage, audit logging, and worker-produced artifacts are not ready. Deterministic in-memory resources exercise the API shape without pretending to execute tools.
- Official docs: LangGraph streaming/events, Agent Server, LangSmith tracing, and MCP remain later integration boundaries behind product authorization.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/langsmith/langgraph-platform

## 2026-04-25: Mock Reports Are Report Artifacts

- Decision: P11 implements `POST /api/reports` and `GET /api/reports/{reportId}` by creating and reading `report.*` `ArtifactRef` records in the existing `AuditMockService` artifact store.
- Reason: reports are already defined as artifact types in the backend and API contracts, and frontend report panels need metadata before content download, object storage, RBAC, and audit logging exist.
- Boundary: no separate report module, native Agent Server route, MCP tool, object storage, or `GET /api/reports/{reportId}/content` implementation is introduced in this round.
- Official docs: Agent Server provides assistants/threads/runs, persistence, task queues, and streaming lifecycle; MCP exposes deployed agents at `/mcp`, but product report resources remain behind `/api/*` authorization and audit boundaries.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/agent-server
  - https://docs.langchain.com/langsmith/server-mcp
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langgraph/interrupts

## 2026-04-25: Report Content Reads Require Audit Logs

- Decision: P12 implements `GET /api/reports/{reportId}/content` as a redacted mock content endpoint and records each read as an `AuditLog` with action `report.content.read`.
- Reason: report content is a sensitive artifact access path. Even in the mock API, content reads must pass through the product boundary and leave a structured audit trail before object storage, RBAC, and export approvals are added.
- Boundary: generic `GET /api/artifacts/{artifactId}/content`, object storage downloads, original sample export, PCAP export, decompiler project export, Agent Server routes, and MCP exposure remain out of scope.
- Official docs: LangGraph streaming and Agent Server/MCP remain integration targets behind the business API; durable state/events should be normalized by product APIs, while sensitive content access is represented by product audit records.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/agent-server
  - https://docs.langchain.com/langsmith/server-mcp
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langgraph/interrupts
  - https://docs.langchain.com/oss/python/langgraph/persistence

## 2026-04-25: Repeated Mock Reports Are Versioned Artifacts

- Decision: P13 keeps reports as `ArtifactRef` records and versions repeated `POST /api/reports` calls for the same analysis and format instead of overwriting the prior artifact.
- Reason: frontend report panels and later object storage need stable historical artifact IDs. Preserving the first ID keeps existing clients/tests compatible, while `_v{versionNumber}` IDs allow regeneration workflows.
- Boundary: no separate report workflow, Report Agent run, persistence layer, object storage, MCP route, or native Agent Server route is introduced.
- Official docs: Agent Server runs, persistence, and streaming remain later integration surfaces; synchronous mock report metadata updates stay in the product API until the report workflow becomes a real graph/run.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/agent-server
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langgraph/persistence

## 2026-04-25: Finding Queries Are Product API Envelopes

- Decision: P14 extends `GET /api/findings` in `AuditMockService` and `AuditApiHandler` with `analysisId` or `projectId` scoping, optional `status`/`severity` filters, and `limit`/`offset` pagination metadata.
- Reason: frontend FindingBoard list views need project-level browsing before persistence and RBAC exist, but the query must still pass through the business API boundary where tenant checks and audit controls will later live.
- Boundary: no separate finding service module, database query layer, Agent Server route, MCP route, new SSE event type, or worker-produced finding normalizer is introduced.
- Official docs: LangGraph streaming/state and Agent Server/MCP remain integration sources behind product APIs; durable finding records and list pagination stay product-owned.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/agent-server
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langgraph/persistence

## 2026-04-25: Artifact Content Preview Is Audited And Limited

- Decision: P15 implements `GET /api/artifacts/{artifactId}/content` only for safe mock evidence artifact previews, returning redacted content and recording `artifact.content.read` in `AuditLog`.
- Reason: frontend ArtifactViewer needs a content contract, but generic artifact export is a sensitive boundary. The mock should prove audit logging and redaction without opening raw samples, PCAPs, decompiler projects, rootfs exports, Agent Server routes, or MCP routes.
- Boundary: report artifacts keep using `GET /api/reports/{reportId}/content`; non-previewable artifacts return an approval-required error until export approval, object storage authorization, and redaction policy are implemented.
- Official docs: LangGraph streaming/state and persistence remain integration sources, while artifact content reads stay product-owned API operations with explicit audit records.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/agent-server
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langgraph/persistence
  - https://docs.langchain.com/oss/python/langgraph/interrupts

## 2026-04-25: Artifact Export Requires Approval Scaffolding

- Decision: P16 marks `artifact-export` as a dangerous approval action and adds `POST /api/artifacts/{artifactId}:request-export` to create or reuse a pending `ApprovalRequest`.
- Reason: artifact export can disclose samples, credentials, exploit evidence, or sensitive tool outputs. Export intent must be structured before any future object storage download or worker export path exists.
- Boundary: the new endpoint emits `approval.requested` and updates state only; it does not return artifact bytes, create signed URLs, call Agent Server, call MCP, resume LangGraph, or launch an export worker.
- Official docs: LangGraph interrupts are the later resume mechanism for approved human gates; product APIs still own authorization, audit, and artifact export policy.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/agent-server
  - https://docs.langchain.com/oss/python/langgraph/interrupts
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langgraph/persistence

## 2026-04-25: Mock API Storage Has A Repository Boundary

- Decision: P17 introduces `AuditRepository` and `InMemoryAuditRepository` in `apps/audit-api/audit_api/repository.py`, and `AuditMockService` now accepts an injected repository.
- Reason: API behavior, SSE events, approvals, artifacts, findings, reports, audit logs, and state snapshots need a stable storage boundary before replacing in-memory data with persistence and object storage.
- Boundary: no database, migrations, RBAC, object storage, native Agent Server client, MCP route, LangGraph checkpointer, or public HTTP/SSE contract change is introduced.
- Official docs: LangGraph persistence/checkpoints and Agent Server storage remain later integration targets; product records still flow through the business API authorization and audit boundary.
- Links:
  - https://docs.langchain.com/mcp
  - https://docs.langchain.com/langsmith/agent-server
  - https://docs.langchain.com/langsmith/server-mcp
  - https://docs.langchain.com/oss/python/langgraph/persistence
  - https://docs.langchain.com/oss/python/langgraph/streaming
