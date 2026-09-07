# SupportOps AWS Infrastructure

This directory defines the AWS deployment foundation for SupportOps with Terraform.

## Architecture

- A dedicated VPC across two Availability Zones
- Two public subnets and an internet gateway
- An internet-facing Application Load Balancer
- Separate frontend and backend ECS Fargate services
- Separate immutable ECR repositories with scan-on-push
- Security groups that allow container ingress only from the ALB
- CloudWatch log groups with finite retention
- Optional AWS Secrets Manager references for database and AI credentials

The Fargate tasks use public IP addresses so they can pull images and reach external APIs without a NAT Gateway. They remain unreachable directly because their security groups accept inbound traffic only from the ALB.

## Cost guardrail

Both ECS desired counts default to zero. Terraform can create the deployment foundation without starting application tasks. An ALB and some other AWS resources can still incur charges after `terraform apply`.

No command in CI applies this configuration.

## Validation

```bash
cd infra
terraform init
terraform fmt -check -recursive
terraform validate
```

## Deployment sequence

1. Review `terraform plan` and expected cost.
2. Apply the foundation.
3. Build the frontend with an empty `VITE_API_BASE_URL` so browser API calls remain on the ALB origin.
4. Push frontend and backend images to the output ECR repository URLs using one immutable tag.
5. Create the PostgreSQL database and store `DATABASE_URL` in AWS Secrets Manager.
6. Store optional AI API keys in Secrets Manager.
7. Set the secret ARN variables, image tag, and both desired counts to one.
8. Apply again and verify ALB target health.

HTTPS, AWS WAF, managed database infrastructure, WAF logging, and automated image deployment are intentionally added in later stages.
