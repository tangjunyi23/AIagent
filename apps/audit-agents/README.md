# audit-agents

Minimal LangGraph supervisor skeleton for the binary audit platform.

This app owns product-level agent state and graph composition. It imports shared contracts from `libs/audit-common` and keeps dangerous dynamic actions behind approval placeholder nodes until sandbox workers and interrupt resume handling are implemented.
