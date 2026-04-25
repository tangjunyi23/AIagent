import { LockKeyhole, ShieldCheck } from "lucide-react";

import type { ApprovalRequest } from "../lib/types";

type HumanGateCardProps = {
  approvals: ApprovalRequest[];
};

export function HumanGateCard({ approvals }: HumanGateCardProps) {
  return (
    <section className="panel gate-panel" data-component="HumanGateCard">
      <div className="panel-heading">
        <h2>Human Gate</h2>
        <span>{approvals.filter((approval) => approval.status === "pending").length} pending</span>
      </div>
      <div className="gate-list">
        {approvals.map((approval) => (
          <article key={approval.id} className="approval-item">
            <div className={`approval-status ${approval.status}`}>
              {approval.status === "approved" ? (
                <ShieldCheck size={16} aria-hidden="true" />
              ) : (
                <LockKeyhole size={16} aria-hidden="true" />
              )}
              {approval.status}
            </div>
            <h3>{approval.action}</h3>
            <p>{approval.riskSummary}</p>
            <dl>
              <div>
                <dt>interrupt</dt>
                <dd>{approval.interruptId}</dd>
              </div>
              <div>
                <dt>network</dt>
                <dd>{String(approval.proposedParameters.networkPolicy ?? "none")}</dd>
              </div>
              <div>
                <dt>timeout</dt>
                <dd>{String(approval.proposedParameters.maxToolRuntimeSeconds ?? "n/a")}s</dd>
              </div>
            </dl>
            {approval.decisionReason ? <p className="decision">{approval.decisionReason}</p> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
