# 🦥 SlothDesk AI
### Your local-first AI productivity assistant

**Less busywork. More headspace.**

SlothDesk AI helps turn cluttered folders into organized workspaces. It scans file metadata, proposes sensible categories and clearer filenames, and presents a reviewable plan before making changes. Optional AI suggestions run through **Ollama on your own machine**—no paid AI API is required for the core workflow.

<p align="center">
  <a href="https://github.com/devanshshukla-3004/SlothDesk-AI-Your-local-AI-productivity-assistant">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  </a>
  <img alt="Streamlit" src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white">
  <img alt="Local AI" src="https://img.shields.io/badge/AI-Ollama%20(optional)-1F6B45?style=for-the-badge">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-6B8E23?style=for-the-badge">
</p>

<p align="center">
  <a href="#-why-slothdesk">Why SlothDesk</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-quick-start">Quick start</a> ·
  <a href="#-local-ai-optional">Local AI</a> ·
  <a href="#-safety-and-privacy">Safety & privacy</a> ·
  <a href="#-development">Development</a>
</p>

---

## 🌿 Why SlothDesk?

File organization should not mean uploading personal files to a third-party service or handing over control to an opaque automation tool.

SlothDesk is built around three principles:

- **Local-first:** work with folders on your own machine.
- **AI when you want it:** use a locally running open-weight model for optional suggestions, or rely on deterministic rules.
- **Human approval first:** inspect the proposed actions before any files are moved.

> **Project status:** Early-stage MVP under active development. SlothDesk is a local Streamlit app, not a hosted file-management service.

## ✨ Features

| Capability | What it does |
| --- | --- |
| **Folder scanning** | Scans a selected folder, with optional recursive scanning and a configurable file limit. |
| **Automatic categorization** | Sorts common documents, spreadsheets, presentations, images, audio, video, archives, and code files using file extensions. |
| **Optional AI suggestions** | Uses Ollama to suggest a category and clearer filename from the filename and extension only. |
| **Reviewable action plan** | Previews proposed moves before you approve them. Scanning and planning do not move files. |
| **Guarded file operations** | Blocks paths outside the selected folder and skips destinations that already exist. |
| **Duplicate detection** | Can identify byte-identical files using local SHA-256 hashes. |
| **CSV activity report** | Exports an activity report so you can inspect the results. |
| **Rule-based fallback** | Core categorization remains available when Ollama is not installed or running. |

## 🔄 How it works

1. **Choose a folder** — select a working folder to inspect.
2. **Scan metadata** — SlothDesk collects file paths, names, extensions, sizes, and modification times.
3. **Generate suggestions** — deterministic rules categorize files; optionally, Ollama suggests category and filename improvements.
4. **Review the plan** — inspect the proposed organization before applying anything.
5. **Approve file moves** — only the approved plan is applied, with safeguards against out-of-folder operations and overwrites.
6. **Review results** — inspect the operation status and export a CSV activity report.

```text
Choose folder
    ↓
Scan metadata
    ↓
Suggest categories and filenames
    ↓
Preview proposed changes
    ↓
User approval
    ↓
Apply guarded moves + export report
```

## 🚀 Quick start

### Requirements

- Python **3.10 or newer**
- Windows, macOS, or Linux environment capable of running Streamlit
- [Ollama](https://ollama.com/) only if you want local AI suggestions

### 1. Clone the repository

```bash
git clone https://github.com/devanshshukla-3004/SlothDesk-AI-Your-local-AI-productivity-assistant.git
cd SlothDesk-AI-Your-local-AI-productivity-assistant
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow it for the current terminal session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Run SlothDesk

```bash
streamlit run app.py
```

Open the local address printed by Streamlit—usually [http://localhost:8501](http://localhost:8501).

**First run tip:** Start with a small test folder containing copies of files. Review every proposed action before approving it.

## 🤖 Local AI (optional)

SlothDesk can use [Ollama](https://ollama.com/) for local filename and category suggestions. AI is optional; the rule-based workflow can run without it.

1. Install Ollama.
2. Pull the default lightweight model:

   ```bash
   ollama pull gemma3:1b
   ```

3. Ensure Ollama is running, then open SlothDesk and use the **Local AI** panel.
4. If you use another installed model, select or enter its model name in the app.

**Default model:** `gemma3:1b`  
**Default local endpoint:** `http://127.0.0.1:11434`

The app sends the model the filename and extension—not the contents of the file. Local inference performance depends on your hardware and chosen model. Invalid model suggestions are rejected rather than applied automatically.

## 🔐 Safety and privacy

SlothDesk is designed to keep file operations transparent and under your control.

- **No SlothDesk upload service:** scanned files are not uploaded to a SlothDesk-hosted backend.
- **Metadata-first scanning:** normal scanning does not read file contents.
- **Local AI requests:** when enabled, only the filename and extension are sent to the configured Ollama service.
- **Local duplicate hashing:** duplicate detection reads file bytes locally to calculate SHA-256 hashes.
- **Approval before changes:** file moves require a separate confirmation step.
- **No automatic deletion:** the current MVP does not delete files.
- **No overwrites:** an existing destination is skipped.
- **Path guards:** moves outside the selected root are blocked.

Privacy note: if you configure Ollama to use a non-local endpoint, your model requests will go to that endpoint. Keep the default local endpoint if you want inference to remain on your machine.

This is an early-stage project, not a substitute for backups. Test on copies and review the plan before applying file operations.

## 🧰 Tech stack

- **Python** — application and file-organization logic
- **Streamlit** — interactive local web interface
- **Ollama** — optional local model inference
- **Requests** — communication with the Ollama API
- **Pytest** — automated tests

## 🗂️ Project structure

```text
SlothDesk-AI-Your-local-AI-productivity-assistant/
├── app.py                 # Streamlit UI and approval workflow
├── slothdesk/
│   ├── organizer.py       # Scanning, categories, planning, hashing and guarded moves
│   └── ai_engine.py       # Optional Ollama integration
├── tests/                 # Automated tests
├── .github/
│   └── workflows/
│       └── tests.yml      # GitHub Actions test workflow
├── requirements.txt
├── README.md
└── LICENSE
```

## 🧪 Development

### Run the test suite

```bash
python -m pytest -q
```

### Contribution workflow

1. Fork the repository.
2. Create a focused branch for your change.
3. Add or update tests for behavior changes, especially file-safety logic.
4. Run the test suite locally.
5. Open a pull request describing the change and its impact.

For safety-related changes, include tests for paths outside the selected folder, existing destination files, invalid AI output, and filesystem errors where relevant.

## 🌍 Open innovation

SlothDesk explores how open-weight AI can support practical everyday productivity without making a hosted proprietary AI service a requirement. Combining local inference with deterministic rules and explicit user approval keeps the workflow useful, inspectable, and adaptable.

Built as an independent project for the **Hacktoberfest Open-Source AI Challenge — Week 3: Slow and Steady**.

## 📄 License

Distributed under the [MIT License](LICENSE).

---

<p align="center">
  <strong>SlothDesk AI</strong><br>
  Less busywork. More headspace. 🌿
</p>
