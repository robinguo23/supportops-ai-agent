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
- CloudWatch application and PostgreSQL logs
- A least-privilege GitHub Actions OIDC role that can push only to the two application repositories

The Fargate tasks use public IP addresses so they can pull images and reach external APIs without a NAT Gateway. They remain unreachable directly because their security groups accept inbound traffic only from the ALB.

## Cost guardrail

Both ECS desired counts default to zero. RDS, ALB, storage, logs, and other AWS resources will still incur charges after `terraform apply`.

No CI workflow applies this configuration automatically.

## Validation

```bash
cd infra
terraform init
terraform fmt -check -recursive
terraform validate
```

## Bootstrap and deployment sequence

1. Review `terraform plan`, the resource list, and expected cost.
2. Apply the foundation from a trusted local environment.
3. Set the Terraform output `github_image_publisher_role_arn` as the repository Actions variable `AWS_PUBLISH_ROLE_ARN`.
4. Run the `Publish container images` workflow on the `main` branch.
5. Copy its immutable image tag into `image_tag`.
6. Set both desired counts to one and apply Terraform again.
7. Verify the frontend and backend target groups are healthy.
8. Open the `application_url` output.

The backend receives the RDS host as environment configuration and the generated username/password through ECS secret injection. A full `DATABASE_URL` remains available as an optional override.

HTTPS, remote Terraform state, automated ECS rollout, and the React security operations view are intentionally added in later stages.
