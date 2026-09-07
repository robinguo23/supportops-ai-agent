# AWS deployment runbook

This runbook records the controlled deployment sequence. Do not deploy from a pull request.

## Prerequisites

- An AWS account with permission to create the Terraform resources
- Terraform installed locally
- AWS credentials configured for the initial bootstrap
- A reviewed cost estimate and a cleanup plan

## 1. Review and create the foundation

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out=supportops.tfplan
terraform apply supportops.tfplan
```

The first apply creates networking, ALB, ECR, ECS definitions with zero running tasks, RDS, logging, and the GitHub image-publisher role.

## 2. Configure GitHub OIDC publishing

Copy the `github_image_publisher_role_arn` Terraform output into a repository Actions variable named `AWS_PUBLISH_ROLE_ARN`.

The role trust policy accepts tokens only from the `main` branch of this repository. Its permissions are limited to authenticating with ECR and pushing images to the SupportOps frontend and backend repositories.

## 3. Publish immutable images

Run `Publish container images` from GitHub Actions. Leave the tag empty to use the commit SHA. Record the tag printed in the workflow summary.

## 4. Start the application

Set the recorded tag and desired counts in `terraform.tfvars`:

```hcl
image_tag             = "<commit-sha>"
frontend_desired_count = 1
backend_desired_count  = 1
```

Review and apply the new plan. The backend creates the `vector` extension and application tables during startup.

## 5. Verify

- Both ALB target groups report healthy targets.
- The application URL loads the frontend.
- `/health` returns the frontend health response through the default route.
- A POST to `/chat` is routed to FastAPI.
- Backend and PostgreSQL logs are visible in CloudWatch.

## Cleanup

Set desired counts to zero before troubleshooting or teardown. For this dev environment, final snapshots and deletion protection default to disabled. Review those settings before using the configuration for persistent data.
