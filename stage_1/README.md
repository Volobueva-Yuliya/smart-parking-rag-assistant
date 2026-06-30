# Module 1: Smart Parking RAG Assistant

This module implements the core RAG (Retrieval-Augmented Generation) pipeline and a terminal-based chatbot for the Smart Parking Assistant.

## Prerequisites

- **Python**: 3.9+
- **OpenAI API Key**: Required for GPT-based responses.
- **Docker & Docker Compose**: Required for running the Weaviate vector database.
- **Weaviate**: Vector database instance (started via Docker).

## Environment Variables

Configure the following environment variables. You can create a `.env` file in this directory or export them in your shell.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI API key | - |
| `DB_NAME` | Path to the SQLite database | `../../parking.db` |
| `WEAVIATE_HOST` | Weaviate connection host | `localhost` |
| `WEAVIATE_PORT` | Weaviate connection port | `8080` |

### Linux/macOS
```bash
export OPENAI_API_KEY="your-api-key"
```

### Windows PowerShell
```powershell
$env:OPENAI_API_KEY="your-api-key"
```

## Installation

### Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

*Note: If PowerShell execution policy blocks activation, run:*
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Linux/macOS Launch

1. **Start Weaviate**:
   ```bash
   docker compose up -d
   ```

2. **Initialize Database and Vector Store**:
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)/..
   python3 scripts/init_db.py
   python3 scripts/create_collection.py
   python3 scripts/ingest_kb.py
   ```

3. **Start Chatbot**:
   ```bash
   python3 app/chatbot.py
   ```

## Windows PowerShell Launch

1. **Start Weaviate**:
   ```powershell
   docker compose up -d
   ```

2. **Initialize Database and Vector Store**:
   ```powershell
   $env:PYTHONPATH="..;."
   python scripts/init_db.py
   python scripts/create_collection.py
   python scripts/ingest_kb.py
   ```

3. **Start Chatbot**:
   ```powershell
   python app/chatbot.py
   ```

## How to Run Tests

### Linux/macOS
```bash
PYTHONPATH=.. pytest -v
```

### Windows PowerShell
```powershell
$env:PYTHONPATH=".."
pytest -v
```

## Troubleshooting (Startup)

- **OpenAI API Key**: Ensure `OPENAI_API_KEY` is set. The bot will fail at startup if missing.
- **Weaviate Connection**: If scripts fail with connection errors, verify Weaviate is running using `docker ps`.
- **Import Errors**: If you encounter `ModuleNotFoundError`, ensure your `PYTHONPATH` includes the parent directory as shown in the launch steps.
- **PowerShell Activation**: Ensure you use `.\.venv\Scripts\Activate.ps1` and have set the correct execution policy.
- **Missing Database**: Ensure `scripts/init_db.py` is run before the chatbot to create `parking.db`.
