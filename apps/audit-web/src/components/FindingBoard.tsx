import { Bug, FileSearch } from "lucide-react";

import type { Finding } from "../lib/types";

type FindingBoardProps = {
  findings: Finding[];
};

const severityLabels = {
  info: "提示",
  low: "低危",
  medium: "中危",
  high: "高危",
  critical: "严重"
} as const;

const findingStatusLabels = {
  draft: "草稿",
  "needs-review": "待复核",
  confirmed: "已确认",
  "false-positive": "误报",
  "accepted-risk": "已接受风险",
  fixed: "已修复"
} as const;

export function FindingBoard({ findings }: FindingBoardProps) {
  return (
    <section className="panel finding-panel" data-component="FindingBoard">
      <div className="panel-heading">
        <h2>漏洞发现</h2>
        <span>{findings.length} 个活跃</span>
      </div>
      <div className="finding-list">
        {findings.map((finding) => (
          <article key={finding.id} className="finding-item">
            <div className="finding-title">
              <Bug size={18} aria-hidden="true" />
              <div>
                <strong>{finding.title}</strong>
                <span>{finding.affectedComponent}</span>
              </div>
            </div>
            <p>{finding.description}</p>
            <div className="finding-meta">
              <span className={`severity ${finding.severity}`}>{severityLabels[finding.severity]}</span>
              <span>{findingStatusLabels[finding.status]}</span>
              <span>{Math.round(finding.confidence * 100)}% 置信度</span>
            </div>
            <div className="evidence-link">
              <FileSearch size={14} aria-hidden="true" />
              {finding.evidenceArtifactIds.join(", ")}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
