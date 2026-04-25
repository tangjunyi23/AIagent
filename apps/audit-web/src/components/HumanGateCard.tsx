import { LockKeyhole, ShieldCheck } from "lucide-react";

import type { ApprovalRequest } from "../lib/types";

type HumanGateCardProps = {
  approvals: ApprovalRequest[];
};

const approvalStatusLabels = {
  pending: "待处理",
  approved: "已批准",
  rejected: "已拒绝",
  expired: "已过期",
  cancelled: "已取消"
} as const;

const approvalActionLabels = {
  "dynamic-execution": "动态执行审批",
  "network-enable": "外连网络审批",
  "exploit-verification": "漏洞验证审批",
  "firmware-emulation": "固件模拟审批",
  "artifact-export": "证据导出审批"
} as const;

const networkPolicyLabels: Record<string, string> = {
  none: "禁止外连",
  allowlist: "仅允许白名单",
  unrestricted: "不限制"
};

export function HumanGateCard({ approvals }: HumanGateCardProps) {
  return (
    <section className="panel gate-panel" data-component="HumanGateCard">
      <div className="panel-heading">
        <h2>人工审批</h2>
        <span>{approvals.filter((approval) => approval.status === "pending").length} 个待处理</span>
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
              {approvalStatusLabels[approval.status]}
            </div>
            <h3>{approvalActionLabels[approval.action]}</h3>
            <p>{approval.riskSummary}</p>
            <dl>
              <div>
                <dt>中断</dt>
                <dd>{approval.interruptId}</dd>
              </div>
              <div>
                <dt>网络策略</dt>
                <dd>
                  {
                    networkPolicyLabels[
                      String(approval.proposedParameters.networkPolicy ?? "none")
                    ]
                  }
                </dd>
              </div>
              <div>
                <dt>超时</dt>
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
