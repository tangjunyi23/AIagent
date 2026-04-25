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

const analysisStatusLabels = {
  queued: "已排队",
  running: "运行中",
  interrupted: "等待审批",
  succeeded: "已完成",
  failed: "失败",
  cancelled: "已取消"
} as const;

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
          <p className="eyebrow">二进制漏洞审计工作台</p>
          <h1>思而听二进制漏洞审计平台</h1>
        </div>
        <div className={`status-pill ${statusTone}`}>
          <ShieldAlert size={16} aria-hidden="true" />
          {analysisStatusLabels[workbench.analysis.status]}
        </div>
      </section>

      <section className="summary-band">
        <div>
          <span>分析</span>
          <strong>{workbench.analysis.id}</strong>
        </div>
        <div>
          <span>线程</span>
          <strong>{workbench.analysis.langgraphThreadId}</strong>
        </div>
        <div>
          <span>运行</span>
          <strong>{workbench.analysis.langgraphRunId ?? "未启动"}</strong>
        </div>
        <div>
          <span>检查点</span>
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
          取消运行
        </button>
        <button
          type="button"
          className="command"
          onClick={() =>
            setWorkbench((current) =>
              branchFromCheckpoint(
                current,
                current.state.checkpointId,
                "对比仅静态分析的替代路径。"
              )
            )
          }
        >
          <GitBranch size={16} aria-hidden="true" />
          从检查点分支
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
                    "批准在隔离组件模拟中继续，保持外连网络关闭。"
                  )
                )
              }
            >
              <CheckCircle2 size={16} aria-hidden="true" />
              批准审批
            </button>
            <button
              type="button"
              className="command reject"
              onClick={() =>
                setWorkbench((current) =>
                  rejectInterrupt(
                    current,
                    pendingApproval.interruptId,
                    "动态分析超出当前授权范围。"
                  )
                )
              }
            >
              <XCircle size={16} aria-hidden="true" />
              拒绝审批
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
            <h2>报告</h2>
          </div>
          <div className="report-row">
            <span>{workbench.reports[0].name}</span>
            <strong>v{workbench.reports[0].versionNumber}</strong>
            <span>{workbench.reports[0].type}</span>
          </div>
        </div>
        <div className="panel">
          <div className="panel-heading">
            <h2>审计日志</h2>
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
