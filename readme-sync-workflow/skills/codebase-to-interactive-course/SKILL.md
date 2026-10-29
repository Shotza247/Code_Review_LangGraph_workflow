---
noteId: "7c3d6100d31411f1a2932b1a69e73653"
tags: []
name: "codebase-to-interactive-course"
description: "Turn repository assessment artifacts into a concise self-guided interactive course with lesson navigation, exercises, and checkpoints. Use when the user selects the interactive course option."

---

# Codebase to interactive course

Create one Markdown course artifact that a learner can navigate independently. Do not create a tutor, application, or additional LLM-generated files.

## Inputs

- File tree and code summary.
- README gaps, static code review, reproducibility assessment, and code-understanding assessment.

## Requirements

- State audience, evidence-based difficulty, and prerequisites.
- Provide a linked table of contents with 3 to 5 lessons.
- Order lessons from setup and repository orientation through architecture, execution/testing, and a small extension.
- Every lesson includes: goal, files to read (only paths in the supplied tree), a short hands-on exercise, and a concrete checkpoint.
- Use review findings and reproducibility gaps to set lesson difficulty and exercises.
- Mark missing evidence as `TODO: confirm`; do not invent commands, test results, or repository facts.
- Keep each lesson concise. Each exercise should be completable in one sitting.
- End with a capstone and a short reproducibility/review checklist.
