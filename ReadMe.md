## Skill 结构总览



```
long-task-agent/
├── SKILL.md                        # 核心指令文件
├── scripts/
│   ├── init_project.py             # 项目脚手架脚本
│   └── validate_features.py        # feature-list.json 校验脚本
└── references/
    └── architecture.md             # 详细架构模式参考
```

## 核心设计思路（源自博文）

该 Skill 将 Anthropic 博文中"长时间运行 Agent"的关键模式落地为可复用的工作流：

1. **两阶段架构**：
   - **Initializer（初始化会话）**：读取需求文档和设计文档，将需求分解为 10-200+ 个可验证的 feature，生成 `feature-list.json`（JSON 格式防止模型误改），创建环境启动脚本和进度日志
   - **Worker（后续每个会话）**：按"定向 → 引导 → TDD Red → TDD Green → TDD Refactor → 验证标记 → 添加示例 → 持久化"循环，每次只做一个 feature
2. **持久化状态桥接**：通过 `feature-list.json`、`task-progress.md`、`RELEASE_NOTES.md`、`examples/`、`init.sh/ps1`、Git 历史六个持久化产物在会话间传递上下文，避免新会话浪费 token 重新发现项目状态
3. **严格 TDD 开发**：
   - 每个 feature 严格遵循 Red→Green→Refactor 流程
   - 先写失败的测试，再写最小实现代码，最后重构
   - 必须所有测试（UT + 功能测试）通过才能标记为 passing
4. **双重验证体系**：
   - **单元测试（UT）**：所有 feature 必须有单元测试
   - **Chrome DevTools MCP 功能测试**：UI 类 feature 必须通过浏览器功能测试（snapshot / click / fill / screenshot）
5. **Release Notes 持续维护**：每次 Git 提交后更新 `RELEASE_NOTES.md`，采用 Keep a Changelog 格式
6. **Feature 示例展示**：
   - 每个用户可见的 feature 完成后，在 `examples/` 目录添加可运行的示例
   - 示例按 feature 颗粒度创建，文件名含 feature ID（如 `01-user-login.py`）
   - 纯基础设施 feature 可选跳过
   - `examples/README.md` 维护示例索引表
7. **严格约束防止失败**：
   - Feature 状态只有 `failing` / `passing`，不允许模糊中间态
   - 验证步骤一旦创建不可修改，防止降低标准
   - 每个会话只做一个 feature，防止上下文耗尽
   - 必须实际验证通过才能标记为 passing
8. **输入要求**：需求文档 + 设计文档（用户提前准备好）



## 改进方案总结

### 核心改动：`/clear` 后自动接续工作



```
┌─── Worker Cycle ──────┐
│ 1. Orient             │  ← 读 task-progress.md + feature-list.json + git log
│ 2. Bootstrap          │  ← 运行 init.sh/ps1，烟雾测试
│ 3. TDD Red            │  ← 先写失败的测试（UT + Chrome DevTools 功能测试）
│ 4. TDD Green          │  ← 写最小实现代码使测试通过
│ 5. TDD Refactor       │  ← 重构，保持测试绿色
│ 6. Verify & Mark      │  ← 全部测试通过后标记 passing
│ 7. Add Examples       │  ← 添加可运行示例展示新功能（按需）
│ 8. Persist            │  ← git commit + 更新进度 + Release Notes
│ 9. /clear             │  ← 清空上下文
└────────┬──────────────┘
         │
  CLAUDE.md 自动加载（Claude Code 原生行为）
         │
  "Read long-task-guide.md" ← 引导指令
         │
┌─── Worker Cycle ──────┐
│     重复...            │
└───────────────────────┘
```

### 关键设计

| 机制                     | 说明                                                         |
| ------------------------ | ------------------------------------------------------------ |
| **`long-task-guide.md`** | 独立文件，存放完整 Worker 工作流指南（含 TDD 流程），不会被 Claude Code 覆盖 |
| **`CLAUDE.md` 追加引用** | 仅追加一个带 `<!-- long-task-agent -->` 标记的引用块，幂等操作，不覆盖已有内容 |
| **`/clear` 后自动发现**  | Claude Code 启动时自动读取 `CLAUDE.md` → 发现引用 → 读取 `long-task-guide.md` → 按流程领取下一个 task |
| **`feature-list.json`**  | JSON 格式防止模型篡改，只有 `failing`/`passing` 两种状态     |
| **`task-progress.md`**   | 每个 session 追加日志，帮助下一个 session 快速了解上下文     |
| **`RELEASE_NOTES.md`**   | 每次 Git 提交后刷新，Keep a Changelog 格式，关联 feature ID   |
| **`examples/`**          | 可运行示例集，每个用户可见的 feature 对应一个示例文件，附 README 索引 |
| **Chrome DevTools MCP**  | UI 功能测试：snapshot / click / fill / screenshot 验证用户交互 |