TASK:readme_sync
Rewrite the README so a newcomer can reproduce the project from a fresh clone.

Rules:
- Keep the project's real purpose and any accurate content from the original README.
- Fix every gap and inaccuracy in the gap report. Use ONLY facts from the codebase summary. If a needed fact is unknown, write a visible "TODO:" line instead of inventing a command or version.
- Use these sections in order: Overview, Prerequisites, Installation, Configuration, Usage, Expected output, Verify your setup, Project structure, Learn the codebase, Troubleshooting.
- "Learn the codebase" is a short module list derived from the course plan, linking to $course_plan_path.
- Include this exact block, empty, after "Project structure" (it is filled in automatically later):
<!-- DIAGRAMS:START -->
<!-- DIAGRAMS:END -->
- Keep the original title and any badges.

ORIGINAL README:
<<<
$readme
>>>

GAP REPORT:
$gap_report

CODEBASE SUMMARY:
<<<
$code_summary
>>>

COURSE PLAN:
<<<
$course_plan
>>>

Return only the new README in Markdown.
