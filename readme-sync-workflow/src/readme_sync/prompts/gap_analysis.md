TASK:gap_analysis
Compare the README with the codebase summary. Find what a person needs to reproduce the project that the README leaves out or gets wrong.

README:
<<<
$readme
>>>

CODEBASE SUMMARY:
<<<
$code_summary
>>>

Return ONLY valid JSON (no fences):
{"missing": [{"item": "<what is missing>", "evidence": "<file or fact in the summary>", "severity": "high|medium|low"}],
 "inaccurate": [{"readme_claim": "...", "reality": "...", "evidence": "..."}],
 "covered_well": ["..."]}
