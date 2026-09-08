# SupportOps AWS Infrastructure

This directory defines the AWS deployment foundation for SupportOps with Terraform.

## Architecture

- A dedicated VPC across two Availability Zones
- Two public subnets for the ALB and Fargate tasks
- Two private database subnets with no internet route
- An internet-facing Application Load Balancer protected by a regional AWS WAF web ACL
- Separate frontend and backend ECS Fargate services
- A private, encrypted RDS for PostgreSQL instance
- AWS-managed RDS master credentials in Secrets Manager
- Separate immutable ECR repositories with scan-on-push
- Security groups that allow container ingress only from the ALB and database ingress only from the backend
- AWS managed common-threat, known-bad-input, SQL injection, and IP reputation rules
- A custom per-IP rate limit scoped to `/chat`
- Blocked-request WAF logs with authorization and cookie headers redacted
- A CloudWatch security dashboard for WAF metrics and recent blocked events
- A read-only application security API protected by a default-deny WAF IP allowlist
- Admin ticket listing and status updates protected by an optional Secrets Manager API key
- CloudWatch application and PostgreSQL logs
- A least-privilege GitHub Actions OIDC role that can push only to the two application repositories

The Fargate tasks use public IP addresses so they can pull images and reach external APIs without a NAT Gateway. They remain unreachable directly because their security groups accept inbound traffic only from the ALB.

## Cost guardrail

Both ECS desired counts default to zero. RDS, ALB, storage, logs, and other AWS resources can still incur charges after `terraform apply`.

No CI workflow applies this configuration automatically.

The repository includes guarded CloudShell helpers:

```bash
# Bootstrap Terraform automatically, validate, and create a reviewed plan
bash scripts/deploy.sh plan

# Apply only the saved plan
bash scripts/deploy.sh apply

# Plan and apply in one interactive command
bash scripts/deploy.sh up

# Create an RDS snapshot, review a destroy plan, then destroy
CONFIRM_DESTROY=I_UNDERSTAND_DATA_WILL_BE_DELETED \
  bash scripts/destroy.sh
```

The destroy helper creates an RDS snapshot by default before deleting the stack. To intentionally delete the database without a snapshot, set `CREATE_SNAPSHOT=false`.

## Validation

The local helper downloads the pinned Terraform version (`1.9.8`) when Terraform is not already installed:

```bash
bash scripts/terraform.sh init
bash scripts/terraform.sh fmt -check -recursive
bash scripts/terraform.sh validate
```

GitHub Actions uses the same pinned Terraform version for formatting and validation.

## Bootstrap and deployment sequence

1. Review `terraform plan`, the resource list, and expected cost.
2. Apply the foundation from a trusted local environment or CloudShell.
3. Set the Terraform output `github_image_publisher_role_arn` as the repository Actions variable `AWS_PUBLISH_ROLE_ARN`.
4. Run the `Publish container images` workflow on the `main` branch.
5. Copy its immutable image tag into `image_tag`.
6. Set both desired counts to one and apply Terraform again.
7. Verify the frontend and backend target groups are healthy.
8. Open the `application_url` output.
9. Run the controlled WAF regression workflow.
10. Run the Application smoke tests workflow.
11. Set both desired counts back to zero when the demo is complete.

The backend receives the RDS host as environment configuration and the generated username/password through ECS secret injection. A full `DATABASE_URL` remains available as an optional override. Set `admin_api_key_secret_arn` to protect ticket listing and status updates; when it is unset, those endpoints deny access by default.

## Security regression coverage

The WAF regression suite requires an explicit ownership confirmation and checks:

- normal frontend health remains allowed;
- SQL injection is blocked;
- cross-site scripting is blocked;
- path traversal is blocked;
- known bad input is blocked;
- untrusted access to `/security-api` is blocked;
- repeated requests to `/chat` trigger the configured rate-based rule.

The rate-limit test is intentionally controlled and should only be run against an endpoint you own.

The application smoke workflow checks backend health, database connectivity, the out-of-scope chat guardrail, and unauthenticated ticket access. It does not create or modify tickets.

## Future infrastructure improvements

These are intentionally not enabled automatically because they require account-specific choices:

- S3 remote Terraform state with encryption and locking
- AWS Budget notifications with a user-selected email address
- HTTPS with an ACM certificate
- separate long-lived foundation and short-lived application stacks
