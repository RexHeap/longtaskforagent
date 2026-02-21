---
name: long-task:status
description: Show progress summary for the current long-task project. Use to check feature completion status.
disable-model-invocation: true
---

To check the status of a long-task project:

1. Read `feature-list.json` to see passing/failing features
2. Read `task-progress.md` to see session history
3. Run `python scripts/validate_features.py feature-list.json` to validate

Use the Skill tool to invoke `long-task-agent` or read these files directly.
