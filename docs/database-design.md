# Database Design

## Purpose

The database is used to persist customer support data that should not disappear when the backend restarts.

The current system stores mock orders and support tickets in memory. This is useful for early prototyping, but it is not realistic for a customer support system. A real support agent needs persistent storage for orders, tickets, conversations, and messages.

<small>中文说明：数据库的作用是保存客服系统里的长期数据，比如订单、工单、对话和消息。现在的 mock ticket 存在内存里，后端重启后会丢失。</small>

---

## Core Tables

### 1. orders

Stores mock customer order information.

| Field | Type | Meaning |
|---|---|---|
| id | integer | Internal database ID |
| order_id | string | Public order ID, such as ORD-1001 |
| status | string | Order status, such as shipped or delivered |
| estimated_delivery | date | Estimated delivery date |
| carrier | string | Delivery carrier |
| created_at | timestamp | Record creation time |

<small>中文说明：orders 表用来保存订单信息。之后 `check_order_status()` 不再查 Python 字典，而是查数据库。</small>

---

### 2. support_tickets

Stores support tickets created by the agent.

| Field | Type | Meaning |
|---|---|---|
| id | integer | Internal database ID |
| ticket_id | string | Public ticket ID, such as TCK-1001 |
| issue_type | string | Refund, complaint, missing order, etc. |
| summary | text | Short summary of the user issue |
| status | string | open, in_progress, resolved, closed |
| created_at | timestamp | Ticket creation time |

<small>中文说明：support_tickets 表保存客服工单。以后用户查不到订单、申请退款或投诉时，系统会把 ticket 存进数据库。</small>

---

### 3. conversations

Stores each chat session.

| Field | Type | Meaning |
|---|---|---|
| id | integer | Internal database ID |
| conversation_id | string | Public conversation ID |
| created_at | timestamp | Conversation start time |

<small>中文说明：conversations 表保存一次完整客服对话。后面如果要做后台管理页面，就可以按 conversation 查看历史聊天。</small>

---

### 4. messages

Stores individual user and agent messages.

| Field | Type | Meaning |
|---|---|---|
| id | integer | Internal database ID |
| conversation_id | string | Related conversation |
| role | string | user or agent |
| content | text | Message content |
| tool_used | string | Tool name if a tool was used |
| needs_human_handoff | boolean | Whether handoff was needed |
| created_at | timestamp | Message creation time |

<small>中文说明：messages 表保存每一条用户和 Agent 消息。现在前端聊天记录刷新就没了，之后可以通过这个表持久化。</small>

---

## First Database Milestone

The first database milestone is not to build everything at once.

The first implementation target should be:

1. Connect FastAPI to PostgreSQL.
2. Create the `support_tickets` table.
3. Store created tickets in the database instead of in memory.
4. Keep the existing API response format unchanged.

<small>中文说明：第一阶段不要一次性接所有表。先把 support ticket 从内存迁移到 PostgreSQL，保持前端不用改。</small>

---

## Interview Explanation

I designed the initial database schema for the customer support agent. The goal is to move from in-memory mock data to persistent storage. I planned tables for orders, support tickets, conversations, and messages. The first implementation milestone is to persist support tickets in PostgreSQL while keeping the existing API contract stable.

<small>中文说明：面试时可以说：我先识别了当前 mock 数据的限制，然后设计数据库 schema，并计划逐步把内存数据迁移到 PostgreSQL。</small>