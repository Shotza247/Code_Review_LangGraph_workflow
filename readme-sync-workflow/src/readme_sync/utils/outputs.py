import json
from pathlib import Path

from ..config import ROOT


def output_dir(settings: dict, owner: str, repo: str) -> Path:
    d = ROOT / settings.get("outputs_dir", "outputs") / f"{owner}__{repo}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_text(out, name, text):
    path = Path(out) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")   # <- add encoding


def save_json(out, name, data):
    path = Path(out) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def zip_dir(path: str | Path) -> bytes:
    """Zip a folder in memory (used by the UI download button)."""
    import io
    import zipfile

    path = Path(path)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(path.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(path))
    return buf.getvalue()
