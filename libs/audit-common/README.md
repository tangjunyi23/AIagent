# audit-common

Shared typed schema contracts for the binary audit platform. This package mirrors the M0 API and SSE contracts in `docs/blueprints/openapi-contract.md` and `docs/blueprints/event-schema.md`.

The package intentionally contains no tool execution logic. API, agent, worker, and frontend adapters should import these names to avoid duplicating schema constants and TypedDict definitions.
