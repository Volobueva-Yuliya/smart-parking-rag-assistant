# Stage 4: LangGraph Orchestration

This module introduces a unified orchestration layer using **LangGraph** to manage the full lifecycle of the smart parking assistant, from initial user query to administrative approval and data persistence.

## Overview

The primary goal of Stage 4 is to transition from isolated functional modules to a cohesive, stateful graph-based workflow. By using LangGraph, we achieve:
- **Unified Pipeline**: Integrating Stage 1 (RAG/Intent), Stage 2 (Approval), and Stage 3 (Export) into a single flow.
- **State Management**: Using a central `GraphState` to track user messages, extracted data, decisions, and results.
- **Dynamic Routing**: Intelligent transitions based on intent and administrative decisions.
- **Robustness**: Integrated error handling and status tracking at each node.

## Architecture

Stage 4 acts as the orchestrator for all previous stages:

1.  **Stage 1 Interaction**: Detects intent and handles informational queries via RAG.
2.  **Stage 2 Approval**: Manages the pending reservation and administrative decision flow.
3.  **Stage 3 Recording**: Exports approved reservations to the finalized text ledger.

### Integration Map
- **Stage 4** invokes **Stage 1** for intent classification and RAG retrieval.
- **Stage 4** invokes **Stage 2** for database operations and approval status updates.
- **Stage 4** invokes **Stage 3** for secure file export.

## Graph Structure

The workflow is defined as a `StateGraph` with the following nodes:

-   **`user_interaction`**: Classifies user intent (booking, info, greeting, etc.). If info, runs the RAG pipeline.
-   **`admin_approval`**: If a booking is requested, creates a pending entry and simulates an administrative decision.
-   **`data_recording`**: If approved, calls Stage 3 logic to write the reservation to the ledger.
-   **`final_response`**: Constructs the final message for the user based on the entire path taken.

### Routing Logic
-   After `user_interaction`: 
    -   If `intent == "booking"`, go to `admin_approval`.
    -   Otherwise, go to `final_response`.
-   After `admin_approval`:
    -   If `admin_decision == "approved"`, go to `data_recording`.
    -   Otherwise, go to `final_response`.

## Workflow Scenarios

1.  **Informational Request**: `User` -> `user_interaction` (RAG) -> `final_response` -> `End`.
2.  **Approved Reservation**: `User` -> `user_interaction` -> `admin_approval` (Approved) -> `data_recording` -> `final_response` -> `End`.
3.  **Rejected Reservation**: `User` -> `user_interaction` -> `admin_approval` (Rejected) -> `final_response` -> `End`.

## Design Decisions

-   **Separation of Concerns**: Stage 4 focuses strictly on orchestration. It reuses functions from Stages 1, 2, and 3 without reimplementing their core business logic.
-   **LangGraph for Statefulness**: Using a graph allows for easy visualization of the pipeline and consistent state handling across complex branching paths.
-   **Deterministic Admin Simulator**: For the orchestration demo, we use a simulator in the `admin_approval` node that reacts to keywords (e.g., "reject") to demonstrate both paths clearly.

## Setup and Installation

Ensure all dependencies from all stages are installed.

**macOS / Linux**

```bash
pip install -r requirements.txt
pip install -r stage_3/requirements.txt
pip install -r stage_4/requirements.txt
```

**Windows**

```powershell
pip install -r requirements.txt
pip install -r stage_3\requirements.txt
pip install -r stage_4\requirements.txt
```

## Running the Demo

Run the end-to-end demo to see all scenarios in action.

**macOS / Linux**

```bash
export PYTHONPATH=$(pwd)/smart-parking-rag-assistant
python3 smart-parking-rag-assistant/stage_4/run_demo.py
```

**Windows (PowerShell)**

```powershell
$env:PYTHONPATH = "$((Get-Location).Path)\smart-parking-rag-assistant"
python smart-parking-rag-assistant\stage_4\run_demo.py
```

## Validation

### Automated End-to-End Validation

We provide a dedicated validation script that sets up a clean environment, runs an approved flow, and verifies the file export.

**macOS / Linux**

```bash
export PYTHONPATH=$(pwd)/smart-parking-rag-assistant
python3 smart-parking-rag-assistant/stage_4/validate_e2e.py
```

**Windows (PowerShell)**

```powershell
$env:PYTHONPATH = "$((Get-Location).Path)\smart-parking-rag-assistant"
python smart-parking-rag-assistant\stage_4\validate_e2e.py
```

### Manual Inspection

1. Run the demo or validation script.
2. Check `smart-parking-rag-assistant/stage_3/storage/confirmed_reservations.txt` to see the exported lines.
3. Verify the format:

```text
Name | Car Number | Reservation Period | Approval Time
```

## Testing

Run the integration and smoke tests.

**macOS / Linux**

```bash
export PYTHONPATH=$(pwd)/smart-parking-rag-assistant
python3 -m pytest smart-parking-rag-assistant/stage_4/tests/
```

**Windows (PowerShell)**

```powershell
$env:PYTHONPATH = "$((Get-Location).Path)\smart-parking-rag-assistant"
python -m pytest smart-parking-rag-assistant\stage_4\tests\
```

Tests cover:

- Informational, booking, and greeting paths.
- Approved vs. rejected outcomes.
- Stage 3 failure handling.
- Performance validation for all key scenarios.
