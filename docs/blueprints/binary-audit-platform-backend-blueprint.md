# 二进制审计平台后端蓝图

## 1. 后端目标

基于 LangGraph 二次开发一个面向二进制审计的多 agent 后端。后端必须让 AI 具备真实执行、验证和审计能力，而不是只输出自然语言推测。平台通过 LangGraph 管理长运行状态、多 agent 协作、checkpoint、interrupt、失败恢复和工具编排，通过 MCP/工具服务接入 Ghidra、IDA/idat、objdump、jadx、binwalk、Joern、EMBA、QEMU 等专业工具链。

## 2. 总体架构

```text
Frontend
  -> API Gateway / Auth / RBAC
  -> Audit Platform API
       -> LangGraph Agent Server
            -> Supervisor Graph
                 -> Triage Agent
                 -> Static Reverse Agents
                 -> Firmware Agent Team
                 -> Mobile Agent Team
                 -> Dynamic Analysis Agents
                 -> Exploit / Verification Agents
                 -> Report Agent
       -> Tool Orchestrator
            -> MCP Tool Servers
            -> Container Sandbox Workers
            -> VM/QEMU/EMBA Workers
       -> Storage
            -> Postgres metadata/checkpoints
            -> Redis queues/ephemeral run state
            -> Object storage artifacts
            -> Vector/index store optional
       -> Observability
            -> traces/logs/metrics/audit logs
```

## 3. LangGraph 二次开发策略

### 3.1 不直接改核心优先

LangGraph 源码是底座，建议优先采用“产品层扩展 + 少量适配”的方式：

- 新增 `apps/audit-api`：业务 API、鉴权、租户、样本、artifact、finding、report。
- 新增 `apps/audit-agents`：LangGraph graph 定义、多 agent 节点、状态 schema、prompt、路由器。
- 新增 `apps/audit-workers`：工具执行 worker、沙箱执行、EMBA/QEMU 长任务。
- 新增 `libs/audit-sdk-py` 与 `libs/audit-sdk-js`：业务客户端 SDK。
- 如需改 LangGraph CLI/server，优先改配置、schema 和 extension hook，不改核心调度语义。

这样可继续跟进上游 LangGraph，同时把审计平台能力沉淀到产品层。

### 3.2 可复用的 LangGraph 能力

- **StateGraph**：建模多阶段审计流程。
- **Subgraph**：每类样本使用专用子图，例如 firmware、mobile、malware、ctf。
- **Checkpoint**：每个超步骤保存状态，支持失败恢复、暂停、分支和重放。
- **Interrupt**：高风险工具调用、动态执行、人工研判进入审批。
- **Parallel nodes**：不同工具链并行执行，降低单 agent 卡死风险。
- **Streaming events**：向前端实时输出 token、工具日志、artifact、finding 和错误。
- **MCP endpoint**：把审计 agent 暴露为外部可调用工具，同时接入内部 MCP tool servers。

LangChain 文档显示 Agent Server 可通过 `/mcp` 以 Streamable HTTP 暴露 MCP，并且 Agent Server 有 `/assistants`、`/threads`、`/runs`、`/mcp` 等路由能力。后端业务层应在这些原生能力之上增加租户、权限、审计和样本数据模型。

## 4. 后端模块划分

```text
apps/audit-api/
  audit_api/
    main.py
    auth/
    routes/
      projects.py
      samples.py
      analyses.py
      artifacts.py
      findings.py
      reports.py
      tools.py
      admin.py
    services/
      langgraph_runs.py
      artifact_store.py
      sample_intake.py
      policy_engine.py
      event_stream.py
    db/
      models.py
      migrations/

apps/audit-agents/
  audit_agents/
    state.py
    graphs/
      root.py
      ctf.py
      firmware.py
      mobile.py
      malware.py
      risk.py
    agents/
      supervisor.py
      triage.py
      reverse.py
      firmware.py
      mobile.py
      dynamic.py
      exploit.py
      report.py
      verifier.py
    prompts/
    routers/
    evaluators/

apps/audit-workers/
  audit_workers/
    tool_orchestrator.py
    sandbox/
    mcp_servers/
      ghidra_server.py
      idat_server.py
      binutils_server.py
      jadx_server.py
      firmware_server.py
      joern_server.py
      emba_server.py
      qemu_server.py
    parsers/
    normalizers/

libs/audit-common/
  audit_common/
    schemas/
    events.py
    policies.py
    artifact_types.py
```

## 5. 数据模型

### 5.1 核心实体

- **Tenant**：组织、配额、全局策略。
- **Project**：项目、分类等级、成员、工具策略。
- **Sample**：上传文件、hash、格式、架构、来源、隔离状态。
- **Analysis**：业务分析任务，关联 LangGraph thread/run。
- **Run**：LangGraph run 映射，保存状态、进度、错误和 checkpoint 指针。
- **Artifact**：工具输出、文件、日志、图、报告、PCAP、反编译结果。
- **Finding**：漏洞或风险发现，关联证据和验证状态。
- **ToolExecution**：工具调用记录，含命令、参数、容器、退出码、资源消耗。
- **Approval**：人工审批记录，含审批人、操作、参数、结果。
- **AuditLog**：所有敏感操作审计。

### 5.2 Artifact 分类

```text
sample.original
sample.extracted
static.objdump
static.readelf
static.ghidra.project
static.ghidra.decompile
static.idat.export
static.jadx.project
static.joern.cpg
firmware.binwalk.tree
firmware.unblob.tree
firmware.emba.report
firmware.rootfs
firmware.qemu.snapshot
dynamic.pcap
dynamic.http_archive
dynamic.command_output
vuln.finding_evidence
report.markdown
report.pdf
```

### 5.3 状态 schema

LangGraph root state 建议包含：

```python
class AuditState(TypedDict):
    analysis_id: str
    project_id: str
    sample_ids: list[str]
    scenario: Literal['ctf', 'risk', 'malware', 'firmware', 'code-audit', 'mobile']
    policy: AuditPolicy
    samples: list[SampleSummary]
    plan: AnalysisPlan
    tool_tasks: list[ToolTask]
    artifacts: list[ArtifactRef]
    findings: list[FindingDraft]
    approvals: list[ApprovalRequest]
    errors: list[AgentError]
    next_actions: list[str]
    report: ReportDraft | None
```

所有 agent 只能通过结构化 state 写入结果，禁止把关键证据只保存在自由文本里。

## 6. 多 agent 编排

### 6.1 顶层 Supervisor Graph

```text
START
  -> sample_intake
  -> triage_router
  -> parallel_static_analysis
  -> scenario_router
      -> ctf_subgraph
      -> firmware_subgraph
      -> mobile_subgraph
      -> malware_subgraph
      -> risk_subgraph
  -> verification_router
  -> report_builder
  -> END
```

### 6.2 Agent 职责

- **Supervisor Agent**：分解任务、分派子图、预算控制、失败恢复、终止条件判断。
- **Triage Agent**：文件类型识别、架构识别、加壳/压缩/加密判断、工具链推荐。
- **Reverse Agent**：调用 Ghidra/idat/objdump，抽取函数、字符串、CFG、导入导出、伪代码。
- **Firmware Agent**：固件解密/解包、rootfs 建模、服务发现、EMBA/Joern/QEMU 编排。
- **Mobile Agent**：jadx/apktool 输出分析、Manifest 风险、导出组件、敏感 API、动态 hook 建议。
- **Malware Agent**：静态 IoC、反沙箱、C2、行为簇、YARA 建议，默认禁止联网执行。
- **Dynamic Agent**：沙箱执行、抓包、HTTP 流量、服务探测、命令注入测试。
- **Exploit/Verifier Agent**：对候选漏洞做最小化验证，必须遵循授权策略和审批。
- **Report Agent**：汇总证据、生成报告、标注置信度和未完成项。
- **Watchdog Agent**：监控 heartbeat、超时、重复失败、LLM 卡死，触发降级或切换。

### 6.3 防单 AI 卡死机制

- **节点级超时**：每个 agent 节点有 `max_runtime_seconds` 和 `max_llm_tokens`。
- **工具级超时**：每个 ToolExecution 有 CPU、内存、磁盘、wall time 限制。
- **Heartbeat**：agent 与 worker 每 N 秒写入进度；前端展示无输出时长。
- **竞争执行**：关键节点可并行启动两个不同模型/策略，采用 verifier 选择结果。
- **降级路径**：Ghidra 失败降级到 objdump/r2；IDA 失败不阻塞整体；QEMU 失败仍产出静态报告。
- **Checkpoint 分支**：从失败前 checkpoint 切换工具链或参数。
- **Watchdog 路由**：超时后转入 `recover_or_interrupt`，由 supervisor 决定重试、降级、人工接管或终止。
- **结构化输出校验**：所有 agent 输出经 schema validator，不合格时重试或交给 verifier。

## 7. 工具链集成

### 7.1 工具执行原则

- 每个工具封装为独立 MCP tool server 或 worker adapter。
- 工具不直接访问用户文件系统，只访问隔离 workspace。
- 命令行参数必须模板化和白名单化，禁止 agent 拼接任意 shell。
- 输出统一转 artifact，并由 normalizer 抽取结构化 JSON。
- 所有工具记录版本、镜像 digest、命令、退出码、资源消耗和 stdout/stderr artifact。

### 7.2 工具矩阵

| 工具 | 场景 | 输出 |
| --- | --- | --- |
| `file`, `magic`, `lief` | 格式识别 | 格式、架构、入口点、节区 |
| `readelf`, `objdump`, `nm`, `strings` | ELF/通用 triage | 导入导出、符号、反汇编、字符串 |
| `dumpbin`, `pefile`, `capa` | PE | PE header、导入表、能力标签 |
| Ghidra headless | ELF/PE/Mach-O | project、函数、反编译、CFG |
| IDA/idat | 高质量反编译/交叉验证 | idb/i64、伪代码、xref、函数元数据 |
| jadx | APK | Java 反编译、Manifest、资源 |
| apktool | APK | smali、资源、Manifest |
| binwalk/unblob | 固件 | 解包树、rootfs、熵、签名 |
| Joern | 代码/固件 web/CGI | CPG、source/sink、污点路径 |
| EMBA | 固件 | 漏洞模块报告、SBOM、模拟辅助 |
| QEMU/systemd-nspawn/chroot | 固件模拟 | 服务状态、端口、日志、snapshot |
| tcpdump/tshark/mitmproxy | 动态分析 | PCAP、HTTP Archive |
| nmap/httpx/ZAP | 攻击面 | 端口、Web 路由、漏洞候选 |
| Frida | Android 动态 | hook 日志、敏感调用 |
| pwntools/checksec/ROPgadget | CTF | 利用条件、ROP、PoC |

### 7.3 MCP 设计

内部工具服务暴露统一能力：

```json
{
  "tool": "ghidra.analyze",
  "input": {
    "sample_artifact_id": "...",
    "analysis_profile": "standard",
    "timeout_seconds": 1800
  },
  "output": {
    "artifacts": ["..."],
    "summary": {},
    "warnings": []
  }
}
```

LangGraph agent 通过 MCP adapter 调用工具。外部客户端可通过 Agent Server `/mcp` 调用审计 agent，但业务平台默认仍走 `/api/analyses`，以保留权限和审计。

## 8. 各格式分析流程

### 8.1 通用二进制：ELF / PE / Mach-O

```text
intake -> file triage -> strings/imports/sections -> Ghidra/idat/objdump 并行 -> 函数摘要 -> 风险模式匹配 -> verifier -> report
```

关键检查：

- 危险 API：`system`、`popen`、`strcpy`、`memcpy`、`CreateProcess`、`WinExec`、`dlopen`。
- 加密/网络/持久化能力。
- 栈保护、NX、PIE、RELRO、签名、entitlements。
- 硬编码密钥、默认口令、隐藏命令。
- 反调试、反虚拟机、混淆、加壳。

### 8.2 APK / Android

```text
intake -> apktool/jadx -> manifest risk -> code pattern -> native libs reverse -> optional frida dynamic -> verifier -> report
```

关键检查：

- 导出 Activity/Service/Receiver/Provider。
- WebView `addJavascriptInterface`、明文 HTTP、证书校验绕过。
- 硬编码 key、token、云服务凭据。
- 动态加载 dex/so、反调试、root 检测。
- native `.so` 转入通用二进制子图。

### 8.3 固件

完整流程：

```text
固件识别/解密/解包
  -> rootfs 与组件建模
  -> 静态分析：Ghidra/idat/objdump + 配置/脚本分析
  -> Joern 污点分析
  -> EMBA 模块分析
  -> 用户选择：跳过模拟 / 局部重要组件模拟 / 完全系统模拟
  -> 模拟成功后动态分析：端口、Web、抓包、命令注入、攻击面挖掘
  -> 漏洞验证
  -> 报告
```

#### 8.3.1 固件解密/解包

- 检测厂商、Magic、熵、压缩/加密特征。
- 依次尝试 binwalk、unblob、firmware-mod-kit、sasquatch、ubi_reader。
- 对高熵区域生成“疑似加密/压缩” finding，要求用户提供密钥或允许爆破/字典。
- 解包结果保存为 rootfs artifact，保留原始 offset 到文件映射。

#### 8.3.2 静态分析

- rootfs 文件分类：ELF、脚本、Web、配置、证书、数据库、init/service。
- Ghidra/idat 分析关键 ELF：web server、CGI、UPnP、诊断工具、升级程序、认证模块。
- Joern 分析 C/C++、CGI、PHP、Lua、Shell 中 source/sink：
  - source：HTTP 参数、环境变量、配置文件、IPC、socket、nvram。
  - sink：`system/popen/exec*`、文件写、命令模板、SQL、危险库调用。
- 输出污点路径图和最小证据片段。

#### 8.3.3 EMBA 与模拟

- EMBA 作为固件安全扫描和模拟辅助工具，由独立 worker 运行。
- 用户在前端选择模拟策略：
  - `none`：只做静态和 EMBA。
  - `component`：局部模拟 web/cgi/关键服务。
  - `full-system`：QEMU 完整系统模拟。
  - `emba-auto`：优先使用 EMBA 自动分析/模拟模块。
- 模拟前必须 interrupt 审批，说明网络隔离、端口映射、资源限制。

#### 8.3.4 动态分析

- 启动服务后收集端口、进程、路由、Web 页面、认证流程。
- 功能点抓包：tshark/mitmproxy 生成 pcap 与 HTTP archive。
- 攻击面挖掘：路由枚举、参数收集、命令注入 payload、路径遍历、弱口令。
- 动态验证必须关联静态污点路径或工具发现，避免无授权扫描泛化。

### 8.4 恶意软件

- 默认离线沙箱，禁止外连公网。
- 静态 IoC：domain、IP、URL、mutex、registry、file path、YARA。
- 动态运行需要审批和隔离网络，模拟 C2 可用假 DNS/INetSim。
- 报告输出行为链和防护建议，不输出可直接滥用的攻击扩散步骤。

### 8.5 CTF

- 可允许更高自动化，但仍要求目标授权。
- pwn 子图：checksec -> 反汇编 -> 漏洞假设 -> PoC -> 本地验证 -> 远程验证。
- reverse 子图：验证逻辑重建 -> solver -> flag 验证。
- Exploit 结果必须保存最小 PoC、运行日志和 flag 证据。

## 9. API 设计

### 9.1 业务 API

- `POST /api/samples:upload`：上传样本到隔离区并触发预识别。
- `POST /api/analyses`：创建分析，初始化 LangGraph thread。
- `POST /api/analyses/{id}/runs`：启动 run。
- `GET /api/analyses/{id}/events`：SSE 事件流。
- `GET /api/analyses/{id}/state`：最新状态快照。
- `POST /api/analyses/{id}/interrupts/{interruptId}:approve`：恢复中断。
- `POST /api/analyses/{id}/interrupts/{interruptId}:reject`：拒绝中断。
- `POST /api/analyses/{id}:branch`：基于 checkpoint 创建分支。
- `POST /api/tool-executions/{id}:cancel`：取消工具任务。
- `GET /api/artifacts/{id}`：获取 artifact metadata。
- `GET /api/artifacts/{id}/content`：下载/预览 artifact。
- `POST /api/artifacts/{id}:request-export`：为敏感 artifact 导出创建审批请求。
- `GET /api/findings`：查询 findings。
- `PATCH /api/findings/{id}`：人工确认。
- `POST /api/reports`：生成报告。

### 9.2 LangGraph 原生 API 映射

- Analysis 创建时创建 thread。
- Analysis run 启动时调用 LangGraph runs API。
- 前端事件流由平台 API 统一转发 LangGraph stream + worker events。
- Interrupt 审批映射为对 thread/run 的 resume/update。
- Checkpoint 分支映射为复制 state snapshot 并创建新 thread/run。

### 9.3 MCP 暴露

对外 MCP tools：

- `audit.create_analysis`
- `audit.get_analysis_state`
- `audit.list_findings`
- `audit.get_artifact_summary`
- `audit.resume_interrupt`

内部 MCP tools：

- `tool.ghidra.analyze`
- `tool.idat.export`
- `tool.binutils.inspect`
- `tool.jadx.decompile`
- `tool.binwalk.extract`
- `tool.joern.taint`
- `tool.emba.run`
- `tool.qemu.boot_firmware`
- `tool.dynamic.capture_http`

## 10. 安全隔离

### 10.1 执行隔离

- 所有工具在容器或 VM 内执行。
- 默认无网络，按审批临时开启白名单网络。
- workspace 只挂载样本和输出目录，不挂载宿主敏感目录。
- rootless container，seccomp/apparmor，capability 最小化。
- CPU、内存、磁盘、进程数、wall time 限制。
- 恶意样本和动态模拟使用独立网络 namespace。

### 10.2 命令安全

- Agent 不能直接提交 shell 字符串。
- Tool adapter 接收结构化参数并渲染白名单命令。
- 参数校验包括路径归一化、artifact 所属检查、扩展名/类型检查。
- stdout/stderr 作为 artifact 保存，敏感日志脱敏后进入前端。

### 10.3 数据安全

- 样本按租户和项目隔离。
- 对象存储开启服务端加密。
- 下载样本、揭示凭据、导出报告都写审计日志。
- 报告导出前执行 secret scanner。

## 11. 可观测性与审计

指标：

- run 时长、节点耗时、工具耗时、失败率、重试率、interrupt 数量。
- worker CPU/内存/磁盘、队列深度、sandbox 创建耗时。
- LLM token、模型错误、schema validation 失败。

日志：

- API access log。
- ToolExecution command log。
- Agent decision log。
- Approval audit log。
- Artifact access log。

Trace：

- 每个 analysis 对应 trace ID。
- 每个 agent 节点和工具调用为子 span。
- artifact/finding ID 写入 span metadata。

## 12. 部署架构

### 12.1 开发环境

```text
Docker Compose:
  audit-api
  langgraph-agent-server
  worker-general
  worker-ghidra
  worker-mobile
  worker-firmware
  postgres
  redis
  minio
```

### 12.2 生产环境

- Kubernetes。
- API server 水平扩展。
- LangGraph queue workers 按场景拆池：general、reverse、firmware、dynamic、report。
- Ghidra/IDA/EMBA/QEMU worker 使用 node selector 和资源配额。
- 对动态执行 worker 使用隔离节点池。
- Postgres 负责 metadata/checkpoint，Redis 负责队列和临时 run 状态，对象存储负责 artifact。

### 12.3 扩展性参数

LangChain 文档提到 Agent Server 写负载来自 run、checkpoint、thread、assistant 等创建，queue worker 并发由 worker 数和 `N_JOBS_PER_WORKER` 决定。平台应按任务类型配置：

- LLM/IO 密集 agent：较高 `N_JOBS_PER_WORKER`。
- Ghidra/Joern/EMBA/QEMU CPU/内存密集任务：较低并发，并通过专用 worker 池调度。
- checkpoint 策略：标准分析使用默认异步 checkpoint；日志密集工具节点只保存 artifact 引用；最终报告可使用 exit durability 降低写放大。

## 13. 测试与验收

### 13.1 单元测试

- State reducer、router、policy engine、tool adapter 参数校验。
- Artifact normalizer：objdump、jadx、binwalk、joern、emba 输出解析。
- Finding dedup 与证据关联。

### 13.2 集成测试样本

- ELF hello + 危险函数样本。
- PE imports 样本。
- Mach-O 基础样本。
- APK demo with exported component。
- 小型 OpenWrt rootfs 或测试固件。
- CTF toy pwn/reverse。

### 13.3 E2E 验收

- 上传样本后 30 秒内完成 triage。
- 工具失败不导致整体分析卡死，能降级并产出可解释失败原因。
- 固件标准流程能产出 rootfs tree、服务列表、至少一个静态 finding。
- interrupt 审批后 run 能恢复。
- 从 checkpoint 分支后新 run 不污染原 run。
- 最终报告中每个高危 finding 至少有一个 evidence artifact。

## 14. 并行开发计划

### Backend Team A：平台 API

- 建立 `apps/audit-api`。
- 实现 project/sample/analysis/artifact/finding/report 数据模型。
- 实现 OpenAPI 和 mock event stream。
- 对接 Postgres、Redis、对象存储。

### Backend Team B：LangGraph agents

- 建立 `apps/audit-agents`。
- 定义 `AuditState`、root graph、scenario subgraphs。
- 实现 supervisor、triage、report、watchdog。
- 接入 checkpoint、interrupt、streaming。

### Backend Team C：工具 worker

- 建立 `apps/audit-workers`。
- 实现 binutils、jadx、binwalk/unblob、Ghidra headless adapter。
- 实现 tool execution DB record 和 artifact normalizer。
- 为 Joern、EMBA、QEMU 预留接口。

### Backend Team D：安全与部署

- 容器沙箱、网络策略、资源限制。
- 审计日志、RBAC、secret redaction。
- Docker Compose/Kubernetes manifests。
- Worker 池和队列隔离。

### Frontend 并行接口

- 按 `binary-audit-platform-frontend-blueprint.md` 的 API contract 开发 mock UI。
- 后端 M0 提供 OpenAPI 后，前端生成类型并替换 mock。
- SSE event schema 必须由前后端共同冻结。

## 15. 首批 MVP 范围

建议 MVP 不一次性实现所有深度能力，先实现：

- 样本上传、格式识别、analysis/run/event/artifact/finding/report 基础闭环。
- ELF/PE/APK/固件四类样本入口。
- 工具接入：binutils、jadx、binwalk/unblob、Ghidra headless。
- LangGraph 多 agent：supervisor、triage、reverse、firmware-lite、mobile-lite、report、watchdog。
- interrupt：动态执行/模拟审批。
- 固件：解包、rootfs tree、基础静态风险；EMBA 在 MVP 中实现异步任务接口、权限审批和 artifact 导入，深度模拟放入 M2/M3。
- 报告：Markdown/HTML 导出。

## 16. 与 LangGraph/LangChain 文档的对应关系

- Agent Server `/mcp` 使用 Streamable HTTP，可把 LangGraph agents 暴露为 MCP tools，也可让外部 MCP 客户端调用平台能力。
- LangGraph checkpoint 按 super-step 保存 state，可用于恢复、分支和时间旅行。
- Interrupt 支撑 human-in-the-loop，适合危险工具执行和动态分析审批。
- Agent Server scale 文档强调 API server、queue worker、Redis、Postgres 的职责，以及并发参数对吞吐和资源的影响。

参考：

- https://docs.langchain.com/langsmith/server-mcp
- https://docs.langchain.com/langsmith/agent-server-scale
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/multi-agent
