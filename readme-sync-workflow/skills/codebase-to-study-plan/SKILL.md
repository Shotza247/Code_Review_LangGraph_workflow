---
noteId: "3e5c1520d55311f191fb873ee259bc0b"
tags: []
name: "codebase-to-study-plan"
description: "Create a concise, evidence-based step-by-step study plan. The workflow loads this with the shared codebase-to-course skill only when the step-by-step format is selected."

---

# Codebase to Study Plan

Create a practical learning sequence. These mode-specific requirements complement the shared `codebase-to-course` skill.

## Requirements

- Address a newcomer who wants to understand and, where evidence permits, reproduce the project.
- Give 5 to 8 consecutively numbered steps. Each step has one concrete action and one observable checkpoint; label them `Action:` and `Checkpoint:`.
- Start with repository orientation and setup evidence, then progress through the main code flow, verification, and a small review or extension task.
- Use the README draft for orientation. Treat the code summary, file tree, and structured assessment as authoritative for commands, paths, and technical details.
- Cite only file paths present in the repository evidence.
- Mark missing facts as `TODO: confirm`; never invent a command, version, test result, or feature.
- Use code-review findings and reproducibility gaps to identify useful cautions and exercises.
- Keep the complete plan under 500 words and avoid assumed study durations.
