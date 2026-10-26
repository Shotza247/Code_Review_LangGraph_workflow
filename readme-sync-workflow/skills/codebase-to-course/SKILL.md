---
name: codebase-to-course
description: Turn a codebase into a course-style planning draft (audience, prerequisites, modules, lessons, exercises, capstone) that makes the project easy to learn and reproduce. Use whenever a workflow or person wants to enhance a README with a learning path, onboard newcomers to a repository, or convert a codebase into a curriculum, even if they do not say "course".
---

# Codebase to Course

Produce a planning draft that teaches a newcomer how the codebase works, in the order they should learn it.

## Inputs you receive
- File tree.
- Factual codebase summary.
- README gap report.
- Static code review findings, strengths, and test gaps.
- Reproducibility assessment with documented setup, run, test, configuration, and verification evidence.
- Code-understanding assessment with main flow, components, data flow, and unknowns.

## Steps
1. Identify the audience (who would reuse or extend this project) and state it in one line.
2. Set the difficulty level from the evidence:
   - Beginner when prerequisites and architecture are simple and reproducibility is documented.
   - Intermediate when setup has gaps, multiple components exist, or test coverage is unclear.
   - Advanced when architecture, operations, or review findings require deeper investigation.
3. List prerequisites: tools, language versions, and concepts the code assumes (only those evidenced in the assessments).
4. Write 3 to 6 learning objectives, each starting with a verb ("Run...", "Explain...", "Review...", "Extend...").
5. Group the code into 4 to 8 modules ordered from setup, to architecture, to runtime flow, to review/test gaps, to extensions. For each module give:
   - Goal (one sentence)
   - Files to read (must exist in the file tree)
   - Key concepts
   - Hands-on exercise
   - Checkpoint (how the learner knows they succeeded)
   - Difficulty (Beginner, Intermediate, or Advanced)
6. Add a capstone exercise that exercises the full flow end to end.
7. Finish with a reproducibility checklist built from high-severity README gaps and reproducibility gaps.
8. Add a review checklist built from static code review findings and test gaps.

## Rules
- Never cite a file that is not in the file tree.
- Never invent commands, versions, execution results, or features. Mark unknowns as "TODO: confirm".
- Treat setup, run, test, and verification commands as documented evidence unless explicitly marked as executed by the workflow.
- Use review findings and test gaps to tune course difficulty and module order.
- Keep every module short enough to finish in one sitting.
- Follow the structure in templates/course_plan.md.
