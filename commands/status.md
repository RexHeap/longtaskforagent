---
name: long-task:status
description: Show progress summary for the current long-task project.
disable-model-invocation: true
---

To check the status of a long-task project:

1. Read `feature-list.json` to see passing/failing features
2. Read `task-progress.md` to see session history
3. Run `python scripts/validate_features.py feature-list.json` to validate
