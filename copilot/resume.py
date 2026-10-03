"""Resume loading. The real resume lives in the gitignored data/ dir (or
RESUME_PATH); the repo only ships a redacted sample profile. Nothing personal
is ever committed.
"""
import html
import os
import re
import zipfile
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PROFILE = REPO_ROOT / "sample_data" / "sample_profile.md"
# Override with JOBFIT_DATA_DIR to keep a separate data set (e.g. a demo copy).
DATA_DIR = Path(os.getenv("JOBFIT_DATA_DIR") or REPO_ROOT / "data")
RESUME_EXTS = (".pdf", ".docx", ".txt", ".md")
# Original filename of the uploaded resume, shown in the UI.
UPLOAD_NAME_FILE = DATA_DIR / "resume_name.txt"


def _read_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_docx(path: Path) -> str:
    """Plain text from a .docx without extra deps; list items become "- " bullets."""
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    lines = []
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        text = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", para))
        text = html.unescape(text)
        if "<w:numPr>" in para and text.strip():
            text = "- " + text.strip()
        lines.append(text)
    return "\n".join(lines)


def _read(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)
    return path.read_text(encoding="utf-8", errors="replace")


def uploaded_resume_path() -> Path | None:
    for ext in RESUME_EXTS:
        path = DATA_DIR / f"resume{ext}"
        if path.is_file():
            return path
    return None


def uploaded_resume_name() -> str | None:
    path = uploaded_resume_path()
    if not path:
        return None
    if UPLOAD_NAME_FILE.is_file():
        return UPLOAD_NAME_FILE.read_text(encoding="utf-8").strip() or path.name
    return path.name


def save_uploaded_resume(filename: str, content: bytes) -> str:
    """Replace any uploaded resume with this file; return its extracted text."""
    ext = Path(filename).suffix.lower()
    if ext not in RESUME_EXTS:
        raise ValueError(f"Unsupported file type {ext!r} — use PDF, DOCX or TXT")
    DATA_DIR.mkdir(exist_ok=True)
    tmp = DATA_DIR / f"resume_upload{ext}"
    tmp.write_bytes(content)
    try:
        text = _read(tmp)
    except Exception as exc:  # noqa: BLE001 — corrupt/unreadable file
        tmp.unlink()
        raise ValueError(f"Could not read {filename}: {exc}") from exc
    if not text.strip():
        tmp.unlink()
        raise ValueError(f"No text found in {filename} (scanned image PDF?)")
    remove_uploaded_resume()
    tmp.replace(DATA_DIR / f"resume{ext}")
    UPLOAD_NAME_FILE.write_text(Path(filename).name, encoding="utf-8")
    return text


def remove_uploaded_resume() -> None:
    for ext in RESUME_EXTS:
        (DATA_DIR / f"resume{ext}").unlink(missing_ok=True)
    UPLOAD_NAME_FILE.unlink(missing_ok=True)


def load_resume_text(explicit_path: str | None = None) -> tuple[str, str]:
    """Return (resume_text, source_label).

    Resolution order: explicit_path → RESUME_PATH env → uploaded resume in
    data/ (pdf/docx/txt/md) → sample_data/sample_profile.md.
    Raises FileNotFoundError only if even the sample profile is missing.
    """
    candidates: list[tuple[str, Path]] = []
    if explicit_path:
        candidates.append(("explicit", Path(explicit_path)))
    if os.getenv("RESUME_PATH"):
        candidates.append(("RESUME_PATH", Path(os.environ["RESUME_PATH"])))
    uploaded = uploaded_resume_path()
    if uploaded:
        candidates.append(("uploaded", uploaded))

    for label, path in candidates:
        if path.is_file():
            text = _read(path)
            if text.strip():
                return text, label

    return SAMPLE_PROFILE.read_text(), "sample profile (redacted)"


def is_sample(source_label: str) -> bool:
    return source_label.startswith("sample profile")


def resume_identity(resume_text: str) -> dict:
    """Best-effort name / headline / years from the top of a resume, so
    outreach speaks as the candidate instead of a hard-coded persona."""
    lines = [ln.strip() for ln in resume_text.splitlines() if ln.strip()]
    name, headline = "", ""
    for i, line in enumerate(lines[:8]):
        words = line.lstrip("# ").split()
        if 2 <= len(words) <= 4 and all(w.replace("-", "").replace(".", "").isalpha()
                                         for w in words):
            name = " ".join(w.capitalize() if w.isupper() else w for w in words)
            for nxt in lines[i + 1:i + 3]:
                cand = re.split(r"\s[|(]|\s[—–-]\s", nxt.lstrip("# "))[0].strip()
                if cand and "@" not in cand and not re.search(r"\d{3}", cand):
                    headline = cand
                    break
            break
    years = re.search(r"(\d{1,2})\+?\s*(?:years|yrs)", resume_text, re.I)
    return {"name": name, "headline": headline,
            "years": int(years.group(1)) if years else None}


# --- Tailored resume export ----------------------------------------------------

_PARA_RE = re.compile(r"<w:p[ >].*?</w:p>", re.S)
_TEXT_RE = re.compile(r"<w:t(?: [^>]*)?>([^<]*)</w:t>")
_RUN_RE = re.compile(r"<w:r[ >].*?</w:r>", re.S)


def _norm(text: str) -> str:
    return " ".join(text.split())


def _para_text(para: str) -> str:
    return html.unescape("".join(_TEXT_RE.findall(para)))


def docx_bullets(path: Path) -> list[str]:
    """Text of every list-item paragraph, exactly as written in the .docx."""
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    return [_norm(_para_text(p)) for p in _PARA_RE.findall(xml)
            if "<w:numPr>" in p and _para_text(p).strip()]


def resume_bullets(resume_text: str, source: str = "") -> list[str]:
    """Bullets to tailor. An uploaded .docx gives exact paragraphs (so edits can
    be written back); other formats fall back to text splitting."""
    path = uploaded_resume_path() if source == "uploaded" else None
    if path and path.suffix.lower() == ".docx":
        return docx_bullets(path)
    from .tailor import _split_bullets
    return _split_bullets(resume_text, limit=None)


def _replace_para_text(para: str, new_text: str) -> str:
    """Swap a paragraph's text, keeping its paragraph properties (bullet style)
    and the formatting of its main run (the one holding the most text)."""
    runs = _RUN_RE.findall(para)
    if not runs:
        return para
    main = max(runs, key=lambda r: len("".join(_TEXT_RE.findall(r))))
    rpr = re.search(r"<w:rPr>.*?</w:rPr>", main, re.S)
    new_run = (f'<w:r>{rpr.group(0) if rpr else ""}'
               f'<w:t xml:space="preserve">{html.escape(new_text, quote=False)}</w:t></w:r>')
    first = para.index(runs[0])
    last = para.rindex(runs[-1]) + len(runs[-1])
    return para[:first] + new_run + para[last:]


def tailored_docx(path: Path, edits: dict[str, str]) -> tuple[bytes, int]:
    """Copy of the .docx with bullets replaced ({original: new}). Returns the
    file bytes and how many bullets were replaced."""
    wanted = {_norm(k): v.strip() for k, v in edits.items() if v and v.strip()}
    replaced = 0

    def swap(m: re.Match) -> str:
        nonlocal replaced
        para = m.group(0)
        new = wanted.get(_norm(_para_text(para))) if "<w:numPr>" in para else None
        if not new:
            return para
        replaced += 1
        return _replace_para_text(para, new)

    out = BytesIO()
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "word/document.xml":
                data = _PARA_RE.sub(swap, data.decode("utf-8")).encode("utf-8")
            dst.writestr(item, data)
    return out.getvalue(), replaced
