# SupportOps AI Agent

A full-stack AI customer support agent prototype with chat interaction, tool calling, human handoff, support ticket persistence, and an admin ticket panel.


## Overview

SupportOps AI Agent is a full-stack customer support application built with React, FastAPI, PostgreSQL, and Docker.

The project demonstrates how a customer support agent can move beyond simple chat responses and interact with backend business workflows. The current version supports order status lookup, support ticket creation, ticket persistence, ticket listing, and ticket status updates.


## Core Features

* Customer chat interface
* Basic human handoff detection
* Order status lookup tool
* Support ticket creation tool
* PostgreSQL persistence for support tickets
* Admin ticket panel in React
* Ticket status update workflow
* Backend API tests with pytest
* Docker-based local PostgreSQL setup

<small>中文说明：当前已经完成聊天界面、人工转接、订单查询、创建工单、数据库保存、后台工单列表、状态更新和后端测试。</small>

## Tech Stack

### Frontend

* React
* TypeScript
* Vite

### Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* psycopg
* pytest

### Infrastructure

* Docker Compose
* PostgreSQL 16

## Project Structure

```text
supportops-ai-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── chat.py
│   │   ├── data/
│   │   │   └── mock_data.py
│   │   ├── db/
│   │   │   ├── init_db.py
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   └── chat.py
│   │   ├── services/
│   │   │   └── handoff.py
│   │   ├── tools/
│   │   │   ├── order_tools.py
│   │   │   └── ticket_tools.py
│   │   └── main.py
│   └── tests/
│       └── test_chat_api.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AdminTicketsPanel.tsx
│   │   │   └── ChatPanel.tsx
│   │   ├── config/
│   │   │   └── api.ts
│   │   ├── types.ts
│   │   └── App.tsx
├── docs/
│   └── database-design.md
├── docker-compose.yml
└── README.md
```

## Current Workflow

### 1. Known Order Lookup

If the user asks about a known order ID, such as `ORD-1001`, the backend extracts the order ID, calls the order lookup tool, and returns the order status.

```text
User message
→ POST /chat
→ extract_order_id()
→ check_order_status()
→ return order information
```

### 2. Unknown Order Escalation

If the user asks about an unknown order ID, such as `ORD-9999`, the backend creates a support ticket and marks the case as requiring human support.

```text
Unknown order ID
→ check_order_status()
→ order not found
→ create_support_ticket()
→ persist ticket in PostgreSQL
```

### 3. Refund or Complaint Handoff

If the user asks for a refund or makes a complaint, the backend detects the handoff intent, classifies the issue type, creates a support ticket, and persists it in PostgreSQL.

```text
Refund / complaint message
→ should_handoff_to_human()
→ classify_issue_type()
→ create_support_ticket()
→ save ticket to PostgreSQL
```

### 4. Admin Ticket Management

The frontend admin panel can retrieve persisted tickets and mark them as resolved.

```text
GET /tickets
→ display tickets in admin panel
→ PATCH /tickets/{ticket_id}/status
→ update ticket status
```

## API Endpoints

| Method | Endpoint                      | Description                                  |
| ------ | ----------------------------- | -------------------------------------------- |
| GET    | `/health`                     | Check backend service status                 |
| GET    | `/db/health`                  | Check PostgreSQL connection                  |
| POST   | `/chat`                       | Send a customer message to the support agent |
| GET    | `/tickets`                    | List persisted support tickets               |
| PATCH  | `/tickets/{ticket_id}/status` | Update support ticket status                 |

## Local Setup

### 1. Start PostgreSQL

```bash
docker compose up -d
```

Check the container:

```bash
docker compose ps
```

### 2. Configure Environment Variables

Create a local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Example database URL:

```env
DATABASE_URL=postgresql://supportops:supportops_dev_password@localhost:5433/supportops
```

### 3. Start Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Backend API runs at:

```text
http://127.0.0.1:8000
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

## Testing

Run backend tests:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
```

The tests cover:

* health check
* known order lookup
* unknown order escalation
* refund ticket creation
* ticket listing
* ticket status update

## Current Limitations

* The order data is still mock data.
* Human handoff detection is keyword-based.
* The project does not yet include RAG.
* There is no authentication for the admin panel.
* The frontend UI is intentionally minimal.


## Next Steps

* Add RAG knowledge base for FAQ and policy documents
* Add conversation and message persistence
* Improve issue classification with LLM-based intent detection
* Add authentication for admin users
* Improve frontend UI and dashboard metrics
* Prepare deployment configuration

## Interview Summary

This project demonstrates a full-stack AI application workflow. I built a React frontend, a FastAPI backend, PostgreSQL persistence, Docker-based local infrastructure, backend tool functions, support ticket lifecycle management, and automated API tests. The project focuses on making an AI customer support agent more action-oriented by connecting conversation logic with backend business workflows.

