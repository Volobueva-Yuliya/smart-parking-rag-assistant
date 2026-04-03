# Smart Parking RAG Assistant

A smart parking chatbot project that combines Retrieval-Augmented Generation (RAG) for information support with an automated booking workflow, human-in-the-loop administrative approval, and a finalized reservation processing service.

## Project Overview

This project implements a multi-stage intelligent parking assistant:
- **Stage 1** covers RAG-based information support (answering questions about parking rules, prices, etc.) and collecting all necessary booking details from users.
- **Stage 2** adds a human-in-the-loop reservation approval workflow, featuring a second administrative agent built using LangChain concepts.
- **Stage 3** introduces a lightweight MCP-style processing server that exports confirmed reservations to a persistent text ledger.

## Features

- **Informational Queries**: RAG pipeline using Weaviate and LLM to provide accurate answers from a knowledge base.
- **Booking Data Collection**: Automated identification and non-empty validation of user details (name, vehicle plate, time) for reservations.
- **SQLite-based Reservation Storage**: A single unified database for managing users, availability, and reservation records.
- **Reservation Approval Lifecycle**: Support for `pending_admin_approval`, `approved`, and `rejected` statuses.
- **Admin REST API**: A FastAPI-based service for administrators to review and decide on reservation requests.
- **Second LangChain-based Admin Agent**: A dedicated agent using LangChain tools (`@tool`) to process administrative decisions.
- **MCP-style Processing Server**: A FastAPI-based service for downstream processing and persistent storage of approved reservations.
- **Automated Tests**: A robust test suite using `pytest` covering all three stages, including database operations, business logic, and API flows.

## Project Structure

- **`parking.db`**: The unified SQLite database file located at the project root.
- **`stage_1/`**: Contains the core RAG pipeline, guardrails, and initial booking logic.
  - `app/`: Chatbot engine and database access modules.
  - `scripts/`: Initialization scripts for DB and knowledge base ingestion.
  - `tests/`: Unit and integration tests for Stage 1.
- **`stage_2/`**: Contains the reservation approval workflow and admin integration.
  - `db.py`: Extended database logic for reservation statuses and admin comments.
  - `booking_flow.py`: Validation logic and reservation finalization.
  - `admin_client.py`: Integration layer for submitting requests to administrators.
  - `admin_api.py`: FastAPI REST service for administrative actions.
  - `admin_agent.py`: LangChain-based second agent for processing decisions.
  - `chatbot_flow.py`: User-facing interaction logic for Stage 2 (confirmation and status checks).
  - `tests/`: Unit and integration tests for Stage 2.
- **`stage_3/`**: Contains the lightweight MCP-style processing server.
  - `app/`: FastAPI server, authentication, and file-writing logic.
  - `storage/`: Persistent storage for confirmed reservations and export state.
  - `tests/`: Unit, smoke, and synchronization tests for Stage 3.

## Stage 1

Stage 1 established the foundation:
- **RAG-based Information Support**: Retrieval from Weaviate and generation via OpenAI.
- **Booking Data Collection**: Logic to extract first name, last name, plate number, and times from user input.
- **Guardrails**: Safety mechanisms for routing and filtering user queries.
- **Initial DB Schema**: Tables for users, parking lots, and reservations.

## Stage 2

Stage 2 introduced the administrative layer:
- **Reservation Lifecycle**: New statuses: `pending_admin_approval`, `approved`, `rejected`.
- **Admin Workflow**: Automatic submission of pending requests to the admin integration layer.
- **Shared DB State**: Unified path handling for `parking.db` across all modules.
- **Admin API**: RESTful endpoints for fetching reservations and submitting decisions.
- **Admin Agent**: A second agent using LangChain tools to manage approvals and rejections.

## Stage 3

Stage 3 finalized the downstream flow:
- **MCP-style Server**: A FastAPI service acting as a confirmed reservation processor.
- **Bearer Token Auth**: Secure API endpoints for manual and automated synchronization.
- **Export Logic**: Formatting and appending approved reservations to a persistent text ledger.
- **Idempotent Sync**: Local state tracking to prevent duplicate exports from the shared SQLite database.

## Reservation Workflow

1. **User Submits Reservation**: User provides all required booking fields to the chatbot.
2. **Confirmation**: Chatbot displays a summary and asks for explicit confirmation.
3. **Pending Status**: Once confirmed, a reservation is created in the DB with status `pending_admin_approval`.
4. **Admin Review**: The request is automatically forwarded for administrative review (simulated via `admin_client`).
5. **Approve/Reject**: Administrator uses the Admin API or Admin Agent to approve or reject the request, optionally adding a comment.
6. **Processing (Stage 3)**: The Stage 3 server synchronizes approved records into the finalized text ledger.
7. **User Checks Status**: User can query the status of their reservation using their unique code.

## Setup

### 1. Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Dependency Installation
```bash
pip install -r smart-parking-rag-assistent/stage_1/requirements.txt
pip install fastapi uvicorn pydantic langchain-core langchain-openai
```

### 3. Database Initialization
```bash
python3 smart-parking-rag-assistent/stage_1/scripts/init_db.py
```

### 4. Environment Variables
Ensure a `.env` file exists in the repository root with the following keys:
```text
OPENAI_API_KEY=your_openai_key
WEAVIATE_URL=your_weaviate_url
```

## Running the Project

### Running Stage 1 Chatbot
```bash
python3 smart-parking-rag-assistent/stage_1/app/chatbot.py
```

### Running Stage 2 Admin API
```bash
python3 -m uvicorn stage_2.admin_api:app --reload
```

### Running Stage 3 Processing Server
```bash
python3 -m uvicorn stage_3.app.mcp_server:app --port 8001 --reload
```

### Running Tests

**Stage 1 tests:**
```bash
python3 -m pytest stage_1/tests/
```

**Stage 2 tests:**
```bash
python3 -m pytest stage_2/tests/
```

**Stage 3 tests:**
```bash
python3 -m pytest stage_3/tests/
```

**All tests:**
```bash
python3 -m pytest stage_1/tests/ stage_2/tests/ stage_3/tests/
```

## Testing

The project uses **pytest** for automated verification. The test suite covers:
- **Database operations**: Schema extensions and status transitions.
- **Guardrails**: Safety filtering and intent routing.
- **Booking logic**: Completeness validation and summary generation.
- **RAG pipeline behavior**: Correct retrieval and generation flows.
- **Admin workflow**: End-to-end integration from submission to decision.
- **Processing and Sync**: Secure export of approved records and duplicate prevention in Stage 3.