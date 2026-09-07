output "aws_region" {
  description = "AWS region used for deployment"
  value       = var.aws_region
}

output "resource_prefix" {
  description = "Prefix used for AWS resource names"
  value       = local.name_prefix
}
