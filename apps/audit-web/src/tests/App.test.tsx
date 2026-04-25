import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import App from "../App";

describe("App", () => {
  it("renders the binary audit workbench panels from structured state", () => {
    const markup = renderToString(<App />);

    expect(markup).toContain("Firmware Analysis Workbench");
    expect(markup).toContain("AnalysisTimeline");
    expect(markup).toContain("HumanGateCard");
    expect(markup).toContain("ArtifactViewer");
    expect(markup).toContain("FindingBoard");
    expect(markup).toContain("Mock suspicious firmware string");
  });
});
