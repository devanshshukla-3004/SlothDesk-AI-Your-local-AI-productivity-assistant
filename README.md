# 🦥 SlothDesk AI — Your Local AI Productivity Assistant

**Less busywork. More headspace.** SlothDesk helps organize cluttered folders using local-first automation and optional open-weight AI. It scans file metadata, suggests categories and clearer filenames, previews every proposed move, and waits for explicit approval.

> Status: MVP under active development. This is a local desktop-style web app, not a hosted file-management service.

## Why this project?

Most file-organizing tools ask you to upload your files or rely on a remote AI API. SlothDesk is designed around a different trade-off: keep file operations on your machine, use a locally running open-weight model when available, and make the proposed actions transparent.

### Current MVP features

- Scan a folder you choose, with optional recursive scanning and a configurable file limit.
- Categorize common document, spreadsheet, presentation, image, audio, video, archive, and code formats.
- Optionally ask an Ollama model for category and filename suggestions using **filename and extension metadata only**.
- Preview a move plan before applying it.
- Refuse paths outside the selected folder and skip existing destinations instead of overwriting files.
- Optionally find byte-identical files with local SHA-256 hashing.
- Export an activity report as CSV.
- Continue with deterministic rules when Ollama is not running.

### Privacy and safety

- The app does not upload scanned files to a SlothDesk server.
- Scanning reads file metadata; it does not read file contents.
- When local AI suggestions are requested, only the filename and extension are sent to the Ollama service configured on your machine.
- Duplicate detection reads file bytes locally to calculate hashes.
- File moves require a separate confirmation step.
- The MVP does not delete files and does not overwrite existing destinations.

Use a test folder first. This is an early-stage tool; always review the plan before approving file operations.

## Quick start (Windows PowerShell)

1. Install Python 3.10 or newer.
2. Clone the repository and open its directory:

   ```powershell
   git clone https://github.com/devanshshukla-3004/SlothDesk-AI-Your-local-AI-productivity-assistant.git
   cd SlothDesk-AI-Your-local-AI-productivity-assistant
   ```

3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use a process-scoped policy for this terminal only:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies and launch the app:

   ```powershell
   python -m pip install -r requirements.txt
   streamlit run app.py
   ```

5. Open the local URL Streamlit prints (usually `http://localhost:8501`). Start by selecting a dedicated test folder.

## Enable local AI with Ollama (optional)

1. Install Ollama from [ollama.com](https://ollama.com/).
2. Download a small model suitable for your hardware, for example:

   ```powershell
   ollama pull gemma3:1b
   ```

3. Ensure Ollama is running, then use the **Local AI** panel in SlothDesk. If you use a different model, enter its installed model name in the sidebar.

The default model is `gemma3:1b`. SlothDesk communicates with Ollama at `http://127.0.0.1:11434`; this can be changed when calling the Python API directly. A model may occasionally return invalid suggestions; those files are skipped rather than automatically renamed.

## Run tests

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

## Architecture

- `app.py` — Streamlit interface and explicit approval flow.
- `slothdesk/organizer.py` — metadata scanning, categories, safe plan generation, duplicate hashing, and guarded moves.
- `slothdesk/ai_engine.py` — optional local Ollama integration.
- `tests/` — automated safety and organization tests.

## Roadmap

- [x] Metadata-only folder scan
- [x] Rule-based categories and safe plan preview
- [x] Optional local Ollama suggestions
- [x] Explicit approval before moves
- [x] Prevent overwrite and out-of-folder operations
- [x] Duplicate detection and CSV activity export
- [ ] Improve AI suggestion review/editing
- [ ] Add undo support and stronger transaction handling
- [ ] Add performance measurements and real demo screenshots
- [ ] Publish a DEV write-up documenting open-model trade-offs

## Built for open innovation

SlothDesk explores how open-weight models can make everyday automation more private and adaptable. Running inference locally can reduce reliance on closed hosted APIs, while deterministic rules keep the core workflow useful even when the model is unavailable.

## License

MIT — see [LICENSE](LICENSE).
