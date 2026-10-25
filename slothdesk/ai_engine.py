"""Optional Ollama integration. Only filenames and extensions are sent to the local model."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma3:1b"
ALLOWED_CATEGORIES = {
    "Documents", "Spreadsheets", "Presentations", "Images", "Audio",
    "Video", "Archives", "Code", "Other",
}


def ollama_status(base_url: str = DEFAULT_OLLAMA_URL, timeout: float = 2.0) -> tuple[bool, list[str]]:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        response.raise_for_status()
        models = [model.get("name", "") for model in response.json().get("models", [])]
        return True, models
    except (requests.RequestException, ValueError):
        return False, []


def _clean_json(text: str) -> dict[str, Any]:
    text = text.strip()
    text = re.sub(r"^\x60{3}(?:json)?\s*|\s*\x60{3}$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("The local model did not return valid JSON.")
    data = json.loads(text[start:end + 1])
    category = data.get("category", "Other")
    if category not in ALLOWED_CATEGORIES:
        category = "Other"
    name = str(data.get("suggested_name", "")).strip()
    if not name:
        raise ValueError("The local model returned no filename suggestion.")
    return {"category": category, "suggested_name": name}


def suggest_organization(filename: str, extension: str, model: str = DEFAULT_MODEL,
                         base_url: str = DEFAULT_OLLAMA_URL, timeout: float = 45.0) -> dict[str, str]:
    """Ask a local Ollama model for a category and filename based on metadata only."""
    prompt = (
        "You organize filenames. Based ONLY on this filename and extension, return one JSON object "
        "with keys category and suggested_name. category must be one of Documents, Spreadsheets, "
        "Presentations, Images, Audio, Video, Archives, Code, Other. Keep the same file extension, "
        "make the name concise and descriptive, do not invent contents, and do not include a path. "
        f"Filename: {json.dumps(filename)}. Extension: {json.dumps(extension)}."
    )
    response = requests.post(
        f"{base_url.rstrip('/')}/api/generate",
        json={"model": model or os.getenv("SLOTHDESK_OLLAMA_MODEL", DEFAULT_MODEL),
              "prompt": prompt, "stream": False, "format": "json"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    result = _clean_json(payload.get("response", ""))
    original_suffix = Path(filename).suffix
    if original_suffix:
        proposed = Path(result["suggested_name"])
        if proposed.suffix.lower() != original_suffix.lower():
            result["suggested_name"] = proposed.stem + original_suffix
    elif Path(result["suggested_name"]).suffix:
        result["suggested_name"] = Path(result["suggested_name"]).stem
    return result
