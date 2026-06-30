# Module 2: Reservation Approval Workflow

This module introduces a human-in-the-loop reservation approval system, including an administrative API and an admin-facing agent.

## Prerequisites

- **Python**: 3.9+
- **OpenAI API Key**: Required for the admin agent.
- **SQLite**: Used for data storage.

## Environment Variables

Configure the following environment variables. You can create a `.env` file in this directory or export them in your shell.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI API key | - |
| `DB_NAME` | Path to the SQLite database | `../parking.db` |

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

## Database setup

Stage 2 uses the shared SQLite database `parking.db` located at the repository root. It extends the schema with approval-specific columns.

### Linux/macOS
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/..
# 1. Initialize base schema (if not done in Stage 1)
python3 ../stage_1/scripts/init_db.py
# 2. Extend schema for Stage 2
python3 -c "from stage_2.db import ensure_stage_2_columns; ensure_stage_2_columns()"
ls -la ../parking.db
```

### Windows PowerShell
```powershell
$env:PYTHONPATH="..;."
# 1. Initialize base schema (if not done in Stage 1)
python ..\stage_1\scripts\init_db.py
# 2. Extend schema for Stage 2
python -c "from stage_2.db import ensure_stage_2_columns; ensure_stage_2_columns()"
dir ..\parking.db
```

## Linux/macOS Launch

### Start Admin API
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/..
python3 -m uvicorn stage_2.admin_api:app --reload
```

## Windows PowerShell Launch

### Start Admin API
```powershell
$env:PYTHONPATH="..;."
python -m uvicorn stage_2.admin_api:app --reload
```

## How to Run Tests

### Linux/macOS
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/..
python3 -m pytest ../stage_2/tests/ -v
```

### Windows PowerShell
```powershell
$env:PYTHONPATH="..;."
python -m pytest ..\stage_2\tests\ -v
```

## Troubleshooting (Startup)

- **Import Errors**: Ensure `PYTHONPATH` is correctly set to include the project root.
- **Database Missing Columns**: If you see errors about missing columns like `admin_comment`, ensure you have run the schema extension command.
- **Uvicorn Not Found**: Ensure you have installed the dependencies from `requirements.txt`.
- **SQLite Busy**: Ensure no other process is holding a lock on `parking.db` during initialization.
