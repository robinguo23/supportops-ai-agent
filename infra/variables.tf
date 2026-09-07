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

variable "vpc_cidr" {
  description = "CIDR block for the SupportOps VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "alb_ingress_cidrs" {
  description = "IPv4 CIDR blocks allowed to reach the public ALB"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "image_tag" {
  description = "Immutable image tag deployed by both ECS services"
  type        = string
  default     = "bootstrap"
}

variable "frontend_desired_count" {
  description = "Number of frontend Fargate tasks; keep at zero until an image is pushed"
  type        = number
  default     = 0

  validation {
    condition     = var.frontend_desired_count >= 0
    error_message = "Frontend desired count must be zero or greater."
  }
}

variable "backend_desired_count" {
  description = "Number of backend Fargate tasks; keep at zero until images and secrets are ready"
  type        = number
  default     = 0

  validation {
    condition     = var.backend_desired_count >= 0
    error_message = "Backend desired count must be zero or greater."
  }
}

variable "database_url_secret_arn" {
  description = "Optional Secrets Manager ARN containing the backend DATABASE_URL"
  type        = string
  default     = null
  nullable    = true
}

variable "gemini_api_key_secret_arn" {
  description = "Optional Secrets Manager ARN containing GEMINI_API_KEY"
  type        = string
  default     = null
  nullable    = true
}

variable "deepseek_api_key_secret_arn" {
  description = "Optional Secrets Manager ARN containing DEEPSEEK_API_KEY"
  type        = string
  default     = null
  nullable    = true
}

variable "cors_allowed_origins" {
  description = "Comma-separated origins allowed by the FastAPI CORS middleware"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log retention period"
  type        = number
  default     = 14
}

variable "enable_deletion_protection" {
  description = "Protect the ALB from accidental deletion"
  type        = bool
  default     = false
}
