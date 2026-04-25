import { useMemo, useState } from "react";
import { Ban, CheckCircle2, GitBranch, ShieldAlert, XCircle } from "lucide-react";

import { AnalysisTimeline } from "./components/AnalysisTimeline";
import { ArtifactViewer } from "./components/ArtifactViewer";
import { FindingBoard } from "./components/FindingBoard";
import { HumanGateCard } from "./components/HumanGateCard";
import {
  approveInterrupt,
  branchFromCheckpoint,
  cancelRun,
  createMockWorkbench,
  rejectInterrupt
} from "./lib/workbenchData";

export default function App() {
  const [workbench, setWorkbench] = useState(() => createMockWorkbench());
  const pendingApproval = useMemo(
    () => workbench.approvals.find((approval) => approval.status === "pending"),
    [workbench.approvals]
  );
  const statusTone = workbench.analysis.status === "interrupted" ? "attention" : "neutral";

  return (
    <main className="app-shell">
      <section className="top-bar">
        <div>
          <p className="eyebrow">Binary Audit Platform</p>
          <h1>Firmware Analysis Workbench</h1>
        </div>
        <div className={`status-pill ${statusTone}`}>
          <ShieldAlert size={16} aria-hidden="true" />
          {workbench.analysis.status}
        </div>
      </section>

      <section className="summary-band">
        <div>
          <span>Analysis</span>
          <strong>{workbench.analysis.id}</strong>
        </div>
        <div>
          <span>Thread</span>
          <strong>{workbench.analysis.langgraphThreadId}</strong>
        </div>
        <div>
          <span>Run</span>
          <strong>{workbench.analysis.langgraphRunId}</strong>
        </div>
        <div>
          <span>Checkpoint</span>
          <strong>{workbench.state.checkpointId}</strong>
        </div>
      </section>

      <section className="action-strip">
        <button
          type="button"
          className="command danger"
          onClick={() => setWorkbench((current) => cancelRun(current))}
          disabled={workbench.analysis.status === "cancelled"}
        >
          <Ban size={16} aria-hidden="true" />
          Cancel Run
        </button>
        <button
          type="button"
          className="command"
          onClick={() =>
            setWorkbench((current) =>
              branchFromCheckpoint(
                current,
                current.state.checkpointId,
                "Compare alternate static-only path."
              )
            )
          }
        >
          <GitBranch size={16} aria-hidden="true" />
          Branch From Checkpoint
        </button>
        {pendingApproval ? (
          <>
            <button
              type="button"
              className="command approve"
              onClick={() =>
                setWorkbench((current) =>
                  approveInterrupt(
                    current,
                    pendingApproval.interruptId,
                    "Approved for isolated component emulation with no external network."
                  )
                )
              }
            >
              <CheckCircle2 size={16} aria-hidden="true" />
              Approve Gate
            </button>
            <button
              type="button"
              className="command reject"
              onClick={() =>
                setWorkbench((current) =>
                  rejectInterrupt(
                    current,
                    pendingApproval.interruptId,
                    "Dynamic analysis is outside the current authorization scope."
                  )
                )
              }
            >
              <XCircle size={16} aria-hidden="true" />
              Reject Gate
            </button>
          </>
        ) : null}
      </section>

      <section className="workspace-grid">
        <AnalysisTimeline events={workbench.events} />
        <HumanGateCard approvals={workbench.approvals} />
        <ArtifactViewer artifacts={workbench.artifacts} auditLogs={workbench.auditLogs} />
        <FindingBoard findings={workbench.findings} />
      </section>

      <section className="lower-grid">
        <div className="panel">
          <div className="panel-heading">
            <h2>Reports</h2>
          </div>
          <div className="report-row">
            <span>{workbench.reports[0].name}</span>
            <strong>v{workbench.reports[0].versionNumber}</strong>
            <span>{workbench.reports[0].type}</span>
          </div>
        </div>
        <div className="panel">
          <div className="panel-heading">
            <h2>Audit Logs</h2>
          </div>
          <ol className="audit-log">
            {workbench.auditLogs.map((log) => (
              <li key={log.id}>
                <span>{log.action}</span>
                <strong>{log.resourceId}</strong>
              </li>
            ))}
          </ol>
        </div>
      </section>
    </main>
  );
}
