# SupportOps Infrastructure

This directory contains the Terraform configuration for the SupportOps cloud security deployment.

The current foundation defines provider requirements, shared naming, tags, inputs, and outputs. It intentionally creates no AWS resources yet.

## Local validation

```bash
cd infra
terraform init
terraform fmt -check
terraform validate
terraform plan
```

Copy `terraform.tfvars.example` to `terraform.tfvars` only when you need local overrides. Do not commit `terraform.tfvars` or Terraform state files.
