import { FileJson, Lock } from "lucide-react";

import type { ArtifactRef, AuditLog } from "../lib/types";

type ArtifactViewerProps = {
  artifacts: ArtifactRef[];
  auditLogs: AuditLog[];
};

export function ArtifactViewer({ artifacts, auditLogs }: ArtifactViewerProps) {
  return (
    <section className="panel artifact-panel" data-component="ArtifactViewer">
      <div className="panel-heading">
        <h2>Artifacts</h2>
        <span>{auditLogs.length} audit logs</span>
      </div>
      {artifacts.map((artifact) => (
        <article key={artifact.id} className="artifact-item">
          <div className="artifact-title">
            <FileJson size={18} aria-hidden="true" />
            <div>
              <strong>{artifact.name}</strong>
              <span>{artifact.type}</span>
            </div>
          </div>
          <pre>{artifact.preview}</pre>
          <div className="artifact-footer">
            <span>{artifact.mediaType}</span>
            <span>
              <Lock size={13} aria-hidden="true" />
              {artifact.redacted ? "redacted preview" : "raw preview"}
            </span>
          </div>
        </article>
      ))}
    </section>
  );
}
