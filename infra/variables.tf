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

variable "database_name" {
  description = "Initial PostgreSQL database name"
  type        = string
  default     = "supportops"
}

variable "database_master_username" {
  description = "RDS master username; the password is generated and managed by AWS"
  type        = string
  default     = "supportops_admin"
}

variable "database_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "database_allocated_storage" {
  description = "Initial RDS storage in GiB"
  type        = number
  default     = 20
}

variable "database_max_allocated_storage" {
  description = "Maximum RDS autoscaled storage in GiB"
  type        = number
  default     = 50
}

variable "database_multi_az" {
  description = "Deploy a standby database in another Availability Zone"
  type        = bool
  default     = false
}

variable "database_backup_retention_days" {
  description = "Number of days to retain automated database backups"
  type        = number
  default     = 1
}

variable "database_deletion_protection" {
  description = "Protect the RDS instance from accidental deletion"
  type        = bool
  default     = false
}

variable "database_skip_final_snapshot" {
  description = "Skip a final snapshot when deleting the RDS instance"
  type        = bool
  default     = true
}

variable "database_url_secret_arn" {
  description = "Optional Secrets Manager ARN containing a full DATABASE_URL override"
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

variable "github_repository" {
  description = "GitHub repository allowed to publish application images"
  type        = string
  default     = "robinguo23/supportops-ai-agent"
}

variable "github_oidc_thumbprint" {
  description = "SHA-1 thumbprint for the GitHub Actions OIDC provider certificate"
  type        = string
  default     = "6938fd4d98bab03faadb97b34396831e3780aea1"
}

variable "chat_rate_limit" {
  description = "Maximum requests from one source IP to /chat in a five-minute window"
  type        = number
  default     = 100

  validation {
    condition     = var.chat_rate_limit >= 10
    error_message = "Chat rate limit must be at least 10 requests."
  }
}

variable "waf_log_retention_days" {
  description = "Retention period for blocked-request WAF logs"
  type        = number
  default     = 14
}

variable "security_admin_ipv4_cidrs" {
  description = "Trusted public IPv4 CIDRs allowed to access /security-api; empty blocks everyone"
  type        = list(string)
  default     = []
}
