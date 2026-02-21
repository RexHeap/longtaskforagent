## 竞品分析：long-task-agent vs superpowers

### 当前项目的独有优势（保留）

| 优势                         | 说明                                                        |
| ---------------------------- | ----------------------------------------------------------- |
| **结构化 feature-list.json** | JSON 格式防止模型腐蚀，含依赖追踪、优先级、不可变验证步骤   |
| **自动化脚手架**             | `init_project.py` + `validate_features.py` 一键初始化和验证 |
| **Chrome DevTools MCP 测试** | UI 功能强制使用 snapshot/click/fill/screenshot 验证         |
| **跨平台引导脚本**           | init.sh + init.ps1 双平台支持                               |
| **单特性/周期约束**          | 防止上下文耗尽的核心策略                                    |
| **Examples 目录**            | 每个用户可见特性附带可运行示例                              |
| **两阶段架构**               | Initializer + Worker 会话分离，持久化状态桥接               |

------

### GAP 分析（18 项差距 → 细化需求）

#### 一、工作流缺失（高优先级）

**GAP-1: 缺少头脑风暴/设计阶段**

- **现状**：从需求文档直接跳到特性分解，无设计评审

- **superpowers**：强制 brainstorming 阶段，硬门控禁止跳过，提出 2-3 种方案及权衡，逐段审批后输出设计文档到 `docs/plans/`

- 需求

  ：

  - R1.1: 新增 brainstorming 阶段，在 Initializer 之前执行
  - R1.2: 强制提出 2-3 种实现方案及优劣对比
  - R1.3: 用户逐段审批设计，审批后输出设计文档至 `docs/plans/YYYY-MM-DD-<topic>-design.md`
  - R1.4: 硬门控 — 未通过设计审批不得进入实现阶段

**GAP-2: 缺少结构化实现计划**

- **现状**：feature-list.json 仅是任务清单，无详细实现步骤

- **superpowers**：writing-plans 技能生成 2-5 分钟粒度的任务计划，含精确文件路径、完整代码、验证步骤

- 需求

  ：

  - R2.1: 新增 plan-writing 阶段，将每个 feature 拆解为可执行步骤
  - R2.2: 每步包含：精确文件路径、预期代码变更、验证命令及预期输出
  - R2.3: 计划假设执行者零上下文（适配子代理场景）
  - R2.4: 计划持久化至 `docs/plans/YYYY-MM-DD-<feature-name>.md`

**GAP-3: 缺少 EnterPlanMode 拦截机制**

- **现状**：无实现前的强制设计门控

- **superpowers**：所有实现任务必须先触发 EnterPlanMode，防止跳过设计直接编码

- 需求

  ：

  - R3.1: Worker 阶段选择新 feature 后，强制进入 plan mode 审查实现策略
  - R3.2: 用户批准计划后才可进入 TDD Red 阶段

------

#### 二、代码质量保障缺失（高优先级）

**GAP-4: 缺少代码审查流程**

- **现状**：无专门的代码审查步骤

- **superpowers**：两阶段审查（规格合规性 → 代码质量），专用 code-reviewer agent，关键/重要/建议三级分类

- 需求

  ：

  - R4.1: Worker 每完成一个 feature 后，触发代码审查
  - R4.2: 两阶段审查：先验证需求合规，再评估代码质量
  - R4.3: 创建 `agents/code-reviewer.md` 定义审查者角色和职责
  - R4.4: 审查反馈分级：Critical（立即修复）、Important（继续前修复）、Minor（后续处理）

**GAP-5: 缺少验证前置强制**

- **现状**：要求测试通过但无形式化的"证据先于声明"机制

- **superpowers**：Iron Law — 无新鲜验证证据不得声称完成，标记"should/probably/seems to"为红旗

- 需求

  ：

  - R5.1: 标记 feature 为 "passing" 前，必须附带实际验证输出（测试日志/截图）
  - R5.2: 文档中增加"验证铁律"：识别证据 → 执行命令 → 读取输出 → 确认 → 才可声明
  - R5.3: 定义红旗词汇列表（"should pass"、"probably works"等），触发时强制重新验证

**GAP-6: 缺少系统化调试流程**

- **现状**：无形式化的调试方法论

- **superpowers**：四阶段调试（根因调查 → 模式分析 → 假设检验 → 实现修复），含辅助技术（根因追踪、纵深防御、条件等待、污染查找脚本）

- 需求

  ：

  - R6.1: 新增 `references/systematic-debugging.md` 调试指南
  - R6.2: 定义四阶段调试流程：根因调查 → 模式分析 → 假设检验 → 实现
  - R6.3: Iron Law — 未调查根因不得直接修复
  - R6.4: 增加辅助脚本（如 find-polluter.sh 测试污染二分法）

------

#### 三、子代理与并行能力缺失（中优先级）

**GAP-7: 缺少子代理驱动开发**

- **现状**：单代理顺序执行

- **superpowers**：每个任务分发独立子代理执行，防止上下文污染，带审查循环

- 需求

  ：

  - R7.1: 支持 subagent-driven 模式 — 每个 feature 可分发给子代理
  - R7.2: 创建提示模板：implementer-prompt.md、spec-reviewer-prompt.md、code-quality-reviewer-prompt.md
  - R7.3: 子代理接收完整任务文本（非文件引用），确保独立执行
  - R7.4: 审查循环：审查不通过 → 子代理修复 → 重新审查

**GAP-8: 缺少并行代理调度**

- **现状**：无并行执行能力

- **superpowers**：识别独立域后并行分发代理，汇总结果后冲突检测

- 需求

  ：

  - R8.1: 支持识别无依赖 feature 并行调度
  - R8.2: 并行结果汇总、冲突检测、全量测试
  - R8.3: 文档化并行调度的适用场景和约束

------

#### 四、工作区管理缺失（中优先级）

**GAP-9: 缺少 Git Worktree 隔离**

- **现状**：直接在项目目录工作，无隔离

- **superpowers**：强制 worktree 隔离，自动检测项目配置，基线测试验证

- 需求

  ：

  - R9.1: 新增 worktree 支持，每个 feature 在隔离分支开发
  - R9.2: 自动检测 .worktrees/worktrees 目录偏好
  - R9.3: 创建 worktree 后运行基线测试确认环境干净
  - R9.4: 确保 worktree 目录在 .gitignore 中

**GAP-10: 缺少分支完成工作流**

- **现状**：仅 git commit，无结构化的合并/PR 流程

- **superpowers**：四选项完成流程（本地合并/推送创建PR/保留/丢弃），含测试验证和 worktree 清理

- 需求

  ：

  - R10.1: feature 完成后提供结构化选项：merge / push+PR / keep / discard
  - R10.2: 合并前强制验证所有测试通过
  - R10.3: 选择丢弃时需二次确认（输入"discard"）
  - R10.4: 自动清理 worktree（合并或丢弃后）

------

#### 五、自动化与可扩展性缺失（中优先级）

**GAP-11: 缺少 Hooks/会话启动自动化**

- **现状**：Worker 手动读取进度文件进行上下文恢复

- **superpowers**：hooks/session-start.sh 在每次会话启动/恢复/清除/压缩时自动注入上下文

- 需求

  ：

  - R11.1: 创建 `hooks/hooks.json` 配置 SessionStart 钩子
  - R11.2: 编写 session-start 脚本，自动注入 long-task-guide.md 内容
  - R11.3: 支持 session resume/clear/compact 事件触发

**GAP-12: 缺少插件/技能发现系统**

- **现状**：单一 SKILL.md 入口

- **superpowers**：完整插件系统，技能发现、前置元数据、技能遮蔽（个人>项目>默认）

- 需求

  ：

  - R12.1: 支持 YAML frontmatter 声明技能名和触发条件
  - R12.2: 支持技能优先级遮蔽（项目级 > 用户级 > 默认）
  - R12.3: 考虑 .claude-plugin 插件打包格式

**GAP-13: 缺少自动更新机制**

- **现状**：静态技能，无版本检查

- **superpowers**：Git-based 自动更新检查

- 需求

  ：

  - R13.1: 增加版本号管理
  - R13.2: 技能启动时检查远程仓库是否有新版本

------

#### 六、防御性文档缺失（低优先级）

**GAP-14: 缺少红旗/反合理化表**

- **现状**：列出了反模式但无针对 agent 行为的"红旗"检测

- **superpowers**：12 条文档化的 agent 跳过流程的合理化借口，如"This Is Too Simple"、"I'll Test After"

- 需求

  ：

  - R14.1: 创建红旗表，列举 agent 跳过 TDD/设计/审查的常见借口
  - R14.2: 每条红旗附带正确应对方式
  - R14.3: 在 SKILL.md 和 long-task-guide.md 中引用红旗表

**GAP-15: 缺少测试反模式参考**

- **现状**：反模式散布在文档中

- **superpowers**：专门的 testing-anti-patterns.md 集中管理

- 需求

  ：

  - R15.1: 创建 `references/testing-anti-patterns.md` 集中文档
  - R15.2: 覆盖：不要测试 mock 行为、不要为测试添加生产方法、不要无脑 mock

**GAP-16: 缺少技能自身的集成测试**

- **现状**：仅有 validate_features.py

- **superpowers**：完整集成测试框架（真实 Claude 会话测试、token 分析、JSONL 会话转录分析）

- 需求

  ：

  - R16.1: 创建 `tests/` 目录，增加技能工作流集成测试
  - R16.2: 增加 token 用量分析工具
  - R16.3: 增加会话转录验证（验证技能调用、subagent 分发、todo 使用等）

------

#### 七、用户体验缺失（低优先级）

**GAP-17: 缺少用户快捷命令**

- **现状**：仅有 long-task-agent 单一入口

- **superpowers**：/brainstorm、/write-plan、/execute-plan 快捷命令

- 需求

  ：

  - R17.1: 新增快捷命令 `/long-task:init`（初始化）
  - R17.2: 新增快捷命令 `/long-task:work`（启动 Worker 周期）
  - R17.3: 新增快捷命令 `/long-task:status`（查看进度摘要）

**GAP-18: 缺少多平台支持**

- **现状**：仅支持 Claude Code

- **superpowers**：支持 Claude Code + Codex + OpenCode

- 需求

  ：

  - R18.1: 评估 Codex 适配可行性（原生技能发现 via symlink）
  - R18.2: 评估 OpenCode 适配可行性（JS 插件系统）
  - R18.3: 创建平台适配文档 `docs/README.<platform>.md`

------

### 需求优先级汇总

| 优先级        | 需求编号    | 主题               |
| ------------- | ----------- | ------------------ |
| **P0 - 高**   | R1.1-R1.4   | 头脑风暴/设计阶段  |
| **P0 - 高**   | R4.1-R4.4   | 代码审查流程       |
| **P0 - 高**   | R5.1-R5.3   | 验证前置强制       |
| **P0 - 高**   | R6.1-R6.4   | 系统化调试流程     |
| **P1 - 中**   | R2.1-R2.4   | 结构化实现计划     |
| **P1 - 中**   | R3.1-R3.2   | EnterPlanMode 门控 |
| **P1 - 中**   | R7.1-R7.4   | 子代理驱动开发     |
| **P1 - 中**   | R9.1-R9.4   | Git Worktree 隔离  |
| **P1 - 中**   | R10.1-R10.4 | 分支完成工作流     |
| **P1 - 中**   | R11.1-R11.3 | Hooks 自动化       |
| **P2 - 低**   | R8.1-R8.3   | 并行代理调度       |
| **P2 - 低**   | R12.1-R12.3 | 插件发现系统       |
| **P2 - 低**   | R13.1-R13.2 | 自动更新机制       |
| **P2 - 低**   | R14.1-R14.3 | 红旗/反合理化表    |
| **P2 - 低**   | R15.1-R15.2 | 测试反模式参考     |
| **P2 - 低**   | R16.1-R16.3 | 技能集成测试       |
| **P2 - 低**   | R17.1-R17.3 | 用户快捷命令       |
| **P3 - 远期** | R18.1-R18.3 | 多平台支持         |

共 **18 个 GAP，48 条细化需求**。建议按 P0 → P1 → P2 → P3 分批实施