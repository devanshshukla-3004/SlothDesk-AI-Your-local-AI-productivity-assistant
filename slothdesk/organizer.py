"""Safe, deterministic file organization primitives for SlothDesk AI."""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

CATEGORY_BY_EXTENSION = {
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".tex"},
    "Spreadsheets": {".csv", ".xls", ".xlsx", ".ods"},
    "Presentations": {".ppt", ".pptx", ".odp", ".key"},
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg", ".heic"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Video": {".mp4", ".mov", ".mkv", ".avi", ".webm", ".wmv"},
    "Archives": {".zip", ".tar", ".gz", ".7z", ".rar", ".bz2"},
    "Code": {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".yml", ".yaml", ".toml", ".sql", ".java", ".c", ".cpp", ".rs", ".go", ".sh", ".ps1"},
}
PROTECTED_NAMES = {".git", ".ssh", ".gnupg", "node_modules", ".venv", "venv", "windows", "system32"}


def category_for(path: Path) -> str:
    """Return a predictable category using the file extension."""
    suffix = path.suffix.lower()
    for category, extensions in CATEGORY_BY_EXTENSION.items():
        if suffix in extensions:
            return category
    return "Other"


def safe_name(name: str, max_length: int = 120) -> str:
    """Normalize a proposed filename while preserving its extension."""
    raw = Path(name).name.strip()
    if not raw or raw in {".", ".."}:
        raise ValueError("Filename cannot be empty.")
    suffix = Path(raw).suffix
    stem = raw[:-len(suffix)] if suffix else raw
    stem = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "-", stem)
    stem = re.sub(r"\s+", " ", stem).strip(" .")
    if not stem:
        stem = "untitled"
    available = max(1, max_length - len(suffix))
    return stem[:available] + suffix[:max_length]


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def scan_directory(folder: str | Path, recursive: bool = True, max_files: int = 2000) -> list[dict[str, Any]]:
    """Scan a user-selected folder without reading file contents or changing anything."""
    root = Path(folder).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("Choose an existing folder.")
    if root.name.lower() in PROTECTED_NAMES:
        raise ValueError("This looks like a protected system folder. Choose a regular working folder.")

    iterator = root.rglob("*") if recursive else root.iterdir()
    results: list[dict[str, Any]] = []
    for path in iterator:
        if len(results) >= max_files:
            break
        try:
            if not path.is_file() or not _is_within(path, root):
                continue
            if any(part.lower() in PROTECTED_NAMES for part in path.relative_to(root).parts[:-1]):
                continue
            stat = path.stat()
            results.append({
                "path": str(path),
                "name": path.name,
                "extension": path.suffix.lower() or "(no extension)",
                "category": category_for(path),
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
            })
        except (OSError, ValueError):
            continue
    return sorted(results, key=lambda item: (item["category"], item["name"].lower()))


def duplicate_groups(files: list[dict[str, Any]]) -> list[list[str]]:
    """Find byte-identical files by size and SHA-256; only hashes file bytes when requested."""
    by_size: dict[int, list[str]] = defaultdict(list)
    for item in files:
        by_size[item["size_bytes"]].append(item["path"])
    groups: list[list[str]] = []
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        hashes: dict[str, list[str]] = defaultdict(list)
        for path in paths:
            digest = hashlib.sha256()
            try:
                with open(path, "rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
                hashes[digest.hexdigest()].append(path)
            except OSError:
                continue
        groups.extend(group for group in hashes.values() if len(group) > 1)
    return groups


def build_plan(files: list[dict[str, Any]], root: str | Path, organize: bool = True) -> list[dict[str, str]]:
    """Build a reviewable plan. No filesystem changes occur here."""
    base = Path(root).expanduser().resolve()
    plan: list[dict[str, str]] = []
    for item in files:
        source = Path(item["path"]).resolve()
        if not _is_within(source, base) or not source.is_file():
            continue
        category = item.get("category") or category_for(source)
        destination_dir = base / category if organize else source.parent
        destination = destination_dir / safe_name(item.get("suggested_name") or source.name)
        if source == destination:
            continue
        plan.append({
            "source": str(source),
            "destination": str(destination),
            "category": str(category),
            "status": "pending",
        })
    return plan


def apply_plan(plan: list[dict[str, str]], root: str | Path) -> list[dict[str, str]]:
    """Apply approved moves only; refuse paths outside root and all overwrites."""
    base = Path(root).expanduser().resolve()
    results: list[dict[str, str]] = []
    for item in plan:
        source = Path(item["source"]).resolve()
        destination = Path(item["destination"]).resolve()
        result = dict(item)
        if not _is_within(source, base) or not _is_within(destination, base):
            result.update(status="blocked", message="Path is outside the selected folder.")
        elif not source.is_file():
            result.update(status="skipped", message="Source file no longer exists.")
        elif destination.exists():
            result.update(status="skipped", message="Destination already exists; no file was overwritten.")
        else:
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                source.rename(destination)
                result.update(status="moved", message="Moved successfully.")
            except OSError as exc:
                result.update(status="error", message=str(exc))
        results.append(result)
    return results
