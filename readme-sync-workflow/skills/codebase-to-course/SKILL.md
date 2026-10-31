---
name: codebase-to-course
description: Shared evidence and learning-design rules injected into the selected step-by-step study-plan or interactive-course generation prompt.
---

# Shared Codebase Learning Design

This shared skill is loaded only inside the selected learning-output node and is combined with that format's specific skill. It is instruction text for the model prompt, not a separate LLM/tool call or artifact.

## Evidence rules

- Use the README draft for orientation only. Use the code summary, file tree, and structured assessment as the technical source of truth.
- Cite only paths present in the supplied file tree or evidence.
- Do not invent commands, versions, features, test outcomes, or external services.
- Mark missing information as `TODO: confirm`.
- Treat discovered commands as documented evidence, not as commands that the workflow executed.
- Use reproducibility gaps, static review findings, and test gaps to shape practical learner checkpoints.
- Keep all instructions relevant to the selected output format; do not generate the other format.

The longer `templates/course_plan.md` is a reference for a standalone course-planning draft. The application does not send that template to the model or generate that additional artifact.
