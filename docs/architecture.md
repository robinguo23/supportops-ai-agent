# SupportOps AI Agent - Architecture

## 1. Project Overview

SupportOps AI Agent is a full-stack customer support assistant prototype.

The system allows users to ask support questions through a React chat interface. The backend uses FastAPI, PostgreSQL, pgvector, and Gemini embeddings to retrieve relevant support policy documents and return grounded answers. If the user is not satisfied with the answer, they can explicitly request human support, which creates a support ticket.

<small>中文说明：这是一个全栈 AI 客服系统原型。用户通过前端聊天提问，后端用 RAG 检索客服政策文档并回答。只有用户明确请求人工支持时，系统才创建 ticket。</small>

---

## 2. High-Level System Architecture

```text
React Frontend
    ↓
FastAPI Backend
    ↓
PostgreSQL
    ├── support_tickets
    └── knowledge_chunks + pgvector embeddings
    ↓
Gemini Embedding API
```

The main components are:

* React frontend for chat interaction and ticket administration;
* FastAPI backend for API routes and business logic;
* PostgreSQL for persistent support tickets and knowledge chunks;
* pgvector for semantic similarity search;
* Gemini embedding service for document and query embeddings;
* Markdown support documents as the source knowledge base.

<small>中文说明：系统由 React 前端、FastAPI 后端、PostgreSQL 数据库、pgvector 向量检索、Gemini embedding 和本地 Markdown 知识库组成。</small>

---

## 3. Frontend Architecture

The frontend is built with React and TypeScript.

Main responsibilities:

* display chat messages;
* send user questions to `/chat`;
* display RAG answers, sources, and similarity scores;
* manage feedback buttons such as `Yes, solved`, `Continue asking`, and `No, I need help`;
* call `/tickets/escalate` only when the user explicitly requests human support;
* display and update support tickets in the admin panel.

Key files:

```text
frontend/src/
├── App.tsx
├── types.ts
├── config/api.ts
└── components/
    ├── ChatPanel.tsx
    └── AdminTicketsPanel.tsx
```

<small>中文说明：前端负责聊天展示、按钮状态、人工转接触发、source 展示和 admin ticket 面板。</small>

---

## 4. Backend Architecture

The backend is built with FastAPI.

Main responsibilities:

* receive chat messages;
* check order IDs;
* detect out-of-scope questions;
* generate query embeddings;
* retrieve relevant knowledge chunks with pgvector;
* return grounded support answers with source metadata;
* create tickets only through explicit escalation;
* provide ticket listing and ticket status update APIs.

Key backend structure:

```text
backend/app/
├── api/
│   └── chat.py
├── db/
│   ├── session.py
│   ├── models.py
│   └── init_db.py
├── data/
│   └── support_documents/
├── models/
│   └── chat.py
├── services/
│   ├── document_chunking.py
│   ├── embedding_service.py
│   └── knowledge_base.py
└── tools/
    ├── knowledge_chunk_tools.py
    ├── order_tools.py
    └── ticket_tools.py
```

<small>中文说明：后端负责核心业务逻辑，包括订单查询、RAG 检索、out-of-scope 判断、ticket escalation 和 ticket 管理。</small>

---

## 5. Database Design

The system currently uses PostgreSQL with pgvector.

### `support_tickets`

Stores human support tickets.

Main fields:

* `id`
* `ticket_id`
* `issue_type`
* `summary`
* `status`
* `created_at`

Tickets are only created when the user explicitly requests human support through the escalation flow.

<small>中文说明：support_tickets 表保存人工支持工单。现在只有用户明确点击人工转接时才创建 ticket。</small>

### `knowledge_chunks`

Stores support policy document chunks and embeddings.

Main fields:

* `id`
* `document_id`
* `title`
* `content`
* `source`
* `embedding`
* `created_at`

The `embedding` column uses pgvector with 1536 dimensions.

<small>中文说明：knowledge_chunks 表保存文档 chunk、来源信息和 Gemini 生成的 1536 维 embedding。</small>

---

## 6. RAG Pipeline

The RAG pipeline contains two stages: document ingestion and query-time retrieval.

### 6.1 Document Ingestion

```text
Markdown support documents
→ document chunking
→ Gemini document embeddings
→ insert into PostgreSQL knowledge_chunks table
```

The support documents are stored as Markdown files under:

```text
backend/app/data/support_documents/
```

The ingestion script reads these documents, splits them into chunks, generates embeddings, and stores them in PostgreSQL.

<small>中文说明：文档写成 Markdown，然后切分成 chunks，调用 Gemini 生成 embedding，再写入 PostgreSQL。</small>

### 6.2 Query-Time Retrieval

```text
User question
→ Gemini query embedding
→ pgvector cosine similarity search
→ retrieve top matching chunks
→ return answer with source metadata
```

The backend uses pgvector cosine distance to rank knowledge chunks by semantic similarity.

<small>中文说明：用户提问后，后端把问题转成 query embedding，再用 pgvector 和数据库里的 chunk embeddings 做相似度检索。</small>

---

## 7. Chat Flow

The main `/chat` endpoint follows this decision flow:

```text
User message
↓
Check if message contains an order ID
↓
If known order:
    return order status and ask for feedback
↓
If unknown order:
    ask whether the user wants human support
↓
If out of support domain:
    return out-of-scope message
    do not create ticket
↓
If support-related:
    generate query embedding
    retrieve policy chunks using pgvector
↓
If top similarity >= threshold:
    return RAG answer with sources
    ask whether the answer solved the issue
↓
If top similarity < threshold:
    ask whether the user wants human support
```

<small>中文说明：/chat 的核心逻辑是：先查订单，再判断是否支持范围内，再做 RAG 检索。只有用户明确转人工才创建 ticket。</small>

---

## 8. Feedback-Based Escalation Flow

The system uses a feedback-based escalation workflow.

After a RAG answer, the frontend shows:

```text
Yes, solved
Continue asking
No, I need help
```

If the user clicks `Yes, solved`:

```text
The system thanks the user and closes the current conversation.
```

If the user clicks `Continue asking`:

```text
The input box is unlocked and the user can ask a follow-up question.
```

If the user clicks `No, I need help`:

```text
The system asks whether the user wants human support.
```

Then the user can choose:

```text
Request human support
End chat
```

Only `Request human support` calls:

```text
POST /tickets/escalate
```

and creates a support ticket.

<small>中文说明：系统不是看到 refund、damaged、charged twice 就自动建 ticket，而是先用 RAG 回答，再让用户选择是否解决。只有用户点击人工支持时才建 ticket。</small>

---

## 9. Out-of-Scope Guardrail

The system includes an out-of-scope guardrail.

Examples of out-of-scope questions:

```text
What is the weather today?
Tell me a joke.
Who is the Prime Minister?
```

For these questions, the system should:

* not answer from support policy documents;
* not show irrelevant sources;
* not create a ticket;
* allow the user to ask a new support-related question.

<small>中文说明：天气、笑话、政治人物这类问题不属于客服范围。系统不应该乱答，也不应该创建 ticket。</small>

---

## 10. API Endpoints

### Chat

```text
POST /chat
```

Receives a user message and returns a support assistant response.

### Escalation

```text
POST /tickets/escalate
```

Creates a support ticket after the user explicitly requests human support.

### Tickets

```text
GET /tickets
PATCH /tickets/{ticket_id}/status
```

Lists support tickets and updates ticket status.

### Knowledge Search

```text
GET /knowledge/search
GET /knowledge/vector-search
```

Provides keyword-based and vector-based knowledge search endpoints for testing and debugging retrieval behaviour.

<small>中文说明：主要 API 包括聊天、人工转接、ticket 管理和知识库检索调试接口。</small>

---

## 11. Testing Strategy

The backend test suite verifies the main support workflow.

Important behaviours tested:

* health check works;
* known order returns order status;
* unknown order asks for escalation but does not create a ticket;
* out-of-scope questions do not create tickets;
* refund, damaged item, and billing issues use RAG and do not automatically create tickets;
* only `/tickets/escalate` creates a ticket;
* ticket listing and status update work;
* vector search tests mock embedding generation to avoid real Gemini API calls.

<small>中文说明：测试重点验证新的业务规则：RAG 回答不自动建 ticket，只有用户明确人工转接才建 ticket。</small>

---

## 12. Design Decisions

### Why PostgreSQL + pgvector?

The project already uses PostgreSQL for support ticket persistence. Using pgvector keeps structured data and vector search in one database instead of adding another vector database service.

<small>中文说明：选择 pgvector 是因为项目已经使用 PostgreSQL，这样 ticket 数据和向量检索都在同一个数据库里，更容易解释和部署。</small>

### Why Gemini embeddings?

Gemini embeddings can output 1536-dimensional vectors, matching the current `vector(1536)` database schema.

<small>中文说明：选择 Gemini embedding 是因为可以输出 1536 维，和当前数据库表结构匹配。</small>

### Why feedback-based escalation?

Automatically creating tickets from keywords can produce noisy or unnecessary tickets. The feedback-based workflow first attempts self-service resolution through RAG and escalates only after explicit user confirmation.

<small>中文说明：反馈式转人工更真实。系统先尝试用知识库解决问题，只有用户确认需要人工时才创建 ticket。</small>

---

## 13. Current Limitations

Current limitations include:

* no real authentication;
* no multi-user conversation persistence;
* no production deployment;
* no LLM answer generation beyond returning retrieved chunks;
* support documents are manually written Markdown files;
* conversation state is currently managed on the frontend;
* no advanced retrieval evaluation dataset yet.

<small>中文说明：当前项目还是原型，没有认证、多用户会话持久化、生产部署，也还没有完整的检索评估集。</small>

---

## 14. Future Improvements

Possible next improvements:

* persist conversations and messages in PostgreSQL;
* add authentication for admin ticket management;
* improve document chunking strategy;
* add retrieval evaluation queries;
* generate natural answers from retrieved chunks using an LLM;
* add deployment with Docker;
* add CI tests;
* improve frontend design and accessibility.

<small>中文说明：后续可以做会话持久化、认证、检索评估、LLM 生成回答、Docker 部署和 CI 测试。</small>
