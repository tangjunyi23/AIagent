# 二进制审计平台前端蓝图

## 1. 产品定位

将 LangGraph 二次开发为“二进制审计平台”的可视化工作台。前端负责承接样本上传、分析编排、人工确认、实时进度、证据链查看、漏洞验证、报告交付和团队协作，后端负责多 agent 编排、真实工具执行与审计数据持久化。

目标用户包括 CTF 选手、安全研究员、恶意软件分析师、固件逆向工程师、移动安全工程师、代码审计人员和企业安全团队。

## 2. 设计原则

- **任务驱动**：用户从“样本”或“目标场景”进入，而不是从单个工具进入。
- **证据优先**：所有 AI 结论必须能关联到工具输出、反编译片段、污点路径、PCAP、HTTP 请求、日志或人工备注。
- **可中断可恢复**：对接 LangGraph thread/run/checkpoint 语义，任何长任务都能暂停、恢复、重放和分支分析。
- **人机协同**：危险动作、动态攻击、模拟网络暴露、恶意样本执行、漏洞利用验证必须有人工审批节点。
- **多视图联动**：文件、函数、图、日志、时间线、漏洞、报告之间通过 artifact ID、address、symbol、CVE/CWE、request ID 串联。
- **并行开发**：前端通过 OpenAPI/SDK 与稳定 API contract 开发，后端通过 mock server 和事件 schema 支撑联调。

## 3. 技术栈建议

### 3.1 Web 应用

- **框架**：Next.js 或 Vite + React，优先 Next.js App Router，便于 SSR 登录态、路由分组和报告预览。
- **语言**：TypeScript。
- **UI**：Tailwind CSS + shadcn/ui 或 Ant Design Pro。企业版偏 Ant Design Pro，安全分析工具偏 shadcn/ui + 自定义面板。
- **状态**：TanStack Query 管理服务端状态，Zustand 管理工作台局部状态。
- **图形**：React Flow 展示 agent DAG、固件流程、调用图；Cytoscape.js 展示函数调用图/污点图；Monaco Editor 展示反编译代码、伪代码、YARA/Sigma/脚本。
- **终端/日志**：xterm.js 展示工具执行日志和受限交互 shell。
- **实时通道**：SSE 作为默认 run event 流，WebSocket 用于多人协作、动态抓包、模拟控制台和高频日志。
- **SDK**：优先封装 `@langchain/langgraph-sdk` 或 REST client；MCP 客户端仅用于调试/插件模式，不直接替代业务 API。

### 3.2 前端目录规划

```text
apps/audit-web/
  app/
    (auth)/login/
    (workspace)/projects/
    (workspace)/samples/
    (workspace)/analyses/[analysisId]/
    (workspace)/reports/[reportId]/
    (admin)/tools/
    (admin)/policies/
  components/
    analysis-timeline/
    artifact-viewer/
    graph-viewer/
    hex-viewer/
    human-gate/
    report-builder/
    tool-console/
    vuln-board/
  features/
    auth/
    projects/
    samples/
    analyses/
    agents/
    artifacts/
    firmware/
    mobile/
    malware/
    reports/
    settings/
  lib/
    api/
    langgraph/
    mcp/
    schemas/
    telemetry/
  tests/
```

如直接放在 LangGraph monorepo 中，建议新增 `apps/audit-web`，避免污染 `libs/sdk-js`。`libs/sdk-js` 当前仓库提示 JS SDK 已迁出，应通过 npm 包依赖或单独 workspace package 引入。

## 4. 核心页面与用户流程

### 4.1 登录与租户选择

- 登录页支持本地账号、OIDC/SAML、API Token。
- 首次进入选择组织、项目和数据保密级别。
- 展示当前用户可用工具权限：静态分析、动态执行、恶意样本沙箱、固件模拟、外连网络、漏洞验证。

### 4.2 项目仪表盘

- 指标：样本总数、进行中分析、已确认漏洞、待人工审批、工具失败率、平均分析时长。
- 最近任务：按 run 状态展示 `queued/running/interrupted/succeeded/failed/cancelled`。
- 风险概览：CWE/CVE 分布、固件/移动/恶意样本分类、严重度趋势。
- 队列状态：后端 queue worker、tool worker、sandbox worker、EMBA worker 健康度。

### 4.3 样本上传页

支持入口：

- 单文件：ELF、PE、Mach-O、DEX、APK、IPA、SO、DLL、EXE、BIN。
- 压缩包：zip、tar、7z，支持密码输入和隔离解压。
- 固件：bin、trx、img、ubi、squashfs、jffs2、cpio、initramfs 等。
- 远程目标：URL、Git 仓库、容器镜像、设备固件下载链接。
- CTF 模式：二进制 + libc + ld + Dockerfile + 远程 nc 信息。

上传后前端展示：

- SHA256、文件大小、MIME、magic、熵、签名、架构、位数、入口点。
- 自动推荐分析模板：CTF pwn/reverse、恶意软件、固件、移动 APK、企业安全风险、代码审计。
- 用户可勾选“允许动态执行”“允许联网”“允许漏洞验证”“生成最终报告”。

### 4.4 分析创建向导

步骤：

1. 选择样本和场景。
2. 选择分析深度：快速 triage、标准审计、深度逆向、完整固件流水线。
3. 选择工具链：Ghidra、IDA/idat、objdump/readelf、radare2、jadx、apktool、binwalk、unblob、Joern、EMBA、QEMU、Frida、tcpdump、nmap、Burp/ZAP。
4. 选择 agent 策略：自动、保守、高并发、人工审批优先。
5. 配置安全策略：沙箱网络、CPU/内存/超时、挂载只读、密钥脱敏、外连白名单。
6. 提交后创建 backend `analysis`，后端映射为 LangGraph thread + run。

### 4.5 分析运行工作台

左侧为分析导航，中间为主视图，右侧为 agent/证据/人工审批侧栏。

主区域标签页：

- **Overview**：样本信息、目标、分析策略、当前状态。
- **Timeline**：按 LangGraph 节点、工具任务、人工节点展示事件。
- **Agents**：Supervisor、Triage、Reverse、Firmware、Mobile、Dynamic、Exploit、Report 等 agent 的 DAG 和当前状态。
- **Artifacts**：文件树、反编译结果、日志、PCAP、截图、内存 dump、SBOM、报告。
- **Static Analysis**：函数列表、字符串、导入导出、CFG、调用图、反编译代码。
- **Taint Analysis**：source/sink、路径、污点图、证据片段、置信度。
- **Dynamic Analysis**：模拟状态、服务列表、HTTP 请求、抓包、命令注入测试、攻击面。
- **Findings**：漏洞列表、证据、复现步骤、影响范围、修复建议、人工确认状态。
- **Report**：可编辑最终报告和导出。

### 4.6 人工审批与防卡死体验

前端必须把后端 `interrupt` 显示为明确审批卡片：

- 审批类型：执行恶意样本、启动 QEMU、允许外连、运行 exploit、执行高风险命令、进入设备交互 shell。
- 审批内容：操作目的、命令、参数、沙箱限制、预计耗时、可观测输出。
- 操作：批准、拒绝、修改参数后批准、转交他人、终止 run、从 checkpoint 分支。

防卡死 UX：

- 每个 agent 和工具任务显示 heartbeat、最近输出、最长无输出时间。
- 超时后提供“重试当前节点”“换备用工具”“降级分析”“切换 agent”“人工接管”。
- 对 LLM 长思考节点显示 token/时间预算和当前阶段。
- 支持从任一 checkpoint 创建分支分析，保留原任务证据链。

### 4.7 固件分析专用工作台

固件流程可视化为阶段化 pipeline：

```text
固件识别/解密/解包 -> 文件系统建模 -> 静态逆向 -> Joern 污点分析 -> EMBA 分析 -> 局部组件模拟/完整系统模拟 -> 动态流量与攻击面挖掘 -> 漏洞验证 -> 报告
```

页面能力：

- 展示 binwalk/unblob/EMBA 解包树，标注 kernel、rootfs、web root、init script、服务配置、证书、默认密码。
- 静态分析区按二进制、CGI、Lua/PHP/Shell、配置文件、硬编码密钥分类。
- 模拟选择：用户选择跳过、局部服务模拟、完整系统 QEMU 模拟、EMBA 自动模拟。
- 动态分析：端口列表、Web 路由、登录状态、HTTP 抓包、命令注入 payload 结果、弱口令尝试、文件读写证据。
- EMBA 集成结果：模块输出、风险等级、CVE、配置风险、SBOM、固件组件清单。

### 4.8 移动 APK 工作台

- APK 基础信息：包名、版本、签名、min/target SDK、权限、组件、导出组件。
- jadx/apktool 输出浏览：Java/Kotlin 反编译、smali、Manifest、资源。
- 风险视图：硬编码密钥、WebView 配置、导出组件、深链、加密误用、调试开关、证书校验绕过。
- 动态视图：Frida hook 脚本、网络请求、文件访问、敏感 API 调用。

### 4.9 CTF 工作台

- 模式：pwn、reverse、crypto 辅助、web-binary 混合。
- 二进制面板：checksec、symbols、ROP gadgets、libc fingerprint、函数图、栈/堆利用假设。
- Exploit 面板：生成 PoC、运行本地 Docker、远程验证、flag 证据。
- 安全限制：远程连接信息需显式确认，禁止对非授权目标执行攻击。

## 5. 前后端 API Contract

前端与后端并行开发时，先冻结以下 contract。所有枚举通过 OpenAPI 生成 TypeScript 类型。

### 5.1 核心资源

```ts
type Project = {
  id: string;
  name: string;
  tenantId: string;
  classification: 'public' | 'internal' | 'confidential' | 'restricted';
};

type Sample = {
  id: string;
  projectId: string;
  filename: string;
  sha256: string;
  size: number;
  format: 'ELF' | 'PE' | 'MachO' | 'APK' | 'Firmware' | 'Archive' | 'Unknown';
  arch?: string;
  uploadedAt: string;
};

type Analysis = {
  id: string;
  projectId: string;
  sampleIds: string[];
  scenario: 'ctf' | 'risk' | 'malware' | 'firmware' | 'code-audit' | 'mobile';
  status: 'queued' | 'running' | 'interrupted' | 'succeeded' | 'failed' | 'cancelled';
  langgraphThreadId: string;
  langgraphRunId?: string;
  createdAt: string;
  updatedAt: string;
};

type AgentEvent = {
  id: string;
  analysisId: string;
  runId: string;
  node: string;
  agent: string;
  type: 'state' | 'token' | 'tool_start' | 'tool_output' | 'tool_end' | 'artifact' | 'finding' | 'interrupt' | 'error';
  payload: unknown;
  createdAt: string;
};
```

### 5.2 主要接口

- `POST /api/projects`：创建项目。
- `POST /api/samples:upload`：上传样本，返回 sample 与预识别结果。
- `POST /api/analyses`：创建分析，返回 analysis + LangGraph thread。
- `POST /api/analyses/{id}/runs`：启动或重启 run。
- `GET /api/analyses/{id}/events`：SSE 订阅事件。
- `GET /api/analyses/{id}/state`：获取最新状态快照。
- `POST /api/analyses/{id}/interrupts/{interruptId}:approve`：审批中断。
- `POST /api/analyses/{id}/interrupts/{interruptId}:reject`：拒绝中断。
- `POST /api/analyses/{id}:cancel`：取消分析。
- `POST /api/analyses/{id}:branch`：从 checkpoint 创建分支。
- `GET /api/artifacts/{artifactId}`：下载或预览 artifact。
- `GET /api/artifacts/{artifactId}/content`：获取受限、脱敏、带审计记录的 artifact 内容预览。
- `POST /api/artifacts/{artifactId}:request-export`：为敏感 artifact 导出创建人工审批请求，不直接下载内容。
- `GET /api/findings?analysisId=&projectId=&status=&severity=&limit=&offset=`：获取分页漏洞发现，支持分析级和项目级列表。
- `PATCH /api/findings/{id}`：人工确认、调整严重度、补充说明。
- `POST /api/reports`：生成报告。

### 5.3 实时事件要求

事件必须满足：

- 有序：按 `sequence` 或 `createdAt + id` 排序。
- 可重放：断线后 `Last-Event-ID` 续传。
- 可过滤：按 agent、node、artifact、severity 过滤。
- 可压缩：大工具日志不直接塞事件，事件只传 artifact/log chunk 引用。

## 6. 组件详细设计

### 6.1 `AnalysisTimeline`

职责：展示 LangGraph run 的节点级进度、工具级进度和人工节点。

输入：`Analysis`、`AgentEvent[]`、`Checkpoint[]`。

交互：

- 点击节点跳转到对应 artifact/log。
- 失败节点显示错误、重试入口和后端建议。
- checkpoint 节点支持创建分支分析。

### 6.2 `AgentGraphViewer`

职责：展示多 agent 编排图。

视图：

- Supervisor 层：规划、分派、汇总。
- Worker 层：triage、reverse、firmware、mobile、dynamic、exploit、report。
- Tool 层：ghidra、idat、objdump、jadx、binwalk、joern、emba、qemu 等。

### 6.3 `ArtifactViewer`

职责：统一预览 artifact。

支持类型：

- 文本：log、markdown、json、yaml、txt。
- 代码：C、伪代码、Java、smali、shell、Lua、PHP。
- 二进制：hex、strings、sections。
- 图：CFG、CG、taint graph、agent DAG。
- 网络：pcap、HTTP archive、Burp/ZAP JSON。
- 报告：markdown/pdf/html/docx。

### 6.4 `HumanGateCard`

职责：承接 LangGraph interrupt。

字段：

- 风险级别、操作类型、命令、沙箱、网络策略、超时、输入输出 artifact。
- 审批表单支持参数覆盖，例如 QEMU 网络模式、payload 字典、目标 URL、HTTP header。

### 6.5 `FindingBoard`

职责：漏洞发现生命周期管理。

状态：

- `candidate`：AI 或工具提出但未验证。
- `verified`：已通过工具/动态复现验证。
- `false_positive`：人工或 agent 驳回。
- `accepted_risk`：业务接受。
- `fixed`：修复完成。

字段：CWE、CVE、CVSS、影响、证据、复现、修复建议、关联 artifact。

### 6.6 P20 初始工作台落地状态

`apps/audit-web` 已创建为 Vite + React + TypeScript 热重载应用，当前第一屏是 `Firmware Analysis Workbench`。

已落地组件：

- `AnalysisTimeline`：按 `AuditEvent.sequence` 展示 `run.*`、`agent.*` 和 `approval.*` mock 事件。
- `HumanGateCard`：展示 `firmware-emulation` interrupt/approval gate、风险摘要和结构化参数。
- `ArtifactViewer`：展示 redacted `vuln.finding_evidence` 预览和审计日志计数。
- `FindingBoard`：展示 mock finding、严重度、状态、置信度和证据 artifact ID。

交互：

- `Approve Gate` 调用前端 mock adapter，将 approval 状态改为 `approved`，追加 `approval.approved` 事件和 `AuditLog`。
- `Reject Gate` 将 approval 状态改为 `rejected`，保留 finding/evidence 记录并追加 `approval.rejected`。
- `Cancel Run` 将 analysis 状态改为 `cancelled`，追加 `run.cancelled` 并更新 state next actions。
- `Branch From Checkpoint` 先以禁用命令展示，因为 `POST /api/analyses/{analysisId}:branch` 仍是后端 draft。

当前前端默认使用本地结构化 mock 数据，不要求 Python mock API 同时运行。后续接入后端时应把 `src/lib/workbenchData.ts` 拆为 mock fixture 与 `/api/*` client adapter，保持组件只依赖 typed view model。

## 7. 权限与安全 UX

前端必须把权限模型显性化：

- 项目权限：读、写、执行、审批、导出、管理。
- 工具权限：静态工具、动态沙箱、外连网络、漏洞验证、恶意样本执行。
- 数据权限：样本下载、报告导出、原始日志、密钥/凭据查看。
- 危险操作必须二次确认并记录审计日志。

敏感信息展示策略：

- 默认脱敏 token、password、private key、cookie。
- 用户有权限时可“短时揭示”，操作记录到审计日志。
- 报告导出前提供敏感信息扫描。

## 8. 可观测性

前端埋点：

- 页面加载、上传耗时、分析创建失败、SSE 断线、审批耗时、报告导出。
- 不采集样本内容、反编译代码或凭据。

运行可视化：

- LangGraph run trace ID。
- agent node 耗时、重试次数、token 使用、工具耗时、artifact 数量。
- 后端队列深度、worker 健康度、沙箱资源使用。

## 9. 前端测试策略

- 单元测试：schema parser、事件 reducer、权限判断、artifact renderer。
- 组件测试：上传向导、HumanGateCard、FindingBoard、Timeline。
- E2E：上传 ELF 快速 triage、上传 APK、固件标准流水线、interrupt 审批、报告导出。
- Mock：使用 MSW 模拟 REST/SSE，后端未完成前由 OpenAPI schema 生成 mock 数据。

## 10. 并行开发里程碑

### M0：契约冻结

- 完成 OpenAPI、事件 schema、状态枚举。
- 前端完成 mock server 与基础布局。P20 已创建 `apps/audit-web` 初始热重载工作台，用本地结构化 mock 展示当前契约。
- 后端提供样本上传与空 run mock。

### M1：最小可用分析

- 支持 ELF/PE/APK/固件上传和格式识别展示。
- 支持创建分析、SSE 时间线、artifact 列表、基础报告。
- 后端跑通 objdump/readelf/jadx/binwalk 至少一种工具链。

### M2：多 agent 可视化与人工中断

- Agent DAG、checkpoint、interrupt 审批上线。
- 支持失败重试、取消、分支。
- 后端接入 LangGraph checkpoint 与 interrupt。

### M3：固件深度分析

- 固件 pipeline 工作台、EMBA 输出、Joern 污点图、模拟控制面上线。
- 支持局部模拟和完整系统模拟的用户选择。

### M4：报告与企业化

- 漏洞生命周期、报告模板、租户权限、审计日志、导出脱敏。

## 11. 与 LangGraph/LangChain 文档的对应关系

- LangGraph 适合作为长运行、有状态、多 actor 的编排层，前端应围绕 thread、run、checkpoint 和 state snapshot 设计。
- Agent Server 的 `/mcp` 端点可把 LangGraph agent 暴露为 MCP tools，适合平台插件化和外部 IDE/客户端调用。
- Agent Server 支持 `/assistants`、`/threads`、`/runs`、`/mcp`、`/ui` 等路由开关，前端产品应通过业务 API 包一层权限和审计，而不是直接暴露全部原生接口。

参考：

- https://docs.langchain.com/langsmith/server-mcp
- https://docs.langchain.com/langsmith/agent-server-scale
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/interrupts
