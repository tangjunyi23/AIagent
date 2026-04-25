import { Activity, CircleDot, ShieldAlert } from "lucide-react";

import type { AuditEvent } from "../lib/types";

type AnalysisTimelineProps = {
  events: AuditEvent[];
};

const eventTypeLabels: Partial<Record<AuditEvent["type"], string>> = {
  "run.queued": "运行已排队",
  "run.started": "运行已启动",
  "run.interrupted": "运行等待审批",
  "run.resumed": "运行已恢复",
  "run.succeeded": "运行已完成",
  "run.failed": "运行失败",
  "run.cancelled": "运行已取消",
  "state.snapshot": "状态快照",
  "agent.started": "Agent 已启动",
  "approval.requested": "请求人工审批",
  "approval.approved": "审批已批准",
  "approval.rejected": "审批已拒绝",
  "artifact.created": "证据已创建",
  "finding.created": "漏洞已创建",
  "finding.updated": "漏洞已更新"
};

export function AnalysisTimeline({ events }: AnalysisTimelineProps) {
  return (
    <section className="panel timeline-panel" data-component="AnalysisTimeline">
      <div className="panel-heading">
        <h2>时间线</h2>
        <span>{events.length} 条事件</span>
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
                <strong>{eventTypeLabels[event.type] ?? event.type}</strong>
                <span>#{event.sequence}</span>
              </div>
              <p>
                <CircleDot size={12} aria-hidden="true" />
                {event.agent ?? "接口"} / {event.node ?? "路由"}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
