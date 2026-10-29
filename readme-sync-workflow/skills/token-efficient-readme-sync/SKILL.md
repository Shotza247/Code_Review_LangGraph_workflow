---
noteId: "7c12f5a0d31411f1a2932b1a69e73653"
tags: []
name: "token-efficient-readme-sync"
description: "Keep README synchronization workflows accurate while minimizing LLM input and output tokens. Use when changing prompts, context selection, map-reduce analysis, or node chains."

---

# Token-efficient README synchronization

## Principles

- Prefer deterministic code over an LLM call for routing, formatting, filtering, validation, and file operations.
- Run only the branch the user selected. Do not generate both a course plan and a guide.
- Pass one bounded summary of evidence downstream instead of repeating source files or the full repository tree.
- Keep each prompt task-specific; include only fields that node needs.
- Reuse a single compact assessment to inform later nodes rather than asking separate models to repeat the same analysis.
- Use LangChain LCEL to compose prompt rendering and model invocation consistently. Chaining itself does not reduce tokens; bounded inputs and avoiding duplicate calls do.
- Bound outputs with concise formats and the configured model output limit. Avoid examples and explanations unless required by the artifact.
- Preserve evidence and uncertainty. Never shorten text in a way that changes a command, file path, severity, or key technical fact.
- Log lengths and state summaries, not full prompts, source files, or generated documents.

## Workflow checklist

1. Select relevant files and cap file, batch, tree, and summary sizes before prompting.
2. Map batches once, reduce them into a factual summary, and produce one consolidated assessment.
3. Use a LangGraph conditional edge to route to exactly one post-assessment output.
4. Keep each output artifact concise and avoid a second LLM call for indexing or formatting.
5. Test that the selected branch alone runs and that shared state carries the assessment artifacts forward.
