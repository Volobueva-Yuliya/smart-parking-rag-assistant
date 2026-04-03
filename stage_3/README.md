# Stage 3: Lightweight MCP-style Processing Server

This module provides a lightweight, FastAPI-based processing server for handling and storing confirmed parking reservations, following a Modular Context Protocol (MCP) inspired architecture.

## Overview

Stage 3 focuses on the downstream processing of reservations after they have been approved by the administrative team in Stage 2. It acts as an independent processing layer that:
- Receives or synchronizes approved reservation data.
- Formats the data according to the required external storage format.
- Persists the records into a finalized text-based ledger.
- Provides a secure, token-protected API for both manual and automated synchronization.

## Architecture and Responsibility

Stage 3 is designed as a standalone consumer of the parking system, implementing a "human-in-the-loop" to "confirmed-storage" transition:
- **MCP-style Architecture**: Implemented as a clean, tool-like service (Python + FastAPI) that can be easily integrated into larger orchestration flows.
- **Separation of Concerns**: Stage 3 logic is completely isolated from the Stage 2 approval process. It observes the shared state and acts upon it.
- **Shared Database Strategy**: Instead of Stage 2 pushing data to Stage 3, Stage 3 independently pulls data from the shared `parking.db`. This keeps the administrative logic clean and allows Stage 3 to be run as an independent background process or a triggered service.
- **Idempotency**: Stage 3 maintains its own internal state (`export_state.json`) to track which reservations have already been exported, preventing duplicate entries in the final output file even if the synchronization process is triggered multiple times.

## Module Structure

```text
stage_3/
├── app/
│   ├── __init__.py
│   ├── mcp_server.py      # FastAPI application and endpoints
│   ├── config.py          # Configuration and environment variables
│   ├── models.py          # Pydantic data models (ConfirmedReservation)
│   ├── auth.py            # Bearer token authentication helper
│   ├── db_reader.py       # Reads approved reservations from shared SQLite
│   ├── export_state.py    # Tracks exported reservation codes (JSON-based state)
│   ├── file_writer.py     # Logic for appending to the text ledger
│   └── service.py         # Business logic and synchronization layer
├── storage/               # Directory for persistent text files and state
│   ├── .gitkeep
│   ├── confirmed_reservations.txt  # The final output ledger
│   └── export_state.json           # Tracking file for duplicate prevention
├── tests/                 # Automated tests for Stage 3
│   ├── __init__.py
│   ├── test_logic.py      # Unit tests for formatting and file writing
│   ├── test_smoke.py      # API health and authentication tests
│   └── test_sync.py       # SQLite synchronization and idempotency tests
├── requirements.txt       # Stage 3 dependencies (FastAPI, uvicorn, etc.)
└── README.md              # This documentation
```

## Export Format

Every confirmed reservation is appended to the output file as a single line in the following format:
`Full Name | Car Number | Reservation Period | Approval Time`

**Example:**
`Lila Ivanova | SDS-100 | 2026-04-02T10:00:00 to 2026-04-02T18:00:00 | 2026-04-02T09:45:10`

## Setup and Installation

1. **Install Dependencies**:
   ```bash
   pip install -r stage_3/requirements.txt
   ```

2. **Environment Variables**:
   - `DB_NAME`: Path to the shared SQLite database (default: `parking.db` at repo root).
   - `CONFIRMED_FILE_PATH`: Path to the output ledger (default: `stage_3/storage/confirmed_reservations.txt`).
   - `EXPORT_STATE_FILE_PATH`: Path to the tracking file (default: `stage_3/storage/export_state.json`).
   - `STAGE_3_API_TOKEN`: Secret Bearer token for authentication (default: `default_secret_token`).

## Running the Server

Start the FastAPI server from the project root:
```bash
python3 -m uvicorn stage_3.app.mcp_server:app --host 0.0.0.0 --port 8001 --reload
```

## API Validation Examples

### 1. Health Check
```bash
curl http://localhost:8001/health
```

### 2. Manual Confirmation (Direct)
```bash
curl -X POST http://localhost:8001/confirm \
     -H "Authorization: Bearer default_secret_token" \
     -H "Content-Type: application/json" \
     -d '{
           "reservation_code": "R-MANUAL-001",
           "first_name": "Lila",
           "last_name": "Ivanova",
           "car_number": "SDS-100",
           "start_time": "2026-04-02T10:00:00",
           "end_time": "2026-04-02T18:00:00",
           "approval_time": "2026-04-02T09:45:10"
         }'
```

### 3. Synchronization (from SQLite)
```bash
curl -X POST http://localhost:8001/sync-confirmed \
     -H "Authorization: Bearer default_secret_token"
```

Expected Sync Response:
```json
{
  "success": true,
  "found_approved": 3,
  "already_exported": 1,
  "exported_now": 2,
  "exported_codes": ["R-001", "R-003"],
  "message": "Sync completed successfully."
}
```

## Testing

Run all automated tests (unit, integration, and sync):
```bash
export PYTHONPATH=$(pwd)
python3 -m pytest stage_3/tests/
```

### Test Coverage Highlights:
- **Idempotency**: Verified that repeated sync calls do not result in duplicate ledger entries.
- **Authentication**: Verified that `/confirm` and `/sync-confirmed` correctly enforce Bearer token rules.
- **Data Integrity**: Verified correct formatting of the output text lines.
- **DB Interaction**: Verified that only `approved` records are fetched and processed.
