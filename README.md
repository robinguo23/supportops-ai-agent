# SupportOps AI Agent

A containerised customer-support application demonstrating secure cloud delivery, AWS WAF protection, Terraform infrastructure as code, and automated security regression testing.

## Security and infrastructure

- AWS WAF attached to an Application Load Balancer
- AWS managed rules for IP reputation, common web threats, known bad inputs and SQL injection
- Custom rate limiting for the /chat endpoint
- Trusted IPv4 restriction for the /security-api endpoint
- WAF logs delivered to CloudWatch Logs
- Restricted Security dashboard for rules, allowed requests and blocked requests
- ECS Fargate frontend and backend services
- PostgreSQL with pgvector on Amazon RDS
- Secrets Manager injection for database and application secrets
- GitHub Actions OIDC for temporary AWS credentials
- Immutable ECR image tags
- Terraform-managed infrastructure
- Guarded destroy workflow with optional RDS snapshots

## Architecture

~~~text
Internet
   |
AWS WAF
   |-- managed threat rules
   |-- SQL injection protection
   |-- IP reputation
   |-- /chat rate limiting
   |-- /security-api IP restriction
   |
Application Load Balancer
   |              |
React/Nginx     FastAPI
frontend        backend
                   |
                PostgreSQL + pgvector

WAF logs -> CloudWatch Logs -> restricted Security dashboard
GitHub -> Actions + OIDC -> ECR -> ECS
Terraform -> VPC, ALB, WAF, ECS, RDS, ECR, IAM and logging
~~~

## WAF regression tests

The controlled regression suite runs only against an owned deployment.

~~~text
Normal health check       200
SQL injection             403
Cross-site scripting      403
Path traversal            403
Known bad input           403
Untrusted Security API    403
Chat rate limit           403 after AWS evaluation delay
~~~

The rate-based test accounts for delayed AWS WAF evaluation. It sends threshold traffic and polls for the resulting block instead of assuming that the threshold request is blocked immediately.

Run from GitHub Actions:

~~~text
Actions -> WAF security regression -> Run workflow
~~~

Required inputs:

~~~text
target_url:                 URL of an owned SupportOps deployment
ownership_confirmation:     I_OWN_THIS_TARGET
~~~

## Application smoke tests

The smoke-test workflow verifies:

- backend health;
- PostgreSQL health;
- the out-of-scope chat guardrail;
- unauthenticated admin ticket access is denied.

The latest validation completed with 4/4 tests passing. The WAF regression suite completed with 7/7 tests passing.

## Application features

- RAG-based support answers using policy documents
- Gemini embeddings and PostgreSQL/pgvector retrieval
- DeepSeek answer generation grounded in retrieved context
- source metadata and similarity scores
- order-status lookup
- out-of-scope request guardrails
- explicit human-support escalation
- PostgreSQL-backed support tickets
- admin ticket management protected by an API key

## Technology

Frontend: React, TypeScript, Vite, Nginx

Backend: Python, FastAPI, Pydantic, SQLAlchemy

Cloud and security: AWS WAF, ALB, ECS Fargate, RDS PostgreSQL, ECR, Secrets Manager, CloudWatch Logs, IAM, Terraform and GitHub Actions OIDC

Testing: pytest, FastAPI TestClient, Python HTTP security tests and controlled WAF regression tests

## Repository structure

~~~text
backend/                         FastAPI application and tests
frontend/                        React application
infra/                           Terraform infrastructure
security-tests/                  Application and WAF regression tests
scripts/                         Deployment and guarded destroy helpers
.github/workflows/               CI and security workflows
docs/                            Architecture documentation
~~~

## Local development

Start PostgreSQL:

~~~bash
docker compose up -d
~~~

Set up the backend:

~~~bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
~~~

Create backend/.env with local credentials. Never commit real API keys or .env files.

~~~bash
uvicorn app.main:app --reload
~~~

Start the frontend:

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

## Terraform deployment

Create local variables from the example:

~~~bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
~~~

Store API keys in AWS Secrets Manager and configure only their ARNs in Terraform:

~~~hcl
gemini_api_key_secret_arn   = "arn:..."
deepseek_api_key_secret_arn = "arn:..."
admin_api_key_secret_arn    = "arn:..."
~~~

The helper scripts bootstrap the pinned Terraform version when required:

~~~bash
cd infra
bash ../scripts/deploy.sh plan
bash ../scripts/deploy.sh apply
~~~

Publish images through GitHub Actions, set image_tag to the immutable commit SHA, then set both ECS desired counts to 1. After testing, set both counts back to 0 or destroy the environment.

For safe destruction:

~~~bash
cd infra
CONFIRM_DESTROY=I_UNDERSTAND_DATA_WILL_BE_DELETED bash ../scripts/destroy.sh
~~~

The destroy helper creates an RDS snapshot before destruction when an RDS instance exists.

## Design decisions

### WAF-first controls

The project uses a small, explainable set of managed and custom WAF controls: common attack protection, API rate limiting and IP restriction for sensitive security data.

### Restricted security data

The Security dashboard is not publicly readable. The /security-api path is allowed only for an explicitly configured trusted public IPv4 address.

### Secrets and deployment traceability

Secrets are stored in Secrets Manager and injected into ECS tasks at runtime. Container images use commit SHA tags, so each ECS deployment is traceable and repeatable.

### Short-lived cloud environments

This is a demonstration environment. RDS, ALB, WAF and CloudWatch resources can continue to incur charges even when ECS desired counts are zero. Destroy the environment when it is not needed.

## summary

> I built a containerised FastAPI and React support application and deployed it with Terraform to AWS. I protected the ALB with AWS WAF managed rule groups, custom rate limiting and IP restrictions for sensitive security data. WAF logs are sent to CloudWatch and exposed through a restricted security dashboard. GitHub Actions uses OIDC and immutable ECR image tags. I wrote controlled Python regression tests covering SQL injection, XSS, path traversal, bad input, access control and rate limiting, including the delayed evaluation behaviour of AWS WAF rate-based rules.
