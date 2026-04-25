# audit-api

Mock business API layer for the binary audit platform.

This package intentionally wraps product contracts instead of exposing native LangGraph Agent Server routes. It stores mock resources in memory, accepts/returns public camelCase JSON dictionaries, and keeps internal state compatible with `libs/audit-common` snake_case schema names.
