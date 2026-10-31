---
noteId: "7c3d6100d31411f1a2932b1a69e73653"
tags: []
name: "codebase-to-interactive-course"
description: "Create a concise self-guided interactive course. The workflow loads this with the shared codebase-to-course skill only when the interactive format is selected."

---

# Codebase to interactive course

Return one Markdown course source that the workflow can split deterministically into an index and lesson files. Do not request extra model calls or unrelated artifacts.

## Inputs

- README draft for orientation, file tree, and code summary.
- README gaps, static code review, reproducibility assessment, and code-understanding assessment.

## Requirements

- State audience, evidence-based difficulty, and prerequisites.
- Provide a linked table of contents with 3 to 5 lessons and a `## Capstone` section.
- Order lessons from setup and repository orientation through architecture, execution/testing, and a small extension.
- Every lesson includes: goal, files to read (only paths in the supplied tree), a short hands-on exercise, and a concrete checkpoint.
- Use review findings and reproducibility gaps to set lesson difficulty and exercises.
- Treat the assessment and code summary as the technical source of truth; the README draft is orientation only.
- Mark missing evidence as `TODO: confirm`; do not invent commands, test results, or repository facts.
- Keep each lesson concise. Each exercise should be completable in one sitting.
- End with a capstone and a short reproducibility/review checklist.
