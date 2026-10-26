TASK:readme_rerate
Re-score the README for reproducibility, now using the codebase as ground truth. Penalize missing steps and anything the code contradicts. Be strict.

RUBRIC:
$rubric

README:
<<<
$readme
>>>

CODEBASE SUMMARY:
<<<
$code_summary
>>>

GAP REPORT:
$gap_report

Return ONLY valid JSON (no fences):
{"criteria": {"<criterion_id>": {"score": <number>, "note": "<one sentence>"}}, "strengths": ["..."], "weaknesses": ["..."], "summary": "<two sentences>"}
