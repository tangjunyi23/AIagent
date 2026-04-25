# Audit Web Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the first hot-reloadable `apps/audit-web` frontend workbench for the binary audit platform.

**Architecture:** Use a local Vite + React + TypeScript app under the reserved `apps/audit-web` path. The workbench renders product-owned structured mock resources that mirror the current `/api/*` contract: analysis, state, events, approvals, artifacts, findings, reports, audit logs, and cancellation.

**Tech Stack:** Vite, React, TypeScript, Vitest, Testing Library, lucide-react, CSS modules through plain CSS.

---

### Task 1: Frontend Contract Fixtures And Tests

**Files:**
- Create: `apps/audit-web/package.json`
- Create: `apps/audit-web/tsconfig.json`
- Create: `apps/audit-web/tsconfig.node.json`
- Create: `apps/audit-web/vite.config.ts`
- Create: `apps/audit-web/src/tests/workbenchData.test.ts`

- [ ] **Step 1: Write failing tests**

Create tests that import `createMockWorkbench`, `approveInterrupt`, `rejectInterrupt`, and `cancelRun` from `src/lib/workbenchData.ts`. Assert that events are ordered, pending approvals are present, approving/rejecting approvals emits `approval.*` events, and cancelling emits `run.cancelled`.

- [ ] **Step 2: Run red test**

Run: `cd apps/audit-web && npm test -- --run src/tests/workbenchData.test.ts`

Expected: FAIL because `src/lib/workbenchData.ts` does not exist.

### Task 2: Workbench Data Owner

**Files:**
- Create: `apps/audit-web/src/lib/workbenchData.ts`
- Create: `apps/audit-web/src/lib/types.ts`

- [ ] **Step 1: Implement minimal data owner**

Implement typed product fixtures and state transition helpers for approval approve/reject and run cancel.

- [ ] **Step 2: Run green test**

Run: `cd apps/audit-web && npm test -- --run src/tests/workbenchData.test.ts`

Expected: PASS.

### Task 3: React Workbench UI

**Files:**
- Create: `apps/audit-web/index.html`
- Create: `apps/audit-web/src/main.tsx`
- Create: `apps/audit-web/src/App.tsx`
- Create: `apps/audit-web/src/components/AnalysisTimeline.tsx`
- Create: `apps/audit-web/src/components/HumanGateCard.tsx`
- Create: `apps/audit-web/src/components/ArtifactViewer.tsx`
- Create: `apps/audit-web/src/components/FindingBoard.tsx`
- Create: `apps/audit-web/src/styles.css`

- [ ] **Step 1: Render workbench**

Render analysis status, product timeline, human gate controls, artifact preview, finding board, audit log trail, report metadata, and cancel control from structured state.

- [ ] **Step 2: Run frontend verification**

Run: `cd apps/audit-web && npm run lint && npm test -- --run && npm run build`

Expected: all commands exit 0.

### Task 4: Blueprint Documentation

**Files:**
- Modify: `docs/blueprints/implementation-progress.md`
- Modify: `docs/blueprints/feature-registry.md`
- Modify: `docs/blueprints/decision-log.md`
- Modify: `docs/blueprints/binary-audit-platform-frontend-blueprint.md`
- Modify: `docs/blueprints/openapi-contract.md`
- Modify: `docs/blueprints/event-schema.md`

- [ ] **Step 1: Record duplicate checks, frontend route, commands, and hot reload URL**

Document `apps/audit-web` ownership, visible components, mock API dependency status, official documentation conclusions, and validation results.

- [ ] **Step 2: Run documentation keyword checks**

Run: `rg -n "P20|audit-web|AnalysisTimeline|HumanGateCard|ArtifactViewer|FindingBoard|5173|front-end mock" docs/blueprints apps/audit-web -S`

Expected: new workbench entries are visible in registry/progress/contracts.
