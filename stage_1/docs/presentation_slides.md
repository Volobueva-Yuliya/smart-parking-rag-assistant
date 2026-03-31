# Presentation: Smart Parking RAG Assistant
## Stage 1: Prototype Development

### Slide 1: Title Slide
- **Project Name:** Smart Parking RAG Assistant
- **Subtitle:** An Intelligent Solution for Urban Parking Management
- **Presenter:** JetBrains AI (Junie)
- **Facility:** Central Plaza Parking, Tbilisi

### Slide 2: Problem Statement
- **Customer Frustration:** Difficulty finding accurate parking rules and pricing information.
- **Manual Overhead:** Human staff spending excessive time on repetitive booking tasks.
- **Data Fragmentation:** Information scattered between static brochures and dynamic availability records.
- **Goal:** Provide a 24/7 intelligent interface for all parking-related needs.

### Slide 3: Solution Overview
- **Hybrid AI Assistant:** Combines the flexibility of Generative AI with the reliability of SQL databases.
- **Three-Pillar Approach:**
  1. **Informational:** RAG pipeline for complex QA.
  2. **Operational:** SQLite-based deterministic booking.
  3. **Security:** Rule-based guardrails for data safety.

### Slide 4: Architecture Diagram
- [Visual: Flowchart showing User -> Chatbot Engine]
- **Engine Logic:** Routes input to Guardrails, RAG Pipeline, or Database.
- **Storage Layer:**
  - **Weaviate:** Vector store for semantic knowledge.
  - **SQLite:** Relational store for users and bookings.

### Slide 5: RAG Pipeline
- **Retriever:** Weaviate Vector DB using `all-MiniLM-L6-v2` embeddings.
- **Reranker:** Custom lightweight layer to boost specific sections (Pricing, Hours).
- **Generator:** GPT-4o-mini using strict context-injection prompts.
- **Output:** Accurate, non-hallucinated answers about parking services.

### Slide 6: Data Storage
- **Static Knowledge (Weaviate):**
  - Rules, Pricing, Location, FAQ.
  - Ingested from Markdown with overlap chunking.
- **Dynamic Data (SQLite):**
  - Real-time Slot Counts (General, EV, Accessible).
  - User Profiles (Name, Plate).
  - Reservation History (Append-only).

### Slide 7: Chatbot Flow
- **Intent Priority:**
  1. Active Booking (Highest Priority)
  2. Guardrails (Greeting/Security/Scope)
  3. Operational (Status/Availability)
  4. RAG (Informational)
- **Outcome:** Predictable and reliable user interaction.

### Slide 8: Booking Flow
- **Deterministic 6-Step Process:**
  1. Name Collection (First/Last)
  2. Plate Identification
  3. Time Definition (Start/End)
  4. Summary Review
  5. User Confirmation
  6. SQLite Persistence
- **Session Memory:** Quick-reuse feature for repeat bookings.

### Slide 9: Evaluation Results
- **Recall@3:** 100% (The correct info is always found).
- **Recall@1:** 67% (Room for ranking improvement).
- **Latency:** ~310ms (Near-instant response).
- **Interpretation:** Highly reliable at finding information; reranking successfully compensates for semantic noise.

### Slide 10: Demo Examples
- **RAG:** "What happens if I park after 23:00?" -> "Staff assistance required..."
- **Operational:** "Do you have EV spaces?" -> "8/10 available."
- **Booking:** "Reserve a space for Anna Ivanova..." -> "Success! Code: R-20260331-001."

### Slide 11: Guardrails & Safety
- **Blocking Sensitive Data:** Prevents mass-listing of reservations.
- **Context Restriction:** LLM cannot use external knowledge.
- **Out-of-Scope:** Politely rejects non-parking queries (e.g., weather).

### Slide 12: Limitations and Next Steps
- **Limitations:** Term-based reranking is sensitive to specific keywords.
- **Next Steps:**
  - Admin Dashboard for 'pending' approval.
  - Integration with payment gateways.
  - Multilingual support (Georgian language).
