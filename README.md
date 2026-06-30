# SupportOps AI Agent

A full-stack AI customer support assistant prototype built with React, FastAPI, PostgreSQL, pgvector, Gemini embeddings, and DeepSeek-V4-Flash.

The system answers customer support questions using a RAG pipeline over local support policy documents. It retrieves relevant policy chunks from PostgreSQL using pgvector semantic search, generates grounded customer-friendly answers with DeepSeek-V4-Flash, displays source metadata and similarity scores, and only creates human support tickets after explicit user escalation.

---

## 1. Overview

SupportOps AI Agent is designed as a customer support workflow prototype.

It supports:

- RAG-based support question answering;
- grounded LLM answer generation from retrieved policy chunks;
- order status lookup using backend tools;
- source-aware answers with similarity scores;
- non-blocking feedback after RAG answers;
- explicit human support escalation;
- support ticket creation;
- admin ticket viewing and status updates.

The project focuses on building an explainable support workflow rather than a generic chatbot.

The assistant first attempts to resolve support questions using retrieved policy documents. The retrieved policy chunks are then passed to DeepSeek-V4-Flash to generate a more natural customer support answer. If the answer does not solve the issue, the user can explicitly request human support, which creates a support ticket.

---

## 2. Key Features

### RAG-Based Support Answers

The backend retrieves relevant support policy chunks using:

- local Markdown support documents;
- document chunking;
- Gemini-generated embeddings;
- PostgreSQL + pgvector;
- cosine similarity search.

Example user question:

```text
Can I return an item after delivery?
```

Example generated answer:

```text
Yes, you can return most items within 30 days of delivery, as long as they are unused, undamaged, and in their original packaging. Please include your order ID when contacting support about the return.
```

The frontend also displays source metadata and similarity scores.

---

### Grounded LLM Answer Generation

The backend uses a two-stage RAG flow.

First, it retrieves relevant support policy chunks from PostgreSQL using Gemini embeddings and pgvector semantic search.

Then, it sends the retrieved chunks to DeepSeek-V4-Flash to generate a more natural customer support answer.

The LLM does not replace retrieval. It only generates the final response based on the retrieved support policy context.

This keeps answers more natural while still grounding them in company policy documents.

---

### Non-Blocking Feedback-Based Escalation Flow

After a support answer, the frontend asks whether the answer solved the issue.

The user can choose:

```text
Yes, solved
No, I need help
```

The input box remains available after a RAG answer, so the user can naturally ask a follow-up question or provide missing information such as an order ID.

If the user continues typing, the previous feedback buttons are automatically deactivated.

If the user chooses `No, I need help`, the system asks whether they want human support.

Only during this explicit escalation confirmation stage is the input box locked.

Only when the user clicks `Request human support` does the backend create a ticket.

This avoids creating unnecessary tickets from keywords such as `refund`, `damaged`, or `charged twice`.

---

### Human Support Ticket Lifecycle

Support tickets are stored in PostgreSQL.

The admin panel can:

- list support tickets;
- view ticket summaries;
- update ticket status from `open` to `resolved`.

Tickets are created only through the explicit escalation endpoint:

```text
POST /tickets/escalate
```

---

### Out-of-Scope Guardrail

The assistant only handles support-related questions about:

- orders;
- returns;
- refunds;
- delivery;
- damaged items;
- billing issues.

Out-of-scope questions such as weather or jokes are rejected without creating tickets.

Example:

```text
What is the weather today?
```

Response:

```text
I can only help with support questions about orders, returns, refunds, delivery, damaged items, or billing issues.
```

---

## 3. Tech Stack

### Frontend

- React
- TypeScript
- Vite
- CSS

### Backend

- FastAPI
- Python
- Pydantic
- SQLAlchemy

### Database

- PostgreSQL
- pgvector

### AI / Retrieval

- Gemini Embedding API
- DeepSeek-V4-Flash chat generation
- 1536-dimensional embeddings
- PostgreSQL + pgvector
- cosine similarity search
- grounded answer generation from retrieved support policy chunks

### Testing

- pytest
- FastAPI TestClient
- mocked embedding/vector search for stable tests

---

## 4. System Architecture

```text
React Frontend
    ↓
FastAPI Backend
    ├── Gemini Embedding API
    ├── DeepSeek-V4-Flash Answer Generation
    ↓
PostgreSQL
    ├── support_tickets
    └── knowledge_chunks + pgvector embeddings
```

Main backend responsibilities:

- receive chat messages;
- detect order IDs;
- detect out-of-scope questions;
- generate query embeddings;
- retrieve relevant document chunks with pgvector;
- generate grounded answers from retrieved chunks;
- return source metadata and similarity scores;
- create tickets only through explicit escalation.

For more detail, see:

```text
docs/architecture.md
```

---

## 5. RAG Pipeline

### Document Ingestion

Support policies are stored as Markdown files:

```text
backend/app/data/support_documents/
```

The ingestion pipeline is:

```text
Markdown support documents
→ document chunking
→ Gemini document embeddings
→ PostgreSQL knowledge_chunks table
```

The ingestion script reads the documents, splits them into chunks, generates embeddings, and inserts them into PostgreSQL.

### Query-Time Retrieval and Generation

At query time:

```text
User question
→ Gemini query embedding
→ pgvector cosine similarity search
→ retrieve top matching chunks
→ DeepSeek-V4-Flash answer generation
→ return grounded answer with source metadata
```

The system first retrieves relevant support policy chunks from PostgreSQL. Then DeepSeek-V4-Flash generates a customer-friendly answer using only the retrieved policy context.

The frontend still displays source metadata and similarity scores from the retrieval layer.

---

## 6. Project Structure

```text
supportops-ai-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── chat.py
│   │   ├── data/
│   │   │   └── support_documents/
│   │   ├── db/
│   │   │   ├── init_db.py
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   └── chat.py
│   │   ├── services/
│   │   │   ├── answer_generation_service.py
│   │   │   ├── document_chunking.py
│   │   │   ├── embedding_service.py
│   │   │   └── knowledge_base.py
│   │   └── tools/
│   │       ├── knowledge_chunk_tools.py
│   │       ├── order_tools.py
│   │       └── ticket_tools.py
│   ├── scripts/
│   │   ├── insert_knowledge_chunks.py
│   │   ├── preview_document_chunks.py
│   │   └── test_gemini_embedding.py
│   └── tests/
│       └── test_chat_api.py
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── types.ts
│       ├── config/
│       │   └── api.ts
│       └── components/
│           ├── ChatPanel.tsx
│           └── AdminTicketsPanel.tsx
├── docs/
│   └── architecture.md
├── docker-compose.yml
└── README.md
```

---

## 7. Local Setup

### 7.1 Start PostgreSQL

The project uses Docker Compose for PostgreSQL with pgvector.

```bash
docker compose up -d
```

The local database uses port `5433` to avoid conflicts with local PostgreSQL installations.

---

### 7.2 Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```env
DATABASE_URL=postgresql://supportops:supportops_dev_password@localhost:5433/supportops

GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_EMBEDDING_DIMENSION=1536

DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_CHAT_MODEL=deepseek-v4-flash
```

Do not commit the real `.env` file.

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

---

### 7.3 Insert Knowledge Chunks

After adding or editing support policy documents, regenerate embeddings and insert chunks into PostgreSQL:

```bash
cd backend
source .venv/bin/activate
python scripts/insert_knowledge_chunks.py
```

This script:

```text
loads Markdown documents
→ chunks the documents
→ generates Gemini embeddings
→ stores chunks in PostgreSQL
```

---

### 7.4 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

---

## 8. Main API Endpoints

### Chat

```text
POST /chat
```

Receives a user message and returns a support assistant response.

### Human Escalation

```text
POST /tickets/escalate
```

Creates a ticket only when the user explicitly requests human support.

### Tickets

```text
GET /tickets
PATCH /tickets/{ticket_id}/status
```

Lists tickets and updates ticket status.

### Knowledge Search

```text
GET /knowledge/search
GET /knowledge/vector-search
```

Debug endpoints for keyword search and vector search.

---

## 9. Testing

Run backend tests:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
```

The test suite verifies:

- health check;
- known order lookup;
- unknown order escalation prompt;
- out-of-scope guardrail;
- RAG answers without automatic ticket creation;
- explicit escalation ticket creation;
- ticket listing;
- ticket status update;
- vector search endpoint behaviour.

Embedding and vector search are mocked in tests to avoid relying on the real Gemini API during automated test runs.

---

## 10. Demo Flow

Recommended demo sequence:

### 1. RAG Answer

Ask:

```text
Can I return an item after delivery?
```

Expected:

```text
Generated return policy answer
Sources shown
Similarity score shown
```

### 2. Natural Follow-Up

After the RAG answer, the input box remains available.

Ask:

```text
How long does a refund take?
```

Expected:

```text
Generated refund policy answer
Sources shown
Similarity score shown
```

### 3. Missing Information Follow-Up

Ask:

```text
I want to return my shoes.
```

Expected:

```text
Generated answer asking for relevant return information, such as order ID
Input box remains available
User can continue typing the order ID directly
```

Then ask:

```text
My order ID is ORD-1001.
```

Expected:

```text
Order status lookup response
```

### 4. Out-of-Scope Guardrail

Ask:

```text
What is the weather today?
```

Expected:

```text
Out-of-scope message
No ticket created
```

### 5. Explicit Human Escalation

Ask:

```text
I want a refund.
```

Expected:

```text
Generated refund policy answer
No ticket created automatically
```

Click:

```text
No, I need help
Request human support
```

Expected:

```text
Support ticket created
```

### 6. Admin Panel

Check the admin panel:

```text
Ticket appears
Ticket can be marked resolved
```

---

## 11. Design Decisions

### Why pgvector?

The project already uses PostgreSQL for support tickets. pgvector allows semantic retrieval to be implemented inside the same database instead of adding a separate vector database service.

### Why Gemini Embeddings?

Gemini embeddings can generate 1536-dimensional vectors, which match the project’s `vector(1536)` schema in PostgreSQL.

### Why DeepSeek for Answer Generation?

The project uses Gemini for embeddings and DeepSeek-V4-Flash for answer generation.

Gemini embeddings are used for semantic retrieval over support policy documents. DeepSeek is used only after retrieval, to generate a customer-friendly answer grounded in the retrieved chunks.

This separates retrieval from generation and keeps the system explainable.

### Why Feedback-Based Escalation?

Automatically creating tickets from keywords can create noisy and unnecessary support tickets. The feedback-based flow first tries to resolve the issue using RAG and only escalates after explicit user confirmation.

### Why Non-Blocking RAG Feedback?

After a RAG answer, users may still want to continue the conversation or provide missing information. For example, if the assistant asks for an order ID, the user should be able to type it directly.

Therefore, the frontend does not lock the input after a normal RAG answer. It only locks the input during explicit human escalation confirmation.

### Why Mock External AI Calls in Tests?

Tests should be fast, deterministic, and safe to run without consuming API quota. Therefore, embedding generation and vector search results are mocked in backend tests.

---

## 12. Current Limitations

This is still a prototype. Current limitations include:

- no authentication;
- no user accounts;
- no multi-user conversation persistence;
- conversation state is currently managed on the frontend;
- support documents are manually written Markdown files;
- no production deployment;
- no advanced retrieval evaluation dataset yet.

---

## 13. Future Improvements

Possible future improvements:

- persist conversations and messages in PostgreSQL;
- add authentication for admin ticket management;
- add retrieval evaluation queries;
- improve chunking strategy;
- add stricter hallucination checks for generated answers;
- add Dockerized full-stack deployment;
- add CI testing;
- improve UI design and accessibility.

---

## 14. Interview Summary

This project demonstrates a full-stack AI support workflow with a real RAG retrieval and generation backend.

I built a React and FastAPI customer support assistant that stores support tickets in PostgreSQL and retrieves policy documents using Gemini embeddings and pgvector. The retrieved policy chunks are passed to DeepSeek-V4-Flash to generate grounded, customer-friendly answers.

I designed a feedback-based escalation flow so users can continue asking follow-up questions after a RAG answer, while tickets are only created after explicit human support confirmation. I also added source-aware responses, similarity scores, out-of-scope guardrails, and mocked backend tests to keep the system reliable and explainable.