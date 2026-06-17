# SupportOps AI Agent

A full-stack AI customer support agent with RAG, tool calling, human handoff, and evaluation.

## Project Goal

This project aims to build a realistic AI customer support system rather than a simple chatbot. The agent will answer questions using a company knowledge base, call backend tools when needed, and decide when to escalate to a human support agent.

## Core Features

- Chat UI for customer support conversations
- RAG-based knowledge base for grounded answers
- Tool calling for order lookup and ticket creation
- Human handoff for low-confidence or sensitive cases
- Evaluation set for testing answer quality and tool use

## Tech Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI
- Database: PostgreSQL
- Vector Search: pgvector or Chroma
- LLM API: OpenAI / Gemini / Claude
- Deployment: To be decided

## Current Status

Project initialized. The next step is to build a minimal FastAPI backend with `/health` and `/chat` endpoints.
