import { Bug, FileSearch } from "lucide-react";

import type { Finding } from "../lib/types";

type FindingBoardProps = {
  findings: Finding[];
};

export function FindingBoard({ findings }: FindingBoardProps) {
  return (
    <section className="panel finding-panel" data-component="FindingBoard">
      <div className="panel-heading">
        <h2>Findings</h2>
        <span>{findings.length} active</span>
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
              <span className={`severity ${finding.severity}`}>{finding.severity}</span>
              <span>{finding.status}</span>
              <span>{Math.round(finding.confidence * 100)}% confidence</span>
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
