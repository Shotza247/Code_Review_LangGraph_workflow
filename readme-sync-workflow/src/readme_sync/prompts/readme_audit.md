TASK:readme_audit
Assess whether a stranger could reproduce this project using ONLY its README.

Score every criterion in the rubric. Be strict: award points only for what the README explicitly states. Do not assume anything.

RUBRIC:
$rubric

README:
<<<
$readme
>>>

Return ONLY valid JSON (no fences) in this shape:
{"criteria": {"<criterion_id>": {"score": <number>, "note": "<one sentence>"}}, "strengths": ["..."], "weaknesses": ["..."], "summary": "<two sentences>"}
