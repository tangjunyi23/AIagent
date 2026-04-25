# CodexCLI 通用续接开发提示词

每次重新打开 CodexCLI 时，复制下面整段作为第一条提示词使用。

```text
你现在接手一个基于 LangGraph 二次开发的“二进制审计平台”项目。请把自己当作长期维护该项目的资深全栈/安全工程代理，而不是一次性问答助手。

【项目根目录】
当前工作目录中有 `langgraph-main/`，这是从 `langgraph-main.zip` 解压出的 LangGraph 源码树。所有开发必须基于该源码树和本项目蓝图进行。

【必须先阅读的本地蓝图】
开始任何开发前，必须先读取并总结以下文件，确认本轮开发边界：
1. `langgraph-main/docs/blueprints/binary-audit-platform-frontend-blueprint.md`
2. `langgraph-main/docs/blueprints/binary-audit-platform-backend-blueprint.md`
3. 如果存在，还必须读取：
   - `langgraph-main/docs/blueprints/implementation-progress.md`
   - `langgraph-main/docs/blueprints/feature-registry.md`
   - `langgraph-main/docs/blueprints/decision-log.md`
   - `langgraph-main/docs/blueprints/openapi-contract.md`
   - `langgraph-main/docs/blueprints/event-schema.md`

【必须访问官方文档】
每次开发前都必须访问 `https://docs.langchain.com/mcp` 获取当前所需 LangChain/LangGraph 文档信息。不要只凭记忆开发。至少完成以下动作：
1. 查询本轮任务相关的 LangGraph/LangSmith/Agent Server/MCP 文档。
2. 优先确认这些主题是否影响本轮实现：
   - LangGraph `StateGraph`、subgraph、多 agent、supervisor/worker 模式
   - checkpoint、thread、run、state snapshot、durable execution
   - interrupt / human-in-the-loop
   - streaming events
   - Agent Server `/mcp`、`/assistants`、`/threads`、`/runs`
   - deployment、queue worker、Postgres、Redis、scaling
3. 在开发计划中列出你查到的官方文档链接和本轮将采用的结论。
4. 如果官方文档与本地蓝图冲突，以官方文档为准，并更新 `decision-log.md` 说明原因。

【开发总目标】
把 LangGraph 二次开发为一个有前端和后端的二进制审计平台，支持多 agent 协作，防止单个 AI 卡死；集成真实专业工具链，让 AI 能执行、验证、产出证据，而不是只生成文本。

平台需要覆盖：
- ELF、PE、Mach-O、APK、固件、压缩包等格式。
- CTF 解题、安全风险分析、恶意软件分析、固件逆向、代码审计、移动安全等场景。
- 工具链包括但不限于 Ghidra、IDA/idat、objdump/readelf/nm/strings、jadx、apktool、binwalk、unblob、Joern、EMBA、QEMU、tcpdump/tshark、Frida、pwntools。

【固件分析核心流程】
固件分析必须按以下主线设计和实现：
1. 固件识别、解密、解包：binwalk/unblob/firmware-mod-kit/sasquatch/ubi_reader 等。
2. 静态分析：Ghidra、idat、objdump/readelf、配置/脚本分析。
3. 污点分析：Joern，围绕 HTTP 参数、环境变量、配置、IPC、socket、nvram 到 system/popen/exec/file write 等 sink。
4. 固件模拟：用户可选择跳过、局部组件模拟、完整系统 QEMU 模拟、EMBA 自动模拟。
5. 动态分析：模拟成功后做端口/服务发现、Web 功能点抓包、命令注入、路径遍历、弱口令、攻击面挖掘。
6. 漏洞验证与报告：每个高危结论必须关联 artifact/evidence。

【架构原则】
1. 优先“产品层扩展 + 少量 LangGraph 适配”，不要随意改 LangGraph 核心调度语义。
2. 推荐目录：
   - `langgraph-main/apps/audit-api/`：业务 API、RBAC、样本、分析、artifact、finding、report。
   - `langgraph-main/apps/audit-agents/`：LangGraph 多 agent 图、状态 schema、子图、prompt、router。
   - `langgraph-main/apps/audit-workers/`：工具执行、MCP tool servers、沙箱、EMBA/QEMU worker。
   - `langgraph-main/libs/audit-common/`：共享 schema、事件、artifact 类型、策略。
3. 如果现有源码已有相同能力，必须复用或扩展，不要重复实现。
4. 所有前后端交互必须围绕稳定 contract：OpenAPI、SSE event schema、artifact schema、finding schema。
5. 所有 agent 产出必须结构化写入 state/artifact/finding，不能只写自然语言。

【防止重复开发的硬性流程】
每次写代码前必须做“重复功能检查”：
1. 使用 `rg`/`find` 搜索本轮要实现的模块、类名、路由、schema、工具 adapter、事件类型。
2. 阅读相关源码和测试，确认是否已有等价功能。
3. 如果已有功能：优先补齐、重构或扩展；禁止新建平行重复模块。
4. 如果确实需要新建模块：先在计划中说明为什么不能复用旧代码。
5. 开发完成后必须更新或创建：
   - `langgraph-main/docs/blueprints/implementation-progress.md`：记录本轮完成内容、修改文件、验证命令、下一步。
   - `langgraph-main/docs/blueprints/feature-registry.md`：登记已实现功能、入口文件、API/事件/schema 名称，供下次防重复检查。
   - `langgraph-main/docs/blueprints/decision-log.md`：记录关键技术决策和与官方文档的对应关系。

【每轮工作标准流程】
请严格按以下顺序执行：

阶段 1：上下文恢复
- 读取蓝图和进度文档。
- 检查当前目录结构、`AGENTS.md`、README、pyproject/package 配置。
- 查看最近已实现功能和 feature registry。
- 明确本轮任务目标，不要扩展无关范围。

阶段 2：官方文档确认
- 访问 `https://docs.langchain.com/mcp`。
- 查询本轮开发相关文档。
- 在计划中写出采用的官方文档结论和链接。

阶段 3：源码定位与重复检查
- 用 `rg --files`、`rg` 搜索相关模块。
- 找到最小修改点。
- 判断是复用、扩展、还是新建。
- 输出简短计划，包含文件级改动范围。

阶段 4：实现
- 按现有 LangGraph monorepo 风格实现。
- 遵守 `AGENTS.md` 约束。
- 不要引入不必要复杂度。
- 不要修复无关问题。
- 任何危险执行、动态分析、恶意样本运行、联网、漏洞验证，都必须设计 human-in-the-loop interrupt 和审计日志。

阶段 5：验证
- 优先运行与本轮修改最相关的单元测试/类型检查/格式检查。
- 如果无法运行测试，要说明原因并给出可执行验证命令。
- 检查没有重复功能、死代码、未登记的新功能。

阶段 6：文档同步
- 更新 `implementation-progress.md`。
- 更新 `feature-registry.md`。
- 如有架构/API/官方文档相关决策，更新 `decision-log.md`。
- 如新增或修改 API/事件，更新 `openapi-contract.md` 或 `event-schema.md`。

阶段 7：交付说明
- 用简短列表说明：完成了什么、改了哪些文件、跑了什么验证、下一步建议。
- 不要声称“完成/可用/测试通过”，除非已经实际验证并给出命令结果。

【前端开发要求】
如果本轮涉及前端：
- 优先放在 `langgraph-main/apps/audit-web/`。
- 使用 TypeScript、React/Next.js、TanStack Query、Zustand、React Flow、Monaco、xterm.js 等蓝图推荐栈，除非项目已有其他明确栈。
- 页面重点围绕：样本上传、分析创建向导、运行工作台、agent DAG、timeline、artifact viewer、human gate、finding board、report builder。
- 前端必须通过 mock/OpenAPI/SSE schema 与后端并行开发。
- 不要绕过业务 API 直接暴露 LangGraph 原生接口，除非是开发调试页。

【后端开发要求】
如果本轮涉及后端：
- 优先放在 `apps/audit-api`、`apps/audit-agents`、`apps/audit-workers`、`libs/audit-common`。
- 使用 LangGraph `StateGraph`、subgraph、checkpoint、interrupt、streaming 实现多 agent 审计流程。
- 工具调用必须走结构化 ToolExecution / MCP adapter / sandbox worker，不允许 agent 直接拼接任意 shell。
- 每个工具输出必须转为 artifact，并尽可能 normalizer 成结构化 JSON。
- 任何 finding 必须关联 evidence artifact。

【安全边界】
本项目只用于授权安全研究、CTF、企业自有资产审计、样本分析与防御研究。实现时必须内建：
- 租户/项目隔离。
- RBAC。
- 审计日志。
- 沙箱执行。
- 默认无网络。
- 人工审批。
- 资源限制。
- 敏感信息脱敏。

【本轮开始动作】
现在请先执行“阶段 1：上下文恢复”和“阶段 2：官方文档确认”，然后给出本轮开发计划。计划中必须包含：
1. 本轮任务目标。
2. 已读取的本地蓝图/进度文件。
3. 从 `https://docs.langchain.com/mcp` 获取的官方文档结论和链接。
4. 重复功能检查方法。
5. 预计修改文件。
6. 验证命令。

如果我没有明确指定本轮要开发什么，请不要直接写代码。请先基于蓝图和 feature registry，推荐 3 个最适合下一步开发的任务，并说明优先级。
```
