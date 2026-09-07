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
