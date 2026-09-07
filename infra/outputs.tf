output "aws_region" {
  description = "AWS region used for deployment"
  value       = var.aws_region
}

output "resource_prefix" {
  description = "Prefix used for AWS resource names"
  value       = local.name_prefix
}

output "vpc_id" {
  description = "SupportOps VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs used by the ALB and Fargate tasks"
  value       = aws_subnet.public[*].id
}

output "database_subnet_ids" {
  description = "Private subnet IDs used by RDS"
  value       = aws_subnet.database[*].id
}

output "alb_dns_name" {
  description = "Public DNS name of the application load balancer"
  value       = aws_lb.application.dns_name
}

output "application_url" {
  description = "HTTP URL for the SupportOps application before HTTPS is configured"
  value       = "http://${aws_lb.application.dns_name}"
}

output "backend_ecr_repository_url" {
  description = "ECR repository URL for the backend image"
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_repository_url" {
  description = "ECR repository URL for the frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "database_endpoint" {
  description = "Private RDS PostgreSQL endpoint"
  value       = aws_db_instance.database.endpoint
}

output "database_master_secret_arn" {
  description = "Secrets Manager ARN containing the generated RDS credentials"
  value       = aws_db_instance.database.master_user_secret[0].secret_arn
}

output "github_image_publisher_role_arn" {
  description = "Set this value as the GitHub Actions variable AWS_PUBLISH_ROLE_ARN"
  value       = aws_iam_role.github_image_publisher.arn
}

output "waf_web_acl_arn" {
  description = "ARN of the regional AWS WAF web ACL"
  value       = aws_wafv2_web_acl.application.arn
}

output "waf_log_group_name" {
  description = "CloudWatch log group containing blocked WAF requests"
  value       = aws_cloudwatch_log_group.waf.name
}

output "security_dashboard_name" {
  description = "CloudWatch security dashboard name"
  value       = aws_cloudwatch_dashboard.security.dashboard_name
}
