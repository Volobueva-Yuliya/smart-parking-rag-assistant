# Stage 2: Reservation Approval Workflow

This documentation covers **Stage 2** of the smart parking assistant project, which introduces a human-in-the-loop reservation approval system and a second administrative agent.

## Overview

The goal of Stage 2 is to move beyond simple data collection and implement a formal approval process for parking reservations. 
- **Human-in-the-loop workflow**: Reservations are not finalized immediately but require administrative review and decision.
- **Second Admin Agent**: A dedicated administrative agent built using **LangChain** concepts is introduced to handle approvals and rejections via specialized tools.

## Key Features

- **Reservation Lifecycle**: Support for advanced statuses: `pending_admin_approval`, `approved`, and `rejected`.
- **Admin REST API**: A FastAPI-based service allowing administrators to retrieve reservation details and submit decisions.
- **LangChain-based Admin Agent**: An administrative agent using `@tool` decorated functions to interact with the database and process decisions.
- **Integration with Booking Flow**: The user-facing booking process automatically submits requests for administrative review upon user confirmation.
- **Shared SQLite Database**: A unified `parking.db` located at the project root, shared between Stage 1 and Stage 2 modules.

## Project Structure (Stage 2)

```text
smart-parking-rag-assistant/
└── stage_2/
    ├── __init__.py
    ├── admin_agent.py        # LangChain-based admin agent (tools)
    ├── admin_api.py          # REST API for admin decisions (FastAPI)
    ├── admin_client.py       # Sending requests to admin (stub/integration layer)
    ├── booking_flow.py       # Booking validation, summary, and finalization
    ├── chatbot_flow.py       # User-facing flow for Stage 2 (confirmation/status)
    ├── db.py                 # Extended DB logic (statuses, admin fields, schema)
    ├── design.md             # Stage 2 behavior and flow definition
    └── tests/                # Stage 2 automated tests (pytest)
```

## Architecture (Stage 2)

- **`chatbot_flow` / `booking_flow`**: Handles user interaction, data validation (non-empty fields), and the finalization of the reservation after user confirmation.
- **`admin_client`**: An abstraction layer (currently a stub) responsible for forwarding reservation requests to the administrative side.
- **`admin_api`**: A FastAPI application providing endpoints for administrators to fetch reservations and submit `approved` or `rejected` decisions.
- **`admin_agent`**: A second agent using LangChain tools (`approve_reservation`, `reject_reservation`) to execute administrative actions.
- **`SQLite Database`**: The central storage for all reservations, updated with timestamps and administrative comments during the lifecycle.

## Reservation Workflow

1. **User Submits Booking**: User provides name, vehicle plate, and requested times.
2. **Chatbot Collects Data**: The system ensures all fields are complete and valid.
3. **Pending Reservation Created**: After explicit confirmation, a reservation is stored with status `pending_admin_approval`.
4. **Request Sent to Admin**: The reservation is automatically forwarded to the admin integration layer (`admin_client`).
5. **Admin Reviews**: Administrator reviews the pending request via the Admin API or the Admin Agent.
6. **Approve/Reject**: Admin submits a decision; the system updates the record with `admin_decision_at` and `admin_comment`.
7. **User Checks Status**: The user queries their reservation code to receive the final decision and any admin notes.

## Running Stage 2

### Start Admin API
Ensure your `PYTHONPATH` includes the project root:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/smart-parking-rag-assistent
python3 -m uvicorn stage_2.admin_api:app --reload
```

### Run Stage 2 Tests
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/smart-parking-rag-assistent
python3 -m pytest smart-parking-rag-assistent/stage_2/tests/ -q
```

## Example Flow

1. **Booking**: User confirms booking for "Lila Ivanova, SDS-100".
2. **Pending**: Reservation `R-20260401-001` created as `pending_admin_approval`.
3. **Approval**: Admin calls API `POST /admin/reservation/R-20260401-001/decision` with `{"decision": "approved", "comment": "Spot confirmed"}`.
4. **Status Check**: User checks status and receives: "Great news! Your reservation has been approved. Admin note: Spot confirmed".

## Limitations

- **REST/Stub Integration**: The current admin notification is a stub and requires manual API/Agent calls for decisions.
- **No External Messaging**: Real notifications (Email/SMS) are not yet integrated.
- **Tool-based Agent**: The Admin Agent uses tools for execution but does not yet implement a full autonomous reasoning loop (LLM agent).
