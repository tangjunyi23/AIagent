# 二进制审计平台 Feature Registry

> Purpose: prevent duplicate development by recording implemented or frozen platform features, entry files, schema names, API names, and event names.

## 1. Registry Rules

- Before adding a module, route, schema, adapter, event, or artifact type, search this registry and the repository with `rg`.
- Prefer extending an existing registered feature over creating a parallel module.
- Every new implementation must update this file with entry path, owner layer, and public names.
- Draft contracts count as reserved names even before implementation exists.

## 2. Reserved Product Directories

| Layer | Path | Status | Purpose |
| --- | --- | --- | --- |
| Web | `apps/audit-web/` | planned | React/Next.js frontend workbench |
| API | `apps/audit-api/` | implemented mock | Business API, RBAC, tenants, samples, analyses, artifacts, findings, reports |
| Agents | `apps/audit-agents/` | implemented skeleton | LangGraph state, graphs, subgraphs, supervisor, routers, prompts |
| Workers | `apps/audit-workers/` | planned | Tool execution, sandbox adapters, MCP tool servers, normalizers |
| Common | `libs/audit-common/` | implemented | Shared schemas, event types, artifact types, policy models |

## 3. Frozen Contract Documents

| Feature | Entry File | Status | Public Names |
| --- | --- | --- | --- |
| Business API draft | `docs/blueprints/openapi-contract.md` | draft | `Project`, `Sample`, `Analysis`, `ArtifactRef`, `Finding`, `ToolExecution`, `ApprovalRequest`, `AuditPolicy`, `AuditLog` |
| SSE event draft | `docs/blueprints/event-schema.md` | draft | `AuditEvent`, `AuditEventType`, `RunPayload`, `StateSnapshotPayload`, `AgentPayload`, `ToolPayload`, `FindingPayload`, `ApprovalPayload` |
| Progress log | `docs/blueprints/implementation-progress.md` | active | M0 documentation tracking |
| Decision log | `docs/blueprints/decision-log.md` | active | architecture decision records |
| Shared schema package | `libs/audit-common/audit_common/schemas.py` | implemented | `Project`, `Sample`, `Analysis`, `AuditPolicy`, `ArtifactRef`, `Finding`, `ToolExecution`, `ApprovalRequest`, `AuditEvent`, `AuditLog`, `ErrorEnvelope` |
| Shared schema exports | `libs/audit-common/audit_common/__init__.py` | implemented | package-level imports for common schema names and enum value tuples |
| Shared schema tests | `libs/audit-common/tests/test_schemas.py` | implemented | contract shape checks for artifacts, findings, tool limits, events, audit logs, and dangerous approvals |
| Audit agent state | `apps/audit-agents/audit_agents/state.py` | implemented skeleton | `AuditAgentState`, `create_initial_state` |
| Audit supervisor graph | `apps/audit-agents/audit_agents/supervisor.py` | implemented skeleton | `SupervisorGraphSpec`, `build_supervisor_graph`, `triage_sample`, idempotent `request_dangerous_action_approval` |
| Audit agent tests | `apps/audit-agents/tests/` | implemented skeleton | state initialization, supervisor node updates, graph build smoke test |
| Audit API casing | `apps/audit-api/audit_api/casing.py` | implemented mock | `to_camel`, `to_snake` |
| Audit API repository boundary | `apps/audit-api/audit_api/repository.py` | implemented storage boundary | `AuditRepository`, `InMemoryAuditRepository`, `allocate_id` |
| Audit API mock service | `apps/audit-api/audit_api/mock_service.py` | implemented mock resources | `AuditMockService`, `create_project`, `get_project`, `upload_sample`, `get_sample`, `create_analysis`, `get_analysis`, `get_artifact`, `get_artifact_content`, `request_artifact_export`, `list_findings`, `patch_finding`, `create_report`, `get_report`, `get_report_content`, `list_audit_logs`, `start_run`, `resume_run`, `get_analysis_state`, `list_events`, `list_approvals`, `decide_approval` with approval decision audit logs |
| Audit API server helpers | `apps/audit-api/audit_api/server.py` | implemented mock resources | `format_sse_event`, `AuditApiHandler`, `AuditApiHandler.with_service`, `do_GET`, `do_PATCH`, `do_POST` |
| Audit API tests | `apps/audit-api/tests/` | implemented mock resources | casing conversion, in-memory resource flow, HTTP POST/GET/PATCH dispatch, paginated finding query/update, redacted artifact/report content, audit-log query, mock run start/resume, state snapshot, SSE formatting, approval list/approve/reject flows |

## 4. Reserved API Routes

| Route | Status | Notes |
| --- | --- | --- |
| `POST /api/projects` | mock implemented | Create project with classification |
| `GET /api/projects` | mock implemented | List visible projects |
| `GET /api/projects/{projectId}` | mock implemented | Fetch project metadata |
| `POST /api/samples:upload` | mock implemented | Upload isolated sample and produce initial artifact |
| `GET /api/samples/{sampleId}` | mock implemented | Fetch sample metadata |
| `POST /api/analyses` | mock implemented | Create business analysis and prepare LangGraph thread |
| `GET /api/analyses/{analysisId}` | mock implemented | Fetch analysis metadata |
| `POST /api/analyses/{analysisId}/runs` | mock implemented | Start mock supervisor run without dangerous tool execution |
| `POST /api/analyses/{analysisId}/runs:resume` | mock implemented | Resume approved mock run and complete without dangerous tool execution |
| `GET /api/analyses/{analysisId}/events` | mock implemented | SSE stream using `AuditEvent` |
| `GET /api/analyses/{analysisId}/state` | mock implemented | Latest mock `AuditAgentState` snapshot |
| `POST /api/analyses/{analysisId}:cancel` | draft | Cancel analysis/run |
| `POST /api/analyses/{analysisId}:branch` | draft | Branch from checkpoint/state snapshot |
| `GET /api/analyses/{analysisId}/interrupts` | mock implemented | List pending approval gates |
| `POST /api/analyses/{analysisId}/interrupts/{interruptId}:approve` | mock implemented | Approve mock interrupt, append `approval.approved`, and record `AuditLog` |
| `POST /api/analyses/{analysisId}/interrupts/{interruptId}:reject` | mock implemented | Reject mock interrupt, append `approval.rejected`, and record `AuditLog` |
| `GET /api/tool-executions/{toolExecutionId}` | draft | Fetch tool execution metadata |
| `POST /api/tool-executions/{toolExecutionId}:cancel` | draft | Cancel authorized tool execution |
| `GET /api/artifacts/{artifactId}` | mock implemented | Fetch mock artifact metadata |
| `GET /api/artifacts/{artifactId}/content` | mock implemented limited | Return redacted preview for safe mock evidence artifacts and record `artifact.content.read`; sensitive exports remain future approval work |
| `POST /api/artifacts/{artifactId}:request-export` | mock implemented approval scaffold | Create or reuse pending `artifact-export` `ApprovalRequest`; does not return artifact bytes |
| `GET /api/findings` | mock implemented | Query mock findings by `analysisId` or `projectId` with optional `status`/`severity` filters and `limit`/`offset` pagination |
| `PATCH /api/findings/{findingId}` | mock implemented | Analyst status/severity updates and `finding.updated` event |
| `POST /api/reports` | mock implemented | Generate versioned mock report artifact metadata |
| `GET /api/reports/{reportId}` | mock implemented | Fetch mock report artifact metadata |
| `GET /api/reports/{reportId}/content` | mock implemented | Return redacted mock report content and record `report.content.read` audit log |
| `GET /api/audit-logs` | mock implemented | Query mock audit logs by `analysisId` |

## 5. Reserved Event Types

| Event Type | Status | Producer |
| --- | --- | --- |
| `run.queued` | draft | API / LangGraph bridge |
| `run.started` | mock implemented | API / LangGraph bridge |
| `run.interrupted` | mock implemented | LangGraph interrupt bridge |
| `run.resumed` | draft | API approval resume bridge |
| `run.succeeded` | draft | LangGraph bridge |
| `run.failed` | draft | LangGraph bridge |
| `run.cancelled` | draft | API / LangGraph bridge |
| `state.snapshot` | draft | LangGraph bridge |
| `agent.started` | mock implemented | Agent graph nodes |
| `agent.heartbeat` | draft | Agent graph nodes / watchdog |
| `agent.completed` | draft | Agent graph nodes |
| `agent.failed` | draft | Agent graph nodes / watchdog |
| `token.delta` | draft | LLM streaming bridge |
| `tool.queued` | draft | Tool orchestrator |
| `tool.started` | draft | Tool worker |
| `tool.output_chunk` | draft | Tool worker |
| `tool.completed` | draft | Tool worker |
| `tool.failed` | draft | Tool worker |
| `tool.cancelled` | draft | Tool orchestrator |
| `artifact.created` | mock implemented | Artifact service / worker normalizer |
| `finding.created` | draft | Agent verifier / finding service |
| `finding.updated` | mock implemented | Finding service / analyst action |
| `approval.requested` | mock implemented | Policy engine / interrupt bridge / artifact export scaffold |
| `approval.approved` | mock implemented | Approval service |
| `approval.rejected` | mock implemented | Approval service |
| `policy.denied` | draft | Policy engine |
| `error.created` | draft | API / agent / worker bridge |

## 6. Reserved Artifact Types

| Prefix | Status | Examples |
| --- | --- | --- |
| `sample.*` | draft | `sample.original`, `sample.extracted` |
| `static.*` | draft | `static.objdump`, `static.readelf`, `static.ghidra.decompile`, `static.jadx.project` |
| `firmware.*` | draft | `firmware.binwalk.tree`, `firmware.unblob.tree`, `firmware.rootfs`, `firmware.emba.report` |
| `dynamic.*` | draft | `dynamic.pcap`, `dynamic.http_archive`, `dynamic.command_output` |
| `vuln.*` | draft | `vuln.finding_evidence` |
| `report.*` | draft | `report.markdown`, `report.html`, `report.pdf` |

## 7. Duplicate Check Log

| Date | Search | Result |
| --- | --- | --- |
| 2026-04-24 | `find apps libs docs -maxdepth 3 -iname '*audit*'` | Only audit blueprint files existed; no product modules found. |
| 2026-04-24 | `rg "AuditState|ToolExecution|ArtifactRef|FindingDraft|ApprovalRequest|/api/analyses|/api/samples:upload" docs apps libs` | Only blueprint references and LangGraph/CLI MCP support found; no equivalent audit implementation found. |
| 2026-04-24 | `find apps libs docs -maxdepth 4 \( -iname '*audit*' -o -iname '*artifact*' -o -iname '*finding*' -o -iname '*tool*execution*' \)` | No existing audit schema package found before creating `libs/audit-common`. |
| 2026-04-24 | `rg "class .*Artifact|ArtifactRef|FindingDraft|class .*Finding|ToolExecution|ApprovalRequest|AuditPolicy|AuditEvent|AnalysisStatus|SampleFormat" libs apps docs -S` | Only blueprint/registry references found before implementation; new work extends the reserved contract rather than duplicating an implementation. |

| 2026-04-24 | `find apps libs docs -maxdepth 4 \( -type f -o -type d \) | rg 'audit-api|api|server|sample|analysis|artifact|finding|approval|openapi'` | No existing `apps/audit-api`; only contracts, docs, and previous shared schemas/agent skeleton existed. |
| 2026-04-24 | `rg -n "audit-api|FastAPI|http.server|POST /api|GET /api|camelCase|snake_case|serialize|deserialize|Analysis|Project|Sample|ApprovalRequest|SSE|events" apps libs docs -S` | No existing API implementation found; new work extends the reserved `apps/audit-api` path. |
| 2026-04-24 | `rg -n "AuditApiHandler|do_POST|create_analysis|list_approv|approve|reject|ApprovalRequest|approval\.requested|create_initial_state|AuditAgentState|build_supervisor_graph|StateGraph|interrupt|Command|thread_id|run_id" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Existing API handler shell and mock service found; extended `apps/audit-api/audit_api/server.py` instead of creating a parallel API module. |
| 2026-04-24 | `rg -n "ApprovalRequest|approval\.requested|approval\.approved|approval\.rejected|interrupts|approve|reject|decided_at|decision_reason|list_approv|request_dangerous_action_approval|firmware-emulation" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Approval schema, event names, agent placeholder, and draft routes existed; API approval list/approve/reject flows did not. Extended existing mock service and handler. |
| 2026-04-24 | `rg -n "create_initial_state|AuditAgentState|agent_state|state snapshot|state\.snapshot|get_state|/state|langgraph_thread_id|thread_id|create_analysis|AuditMockService|build_supervisor_graph|StateGraph|checkpoint|persistence|Agent Server|runs" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Existing `audit-agents` state constructor found; API state storage/route did not exist. Extended existing mock service/handler and reused `create_initial_state`. |
| 2026-04-24 | `rg -n "POST /api/analyses/.*/runs|/runs|start_run|create_run|run\.started|run\.interrupted|run_id|langgraph_run_id|build_supervisor_graph|SupervisorGraphSpec|triage_sample|request_dangerous_action_approval|agent\.started|approval\.requested|ToolExecution|sandbox|dangerous" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Existing supervisor skeleton found and run route was draft. Extended mock service/handler and made approval gate idempotent; no sandbox/tool execution added. |
| 2026-04-24 | `rg -n "GET /api/projects/|GET /api/samples/|GET /api/analyses/|get_project|get_sample|get_analysis|list_projects|AuditMockService|AuditApiHandler|do_GET" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Existing mock service and handler owned resource APIs; `get_analysis` already existed, while project/sample detail and HTTP detail dispatch were missing. Extended existing files only. |
| 2026-04-24 | `rg -n "resume|run\.resumed|start_run|decide_approval|approved|ApprovalRequest|interrupt.*resume|Command\(resume|POST /api/analyses/.*/runs|:resume|run resume|safe resume|dangerous" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Existing approval decision and mock run start flows found; no mock resume service or route existed. Extended `AuditMockService`/`AuditApiHandler` only and did not add Agent Server or LangGraph `Command(resume=...)` integration. |
| 2026-04-24 | `rg -n "artifacts|findings|reports|runs:resume|approvals|state|events|do_POST|do_GET|resume_run|list_artifacts|list_findings|get_artifact|get_finding" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Existing schemas and draft routes found; no artifact/finding query/update implementation existed. Extended `AuditMockService`/`AuditApiHandler` only. |
| 2026-04-25 | `rg -n "Report|reports|POST /api/reports|GET /api/reports|report\." docs/blueprints/openapi-contract.md docs/blueprints/feature-registry.md docs/blueprints/binary-audit-platform-*.md apps libs/audit-common -S` | Report artifact types and draft routes existed, but no mock report service or HTTP dispatch existed. Extended `AuditMockService` and `AuditApiHandler` only; no parallel report module or Agent Server/MCP route was added. |
| 2026-04-25 | `rg -n "AuditLog|audit log|audit_log|audit-logs|auditLogs|report.*content|reports/.*/content|artifact.*content|artifact-export|sensitive export|export" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Report/artifact content routes were draft and no `AuditLog` schema or audit-log query existed. Extended `libs/audit-common`, `AuditMockService`, and `AuditApiHandler`; no parallel content, artifact, report, Agent Server, or MCP module was added. |
| 2026-04-25 | `find apps libs docs -maxdepth 5 \( -iname '*audit*log*' -o -iname '*content*' -o -iname '*report*' -o -iname '*artifact*' \) -print | sort` | Only prior report/artifact plan docs and unrelated checkpoint conformance report helper were found; no existing product audit-log/content implementation existed. |
| 2026-04-25 | `rg -n "get_report\(|create_report\(|get_artifact\(|list_events\(|AuditMockService|AuditApiHandler|GET /api/reports|GET /api/artifacts/.*/content" apps/audit-api libs/audit-common docs/blueprints -S` | Existing owner files were `AuditMockService` and `AuditApiHandler`; extended those files for report content and audit logs. |
| 2026-04-25 | `rg -n "report.*version|version.*report|reportVersion|versionNumber|supersedes|superseded|latestReport|regenerate|regeneration|create_report|get_report" apps/audit-api libs/audit-common docs/blueprints -S` | Existing report creation/read/content owner methods were found, but no report versioning or regeneration metadata existed. Extended `AuditMockService` and existing report tests only. |
| 2026-04-25 | `find apps libs docs -maxdepth 5 \( -iname '*report*version*' -o -iname '*report*' -o -iname '*version*' \) -print | sort` | Only unrelated version files and existing report helpers were found; no product report versioning module existed. |
| 2026-04-25 | `rg -n "report_\{analysis|report_\{|report_.*_markdown|memory://reports|finding_count|redaction_profile|create_report\(" apps/audit-api docs/blueprints -S` | Existing deterministic report ID and URI rules were found in `AuditMockService`; P13 extended that method instead of adding a parallel generator. |
| 2026-04-25 | `rg -n "list_findings|findings\?|GET /api/findings|pageSize|page_size|nextPage|next_cursor|cursor|pagination|projectId|severity|FindingBoard" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Existing finding ownership was limited to `AuditMockService.list_findings` and `AuditApiHandler`; no project-level filters, status/severity filters, pagination envelope, or parallel finding query module existed. |
| 2026-04-25 | `find apps libs docs -maxdepth 5 \( -iname '*finding*' -o -iname '*pagination*' -o -iname '*filter*' \) -print | sort` | Only prior artifact/finding plan docs and unrelated upstream tests were found; P14 extended the existing mock service and handler only. |
| 2026-04-25 | `rg -n "artifact.*content|artifacts/.*/content|get_artifact_content|ArtifactContent|artifact.content.read|artifact-export|approval_required|redacted|content read|sensitive artifact|report.content.read|get_report_content" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Existing content ownership was report-only `get_report_content` plus `AuditLog`; generic artifact content remained draft with no service method or route dispatch. |
| 2026-04-25 | `find apps libs docs -maxdepth 5 \( -iname '*artifact*content*' -o -iname '*content*' -o -iname '*artifact*' -o -iname '*audit*log*' \) -print | sort` | No product artifact content module existed; P15 extended existing `AuditMockService` and `AuditApiHandler` only. |
| 2026-04-25 | `rg -n "artifact-export|ApprovalRequest|approval\.requested|is_dangerous_approval_action|artifact content requires|request.*export|export.*artifact" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | `artifact-export` enum and approval event schema existed, but it was not classified as dangerous and no artifact export request method or route existed. P16 extended existing approval storage and handler only. |
| 2026-04-25 | `rg -n "Repository|repository|store|storage|_projects|_samples|_analyses|_artifacts|_findings|_audit_logs|_agent_states|_approvals|_events|_next_project|_next_event|Persistence|checkpoint" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | No existing audit API repository owner existed; storage was embedded in `AuditMockService`. P17 adds `audit_api/repository.py` and injects it into the existing mock service. |
| 2026-04-25 | `find apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -maxdepth 5 \( -iname '*repository*' -o -iname '*storage*' -o -iname '*store*' -o -iname '*persistence*' \) -print | sort` | No product repository/storage module was present before P17; new repository file is the single audit API storage boundary and does not duplicate routes, services, Agent Server, or MCP modules. |
| 2026-04-25 | `rg -n "approval\.(approved\|rejected)\|approval decision\|approval.*audit\|audit.*approval\|decide_approval\|decision_reason\|decided_by\|_record_audit_log\|list_audit_logs\|AuditLog" apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -S` | Existing approval decision owner is `AuditMockService.decide_approval`; existing audit-log writer is `_record_audit_log`. P18 extends that owner only and does not add a parallel approval audit module. |
| 2026-04-25 | `find apps/audit-api apps/audit-agents libs/audit-common docs/blueprints -maxdepth 5 \( -iname '*approval*' -o -iname '*audit*log*' -o -iname '*decision*' \) -print | sort` | No dedicated approval decision audit module existed; only decision-log docs matched. Existing service owner is sufficient for the small closed-loop change. |
