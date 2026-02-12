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
   - **Worker（后续每个会话）**：按"定向 → 引导 → 实现 → 持久化"四步循环，每次只做一个 feature
2. **持久化状态桥接**：通过 `feature-list.json`、`task-progress.md`、`init.sh/ps1`、Git 历史四个持久化产物在会话间传递上下文，避免新会话浪费 token 重新发现项目状态
3. **严格约束防止失败**：
   - Feature 状态只有 `failing` / `passing`，不允许模糊中间态
   - 验证步骤一旦创建不可修改，防止降低标准
   - 每个会话只做一个 feature，防止上下文耗尽
   - 必须实际验证通过才能标记为 passing
4. **输入要求**：需求文档 + 设计文档（用户提前准备好）



## 改进方案总结

### 核心改动：`/clear` 后自动接续工作



```
┌─── Worker Cycle ───┐
│ 1. Orient          │  ← 读 task-progress.md + feature-list.json + git log
│ 2. Bootstrap       │  ← 运行 init.sh/ps1，烟雾测试
│ 3. Implement       │  ← 做 1 个 feature，验证，标记 passing
│ 4. Persist         │  ← git commit + 更新进度文件
│ 5. /clear          │  ← 清空上下文
└────────┬───────────┘
         │
  CLAUDE.md 自动加载（Claude Code 原生行为）
         │
  "Read long-task-guide.md" ← 引导指令
         │
┌─── Worker Cycle ───┐
│     重复...         │
└────────────────────┘
```

### 关键设计

| 机制                     | 说明                                                         |
| ------------------------ | ------------------------------------------------------------ |
| **`long-task-guide.md`** | 独立文件，存放完整 Worker 工作流指南，不会被 Claude Code 覆盖 |
| **`CLAUDE.md` 追加引用** | 仅追加一个带 `<!-- long-task-agent -->` 标记的引用块，幂等操作，不覆盖已有内容 |
| **`/clear` 后自动发现**  | Claude Code 启动时自动读取 `CLAUDE.md` → 发现引用 → 读取 `long-task-guide.md` → 按流程领取下一个 task |
| **`feature-list.json`**  | JSON 格式防止模型篡改，只有 `failing`/`passing` 两种状态     |
| **`task-progress.md`**   | 每个 session 追加日志，帮助下一个 session 快速了解上下文     |