import { describe, expect, it } from "vitest";

import {
  approveInterrupt,
  cancelRun,
  createMockWorkbench,
  rejectInterrupt
} from "../lib/workbenchData";

describe("audit workbench data", () => {
  it("creates a structured workbench snapshot with ordered product events", () => {
    const workbench = createMockWorkbench();

    expect(workbench.analysis.id).toBe("analysis_1");
    expect(workbench.analysis.status).toBe("interrupted");
    expect(workbench.approvals.some((approval) => approval.status === "pending")).toBe(true);
    expect(workbench.events.map((event) => event.sequence)).toEqual([1, 2, 3, 4]);
    expect(workbench.events.map((event) => event.type)).toContain("approval.requested");
    expect(workbench.artifacts[0].type).toBe("vuln.finding_evidence");
    expect(workbench.findings[0].evidenceArtifactIds).toEqual(["artifact_analysis_1_evidence"]);
  });

  it("approves the pending interrupt and appends an approval event plus audit log", () => {
    const approved = approveInterrupt(
      createMockWorkbench(),
      "interrupt_analysis_1_firmware_emulation",
      "Approved for isolated component emulation with no network."
    );

    expect(approved.approvals[0].status).toBe("approved");
    expect(approved.events.at(-1)?.type).toBe("approval.approved");
    expect(approved.events.at(-1)?.sequence).toBe(5);
    expect(approved.auditLogs.at(-1)?.action).toBe("approval.approved");
  });

  it("rejects the pending interrupt without changing evidence records", () => {
    const rejected = rejectInterrupt(
      createMockWorkbench(),
      "interrupt_analysis_1_firmware_emulation",
      "Dynamic analysis is outside the current scope."
    );

    expect(rejected.approvals[0].status).toBe("rejected");
    expect(rejected.events.at(-1)?.type).toBe("approval.rejected");
    expect(rejected.findings[0].evidenceArtifactIds).toEqual(["artifact_analysis_1_evidence"]);
  });

  it("cancels the run through the product lifecycle route contract", () => {
    const cancelled = cancelRun(createMockWorkbench());

    expect(cancelled.analysis.status).toBe("cancelled");
    expect(cancelled.events.at(-1)?.type).toBe("run.cancelled");
    expect(cancelled.state.nextActions).toContain("Run cancelled by analyst");
  });
});
