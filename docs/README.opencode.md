# Long-Task Agent — OpenCode Setup

## Overview

long-task-agent can run on OpenCode via its JavaScript plugin system. The core workflow is platform-agnostic; only the plugin wrapper differs.

## Installation

### Option 1: Symlink to Skills Directory

```bash
# Clone the repository
git clone <repo-url> ~/long-task-agent

# Create the skills directory if it doesn't exist
mkdir -p ~/.opencode/skills

# Symlink the skill
ln -s ~/long-task-agent/long-task-agent ~/.opencode/skills/long-task-agent
```

### Option 2: JavaScript Plugin Wrapper

If OpenCode requires a JS plugin entry point, create a minimal wrapper:

```javascript
// opencode-plugin.js
const fs = require('fs');
const path = require('path');

module.exports = {
  name: 'long-task-agent',
  description: 'Execute complex, multi-session software projects that exceed a single context window.',

  getSkillContent() {
    const skillPath = path.join(__dirname, 'long-task-agent', 'SKILL.md');
    return fs.readFileSync(skillPath, 'utf-8');
  }
};
```

## Skill Discovery

OpenCode supports a three-tier skill priority system:
1. **Project-level** skills (`.opencode/skills/` in project root)
2. **Personal** skills (`~/.opencode/skills/`)
3. **Plugin** skills (installed plugins)

long-task-agent can be installed at any tier. Project-level takes highest priority.

## Limitations on OpenCode

- **No hooks system**: The `hooks/` directory is Claude Code-specific. Context injection must be done via OpenCode's plugin lifecycle events.
- **No Skill tool**: Shortcut commands are Claude Code-specific. On OpenCode, invoke by describing the task.
- **Subagent dispatch**: Adapt to OpenCode's native task dispatch mechanism if available.

## Verification

After installation, verify the skill loads by asking OpenCode about available skills or directly requesting a multi-session task.

## Updates

```bash
cd ~/long-task-agent && git pull
```
