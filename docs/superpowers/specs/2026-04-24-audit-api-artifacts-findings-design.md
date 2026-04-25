# Audit API Artifacts and Findings Query Design

## Scope

Implement P10 mock resource query endpoints for the binary audit platform API. The scope is limited to extending the existing in-memory `AuditMockService` and `AuditApiHandler` so frontend artifact and finding panels can bind to stable contracts.

## Architecture

The product `/api/*` layer remains the authorization, RBAC, audit, and contract boundary. This design does not expose native Agent Server `/threads`, `/runs`, or `/mcp` routes and does not add real object storage, persistence, sandbox execution, or MCP tool servers.

The mock service will seed deterministic artifacts and findings for each created analysis. The seeded finding references the seeded evidence artifact, exercising the contract rule that durable findings point to evidence artifacts instead of relying on event text.

## API Surface

- `GET /api/artifacts/{artifactId}` returns artifact metadata in public camelCase JSON.
- `GET /api/findings?analysisId={analysisId}` returns findings for one analysis.
- `PATCH /api/findings/{findingId}` updates analyst-editable finding fields: `status`, `severity`, and optional `description`.

## Data Flow

Creating an analysis adds one mock evidence artifact and one mock finding to service indexes and the agent state snapshot. Listing findings filters by `analysis_id`. Patching a finding updates `updated_at`, emits `finding.updated`, and synchronizes the state snapshot.

## Error Handling

Missing artifacts, findings, or analyses use existing `KeyError` handling through the HTTP handler and return `404 not_found`. Unsupported paths continue to return `404 not_found`.

## Testing

Follow TDD in `apps/audit-api` by first adding failing service and route tests. Verify with targeted unittest commands, then run `make format`, `make lint`, and `make test` in `apps/audit-api`.

## Self-Review

- No placeholders remain.
- Scope stays inside the existing mock API implementation.
- No parallel modules, persistence layer, or direct MCP/Agent Server exposure are introduced.
