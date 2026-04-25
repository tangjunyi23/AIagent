import { Activity, CircleDot, ShieldAlert } from "lucide-react";

import type { AuditEvent } from "../lib/types";

type AnalysisTimelineProps = {
  events: AuditEvent[];
};

export function AnalysisTimeline({ events }: AnalysisTimelineProps) {
  return (
    <section className="panel timeline-panel" data-component="AnalysisTimeline">
      <div className="panel-heading">
        <h2>Timeline</h2>
        <span>{events.length} events</span>
      </div>
      <ol className="timeline">
        {events.map((event) => (
          <li key={event.id}>
            <div className="event-icon">
              {event.type.startsWith("approval") ? (
                <ShieldAlert size={16} aria-hidden="true" />
              ) : (
                <Activity size={16} aria-hidden="true" />
              )}
            </div>
            <div>
              <div className="event-title">
                <strong>{event.type}</strong>
                <span>#{event.sequence}</span>
              </div>
              <p>
                <CircleDot size={12} aria-hidden="true" />
                {event.agent ?? "api"} / {event.node ?? "route"}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
