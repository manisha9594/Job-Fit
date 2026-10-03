import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from copilot import resume


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(resume, "DATA_DIR", tmp_path)
    monkeypatch.setattr(resume, "UPLOAD_NAME_FILE", tmp_path / "resume_name.txt")
    monkeypatch.delenv("RESUME_PATH", raising=False)
    return tmp_path


def _docx_bytes(tmp_path: Path) -> bytes:
    body = (
        '<w:document><w:body>'
        '<w:p><w:r><w:t>Jane Doe</w:t></w:r></w:p>'
        '<w:p><w:pPr><w:numPr/></w:pPr><w:r><w:t>Built FastAPI &amp; React apps</w:t></w:r></w:p>'
        '</w:body></w:document>'
    ).replace("<w:numPr/>", "<w:numPr></w:numPr>")
    path = tmp_path / "src.docx"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", body)
    return path.read_bytes()


def test_falls_back_to_sample_without_upload(data_dir):
    _, source = resume.load_resume_text()
    assert resume.is_sample(source)
    assert resume.uploaded_resume_name() is None


def test_upload_txt_then_remove(data_dir):
    resume.save_uploaded_resume("My CV.txt", b"- Built Python services on AWS")
    text, source = resume.load_resume_text()
    assert source == "uploaded" and "Python" in text
    assert resume.uploaded_resume_name() == "My CV.txt"

    resume.remove_uploaded_resume()
    assert resume.is_sample(resume.load_resume_text()[1])


def test_upload_docx_extracts_bullets(data_dir, tmp_path):
    text = resume.save_uploaded_resume("cv.docx", _docx_bytes(tmp_path))
    assert "Jane Doe" in text
    assert "- Built FastAPI & React apps" in text


def test_new_upload_replaces_old(data_dir, tmp_path):
    resume.save_uploaded_resume("old.txt", b"old resume text here")
    resume.save_uploaded_resume("new.docx", _docx_bytes(tmp_path))
    assert not (data_dir / "resume.txt").exists()
    assert resume.uploaded_resume_name() == "new.docx"


def test_rejects_unsupported_and_empty(data_dir):
    with pytest.raises(ValueError):
        resume.save_uploaded_resume("cv.png", b"\x89PNG")
    with pytest.raises(ValueError):
        resume.save_uploaded_resume("cv.txt", b"   ")
    assert resume.uploaded_resume_path() is None


def test_tailored_docx_replaces_only_matching_bullets(data_dir, tmp_path):
    body = (
        '<w:document><w:body>'
        '<w:p><w:r><w:t>Header</w:t></w:r></w:p>'
        '<w:p><w:pPr><w:numPr></w:numPr></w:pPr>'
        '<w:r><w:rPr><w:b/></w:rPr><w:t>Built</w:t></w:r>'
        '<w:r><w:rPr><w:i/></w:rPr><w:t xml:space="preserve"> REST services in C#</w:t></w:r></w:p>'
        '<w:p><w:pPr><w:numPr></w:numPr></w:pPr><w:r><w:t>Led a team</w:t></w:r></w:p>'
        '</w:body></w:document>'
    )
    src = tmp_path / "multi.docx"
    with zipfile.ZipFile(src, "w") as zf:
        zf.writestr("word/document.xml", body)
        zf.writestr("word/styles.xml", "<styles/>")

    assert resume.docx_bullets(src) == ["Built REST services in C#", "Led a team"]
    data, n = resume.tailored_docx(src, {"Built  REST services in C#": "Built REST APIs & <services>"})
    assert n == 1
    out = tmp_path / "out.docx"
    out.write_bytes(data)
    assert resume.docx_bullets(out) == ["Built REST APIs & <services>", "Led a team"]
    xml = zipfile.ZipFile(out).read("word/document.xml").decode()
    assert "<w:i/>" in xml and "<w:numPr>" in xml  # main run + bullet formatting kept
    assert zipfile.ZipFile(out).read("word/styles.xml") == b"<styles/>"
