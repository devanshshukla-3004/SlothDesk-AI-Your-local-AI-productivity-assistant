from pathlib import Path

import pytest

from slothdesk.organizer import apply_plan, build_plan, category_for, safe_name, scan_directory


def test_category_for_common_extensions():
    assert category_for(Path("report.pdf")) == "Documents"
    assert category_for(Path("portrait.PNG")) == "Images"
    assert category_for(Path("script.py")) == "Code"
    assert category_for(Path("mystery.blob")) == "Other"


def test_safe_name_removes_invalid_characters():
    assert safe_name("bad:name?.pdf") == "bad-name-.pdf"
    with pytest.raises(ValueError):
        safe_name("   ")


def test_scan_does_not_change_files(tmp_path):
    source = tmp_path / "report.pdf"
    source.write_text("private document", encoding="utf-8")
    files = scan_directory(tmp_path)
    assert len(files) == 1
    assert source.exists()
    assert files[0]["category"] == "Documents"


def test_build_plan_only_proposes_moves(tmp_path):
    source = tmp_path / "photo.png"
    source.write_bytes(b"image")
    files = scan_directory(tmp_path)
    plan = build_plan(files, tmp_path)
    assert len(plan) == 1
    assert plan[0]["destination"].endswith("Images/photo.png")
    assert source.exists()


def test_apply_plan_moves_approved_file_and_never_overwrites(tmp_path):
    source = tmp_path / "photo.png"
    source.write_bytes(b"new")
    destination = tmp_path / "Images" / "photo.png"
    destination.parent.mkdir()
    destination.write_bytes(b"keep")
    plan = [{"source": str(source), "destination": str(destination), "category": "Images", "status": "pending"}]
    results = apply_plan(plan, tmp_path)
    assert results[0]["status"] == "skipped"
    assert destination.read_bytes() == b"keep"
    assert source.exists()


def test_apply_plan_rejects_outside_paths(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("not in root", encoding="utf-8")
    plan = [{"source": str(outside), "destination": str(tmp_path / "Documents" / "outside.txt"), "category": "Documents", "status": "pending"}]
    results = apply_plan(plan, tmp_path)
    assert results[0]["status"] == "blocked"
    assert outside.exists()
