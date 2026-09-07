variable "aws_region" {
  description = "AWS region for SupportOps infrastructure"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Project name used for AWS resource naming"
  type        = string
  default     = "supportops"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}
