TASK:diagram_repair
The Mermaid diagram below failed to render. Fix the syntax error and return the corrected diagram.

Rules:
- Keep the same meaning and the same components. Do not add anything new.
- Wrap labels containing parentheses, colons, slashes, or quotes in double quotes.
- Output ONLY one fenced ```mermaid block, nothing else.

DIAGRAM TYPE: $diagram_type

BROKEN DIAGRAM:
$code

RENDER ERROR:
$error
