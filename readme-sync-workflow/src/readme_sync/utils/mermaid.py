import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..config import ROOT

INSTALL_HINT = "npm install -g @mermaid-js/mermaid-cli"
# mmdc failures that mean "the tool could not run", not "the diagram is wrong"
_LAUNCH_FAILURES = ("Failed to launch", "Could not find Chrome", "Could not find browser", "No usable sandbox")


class MermaidToolError(RuntimeError):
    """mmdc is missing or cannot start, and validation mode is 'required'."""


@dataclass
class ValidationResult:
    ok: bool
    validated: bool          # False when mmdc did not run (off, missing, or could not launch)
    error: str = ""
    svg_path: str | None = None
    note: str = ""           # why validation was skipped, if it was

def find_mmdc(cfg: dict) -> str | None:
    """Priority: explicit config path > project-local install > global install."""
    if cfg.get("mmdc_path"):
        return cfg["mmdc_path"]
    exe = "mmdc.cmd" if os.name == "nt" else "mmdc"
    local = ROOT / "node_modules" / ".bin" / exe
    if local.exists():
        return str(local)
    return shutil.which("mmdc")

def validate_mermaid(code: str, svg_path: Path, cfg: dict) -> ValidationResult:
    """Render `code` with mmdc. A non-zero exit with a parse error means the diagram is invalid."""
    mode = cfg.get("mode", "auto")
    if mode == "off":
        return ValidationResult(ok=True, validated=False, note="mermaid_validation.mode is off")

    exe = find_mmdc(cfg)
    if not exe:
        msg = f"mmdc not found. Install with: {INSTALL_HINT}"
        if mode == "required":
            raise MermaidToolError(msg)
        return ValidationResult(ok=True, validated=False)

    svg_path = Path(svg_path)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "diagram.mmd"
        src.write_text(code, encoding="utf-8")
        cmd = [exe, "-i", str(src), "-o", str(svg_path), "-q"]
        if cfg.get("puppeteer_config"):
            cmd += ["-p", str((ROOT / cfg["puppeteer_config"]).resolve())]
        try:
                        proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=cfg.get("timeout_s", 60),
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(ok=False, validated=True, error="mmdc timed out while rendering")

    if proc.returncode == 0:
        return ValidationResult(ok=True, validated=True, svg_path=str(svg_path))

    err = (proc.stderr or proc.stdout or "").strip()
    if any(marker in err for marker in _LAUNCH_FAILURES):
        msg = (
            "mmdc could not start its headless browser. In Docker/root/WSL set "
            "mermaid_validation.puppeteer_config to config/puppeteer-config.json. "
            f"Details: {err[-300:]}"
        )
        if mode == "required":
            raise MermaidToolError(msg)
        return ValidationResult(ok=True, validated=False, note=msg)
    return ValidationResult(ok=False, validated=True, error=err[-800:])
