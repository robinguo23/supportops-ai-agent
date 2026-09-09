# SupportOps AI Agent

A RAG-based customer support application built with React, FastAPI, PostgreSQL and pgvector.

The application answers customer questions using support-policy documents, retrieves relevant knowledge with semantic search, generates grounded responses, and escalates to human support when the user explicitly requests it.

## What the application does

- Answers support questions about orders, returns, refunds, delivery and billing
- Retrieves relevant policy documents using Gemini embeddings and pgvector
- Generates customer-friendly answers using retrieved policy context
- Displays source metadata and similarity scores
- Looks up order status
- Rejects out-of-scope questions without creating tickets
- Creates support tickets only after explicit escalation
- Provides an admin interface for reviewing and resolving tickets
- Protects admin ticket operations with an API key

## RAG flow

~~~text
Support policy documents
        |
Document chunking and embeddings
        |
PostgreSQL + pgvector
        |
User question -> semantic retrieval
        |
Retrieved context -> grounded answer
        |
Optional explicit human escalation
~~~

## Secure AWS deployment

The application can be deployed as a short-lived development environment on AWS using Terraform.

The deployment includes:

- React frontend running behind Nginx
- FastAPI backend on ECS Fargate
- Application Load Balancer
- PostgreSQL on Amazon RDS
- Amazon ECR container registries
- AWS Secrets Manager for database and API secrets
- AWS WAF attached to the Application Load Balancer
- CloudWatch WAF logging
- GitHub Actions with OIDC-based AWS access
- Terraform-managed networking, IAM and application infrastructure

AWS WAF provides the security layer around the application:

- Amazon IP reputation managed rule
- Common web-threat managed rule
- Known-bad-input managed rule
- SQL injection managed rule
- Rate limiting for the /chat endpoint
- Trusted IPv4 restriction for the /security-api endpoint

The Security page reads restricted WAF data and shows deployed rules, request totals, allowed requests, blocked requests and block rate.

## Validation

The application smoke-test workflow validates:

- backend health;
- PostgreSQL health;
- the out-of-scope chat guardrail;
- unauthenticated admin ticket access.

The WAF regression workflow validates:

- normal application traffic;
- SQL injection blocking;
- cross-site scripting blocking;
- path traversal blocking;
- known-bad-input blocking;
- restricted Security API access;
- /chat rate limiting.

The latest validation completed successfully:

~~~text
Application smoke tests: 4/4 passed
WAF security regression: 7/7 passed
~~~

The rate-limit test accounts for the delayed evaluation behaviour of AWS WAF rate-based rules by polling after the request threshold is reached.

## Technology

Application:

- React
- TypeScript
- Vite
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- pgvector

AI and retrieval:

- Gemini Embedding API
- DeepSeek answer generation
- cosine similarity search
- grounded response generation

Cloud and delivery:

- AWS WAF
- Application Load Balancer
- ECS Fargate
- Amazon RDS
- Amazon ECR
- AWS Secrets Manager
- CloudWatch Logs
- IAM
- Terraform
- GitHub Actions OIDC
- Docker

Testing:

- pytest
- FastAPI TestClient
- Python HTTP smoke tests
- controlled WAF regression tests

## Repository structure

~~~text
backend/                         FastAPI application and tests
frontend/                        React application
infra/                           Terraform AWS infrastructure
security-tests/                  Application and WAF tests
scripts/                         Deployment and guarded destroy helpers
.github/workflows/               CI, image publishing and security workflows
docs/                            Architecture documentation
~~~

## Local development

Start PostgreSQL:

~~~bash
docker compose up -d
~~~

Set up and run the backend:

~~~bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
~~~

Run the frontend:

~~~bash
cd frontend
npm install
npm run dev
~~~

Run backend tests:

~~~bash
cd backend
python -m pytest -q
~~~

Create backend/.env for local development. Never commit real API keys or .env files.

## AWS deployment

Create local Terraform variables from the example:

~~~bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
~~~

Store API keys in AWS Secrets Manager and configure only their ARNs in terraform.tfvars.

~~~hcl
gemini_api_key_secret_arn   = "arn:..."
deepseek_api_key_secret_arn = "arn:..."
admin_api_key_secret_arn    = "arn:..."
~~~

Deploy the infrastructure:

~~~bash
cd infra
bash ../scripts/deploy.sh plan
bash ../scripts/deploy.sh apply
~~~

Container images are published with immutable commit SHA tags. After publishing an image, set image_tag to that SHA and set the ECS desired counts to 1 for a demonstration.

When the demonstration is complete, set the desired counts back to 0 or destroy the environment. The guarded destroy helper can create an RDS snapshot before destruction:

~~~bash
cd infra
CONFIRM_DESTROY=I_UNDERSTAND_DATA_WILL_BE_DELETED bash ../scripts/destroy.sh
~~~

## Design choices

### RAG before escalation

The assistant first tries to answer using support-policy context. A ticket is created only after explicit user confirmation, reducing unnecessary escalations.

### Secrets outside source control

API keys and database credentials are stored in Secrets Manager and injected into ECS tasks at runtime.

### Restricted security data

The Security page is not publicly readable. Access to /security-api is limited to an explicitly configured trusted public IPv4 address.

### Immutable deployments

ECS task definitions reference container images by commit SHA, making deployments traceable and repeatable.

### Short-lived environments

The AWS environment is intended for demonstrations and testing. RDS, ALB, WAF and CloudWatch resources may continue to incur charges even when ECS tasks are stopped.
