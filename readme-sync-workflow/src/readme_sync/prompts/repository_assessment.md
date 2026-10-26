TASK:repository_assessment
Create a compact static assessment from the evidence only. Do not claim code or commands were executed.

README:
<<<
$readme
>>>

FILE TREE:
<<<
$tree
>>>

SAMPLED FILES:
<<<
$sampled_files
>>>

CODE SUMMARY:
<<<
$code_summary
>>>

Return ONLY minified valid JSON. No Markdown. No trailing commas. No line breaks inside string values. Maximum 2 items per array. Maximum 120 characters per string.

Schema:
{"gap_report":{"missing":[],"inaccurate":[],"covered_well":[]},"code_review":{"findings":[],"strengths":[],"test_gaps":[],"scope_note":"Static review only; no code or tests were executed."},"reproducibility_report":{"status":"documented|partial|unknown","prerequisites":[],"setup_commands":[],"run_commands":[],"test_commands":[],"configuration":[],"verification":[],"gaps":[],"scope_note":"Commands and checks were identified from files and were not executed."},"code_understanding":{"main_flow":"...","components":[],"data_flow":"...","unknowns":[]}}

Object shapes:
missing={"item":"...","evidence":"...","severity":"high|medium|low"}
inaccurate={"readme_claim":"...","reality":"...","evidence":"..."}
finding={"severity":"high|medium|low","file":"...","issue":"...","evidence":"...","recommendation":"...","confidence":1}
component={"name":"...","responsibility":"...","evidence":"..."}
verification={"check":"...","evidence":"...","execution_status":"documented_not_executed"}
