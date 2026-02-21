# Plan: 架构设计阶段支持自定义设计文档模板

## Context

当前 brainstorming 阶段的 Step 5（Write Design Document）使用硬编码的 markdown 模板结构输出设计文档。用户需要能够指定一个外部架构设计文档规范文件（模板），让设计文档按照指定范本格式输出。若未指定模板则保持现有默认行为。

## 方案

### 模板发现机制（优先级从高到低）

| 方式             | 说明                                                         |
| ---------------- | ------------------------------------------------------------ |
| 用户显式指定     | 用户告知模板路径，如 "使用 `path/to/template.md` 作为设计模板" |
| 约定位置自动检测 | 检查项目目录下 `docs/templates/design-template.md` 是否存在，存在则确认使用 |
| 默认模板         | 无模板指定时，使用当前内置模板（无破坏性变更）               |

### 模板格式

标准 markdown 文件，标题结构定义输出格式：

- H1 (`#`) — 文档标题模式（可选）
- H2 (`##`) — 主要章节（至少一个）
- H3 (`###`) — 子章节（可选）
- 标题下正文 — 作为填写指导，agent 用实际内容替换

### 模板校验

- 必须是 `.md` 文件
- 必须包含至少一个 `## `标题
- 校验失败则警告用户并提供回退到默认模板的选项

## 修改文件清单

### 1. `long-task-agent/references/brainstorming.md`（主要改动）

**Step 1 (Explore Context)** — 在第 4 项后新增第 5 项：模板发现

- 检查用户是否指定了模板路径
- 检查 `docs/templates/design-template.md` 是否存在
- 校验模板有效性
- 无模板则继续使用默认

**Step 5 (Write Design Document)** — 改为条件分支结构：

- 有自定义模板时：保留模板标题结构，填充审批通过的设计内容，添加元数据（Date/Status/Template）
- 无自定义模板时：保持现有默认模板不变

**文件末尾** — 新增 "Design Template Reference" 章节：

- 模板定义、指定方式表格、校验规则、映射行为说明

### 2. `long-task-agent/SKILL.md`（Phase 0 描述更新）

- Step 1: 添加 "; check for design template (user-specified path or `docs/templates/design-template.md`)"
- Step 5: 添加 "using custom template if provided"

### 3. `long-task-agent/references/architecture.md`（一致性更新）

- Step 1: 添加 "; detect design template"
- Step 5: 添加 "(uses custom template if provided)"

### 4. `CLAUDE.md`（项目说明更新）

- 在 Brainstorming & Design 段落中新增一行：支持自定义设计模板

### 5. `long-task-agent/commands/init.md`（用户指引更新）

- 添加可选步骤：准备设计模板文件

## 不需要修改的文件

- `scripts/init_project.py` — 模板发现在对话中完成，不影响项目脚手架
- `feature-list.json` schema — 模板影响设计文档格式，不影响特性分解
- 测试文件 — 本次是文档/提示词变更，无代码逻辑新增

## 验证方式

1. 阅读修改后的 `brainstorming.md`，确认 Step 1 包含模板发现逻辑、Step 5 包含条件分支、末尾有模板参考章节
2. 阅读 `SKILL.md` Phase 0 步骤描述，确认提到模板支持
3. 阅读 `architecture.md` 确认一致性
4. 阅读 `CLAUDE.md` 确认提到模板支持
5. 阅读 `commands/init.md` 确认包含可选模板步骤