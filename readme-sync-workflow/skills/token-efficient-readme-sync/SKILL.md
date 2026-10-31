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
- Draft the evidence-based README before pausing for a selected learning format; pass that bounded draft plus compact evidence to exactly one selected branch.
- Route resumes using an explicit completion/draft state, never truthiness of generated prose such as a code summary.
- Insert the selected artifact link deterministically after generation rather than spending another model call.
- If an intermediate summary is empty, fall back to mapped evidence or the bounded file tree and report the fallback.
- Prefer deterministic artifact checks before considering any additional LLM reviewer call.
- Load shared and format-specific learning skills lazily inside only the selected branch; inject their instructions into that branch's single artifact-generation prompt.
- Skills are local Markdown instructions, not independent LLM or tool calls. Do not send the token-efficiency guidance itself to the model.
- Use LangChain LCEL to compose prompt rendering and model invocation consistently. Chaining itself does not reduce tokens; bounded inputs and avoiding duplicate calls do.
- Bound outputs with concise formats and the configured model output limit. Avoid examples and explanations unless required by the artifact.
- Preserve evidence and uncertainty. Never shorten text in a way that changes a command, file path, severity, or key technical fact.
- Log lengths and state summaries, not full prompts, source files, or generated documents.
- Distinguish request-count estimates from measured token usage; do not claim exact token savings unless provider usage is captured and compared.

## Workflow checklist

1. Select relevant files and cap file, batch, tree, and summary sizes before prompting.
2. Map batches once, reduce them into a factual summary, and produce one consolidated assessment.
3. Generate the README draft, then pause with an explicit assessment-complete state.
4. Resume directly into the user's selected output branch without repeating repository reads or assessment.
5. Keep each output artifact concise and avoid a second LLM call for indexing, formatting, or link insertion.
6. Test that empty summaries do not trigger a restart, only the selected branch runs, and state carries the README and assessment forward.
7. Verify the selected skill instructions appear in the selected prompt and the unselected mode is neither called nor loaded.
