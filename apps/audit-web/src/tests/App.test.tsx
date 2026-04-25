import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import App from "../App";

describe("App", () => {
  it("renders the Chinese binary audit workbench panels from structured state", () => {
    const markup = renderToString(<App />);

    expect(markup).toContain("思而听二进制漏洞审计平台");
    expect(markup).toContain("二进制漏洞审计工作台");
    expect(markup).toContain("时间线");
    expect(markup).toContain("人工审批");
    expect(markup).toContain("证据文件");
    expect(markup).toContain("漏洞发现");
    expect(markup).toContain("取消运行");
    expect(markup).toContain("从检查点分支");
    expect(markup).toContain("AnalysisTimeline");
    expect(markup).toContain("HumanGateCard");
    expect(markup).toContain("ArtifactViewer");
    expect(markup).toContain("FindingBoard");
    expect(markup).toContain("模拟固件命令执行风险");
    expect(markup).not.toContain("Firmware Analysis Workbench");
    expect(markup).not.toContain("Mock suspicious firmware string");
  });
});
