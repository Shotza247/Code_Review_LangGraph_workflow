TASK:diagram
Create one Mermaid diagram.

Name: $diagram_name
Type: $diagram_type
Shows: $description

Rules:
- Start with the keyword "$diagram_type" (for flowchart add a direction, e.g. "flowchart TD").
- Use ONLY components, files, and steps present in the summary below. Do not invent.
- Keep it under 15 nodes. Use short plain-text labels; wrap labels with special characters in double quotes.
- Output ONLY one fenced ```mermaid block, nothing else.

FILE TREE:
$tree

CODEBASE SUMMARY:
$code_summary
