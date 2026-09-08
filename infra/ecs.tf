resource "aws_ecs_cluster" "main" {
  name = local.name_prefix

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.frontend_task.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${aws_ecr_repository.frontend.repository_url}:${var.image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.frontend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "frontend"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name_prefix}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.backend_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "CORS_ALLOWED_ORIGINS"
          value = var.cors_allowed_origins
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "WAF_WEB_ACL_NAME"
          value = aws_wafv2_web_acl.application.name
        },
        {
          name  = "WAF_WEB_ACL_ID"
          value = aws_wafv2_web_acl.application.id
        },
        {
          name  = "WAF_LOG_GROUP_NAME"
          value = aws_cloudwatch_log_group.waf.name
        },
        {
          name  = "PGHOST"
          value = aws_db_instance.database.address
        },
        {
          name  = "PGPORT"
          value = tostring(aws_db_instance.database.port)
        },
        {
          name  = "PGDATABASE"
          value = var.database_name
        }
      ]

      secrets = concat(
        [
          {
            name = "PGUSER"
            valueFrom = (
              "${aws_db_instance.database.master_user_secret[0].secret_arn}:username::"
            )
          },
          {
            name = "PGPASSWORD"
            valueFrom = (
              "${aws_db_instance.database.master_user_secret[0].secret_arn}:password::"
            )
          }
        ],
        var.database_url_secret_arn == null ? [] : [
          {
            name      = "DATABASE_URL"
            valueFrom = var.database_url_secret_arn
          }
        ],
        var.gemini_api_key_secret_arn == null ? [] : [
          {
            name      = "GEMINI_API_KEY"
            valueFrom = var.gemini_api_key_secret_arn
          }
        ],
        var.deepseek_api_key_secret_arn == null ? [] : [
          {
            name      = "DEEPSEEK_API_KEY"
            valueFrom = var.deepseek_api_key_secret_arn
          }
        ],
        var.admin_api_key_secret_arn == null ? [] : [
          {
            name      = "ADMIN_API_KEY"
            valueFrom = var.admin_api_key_secret_arn
          }
        ]
      )

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "frontend" {
  name            = "${local.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  platform_version = "LATEST"

  network_configuration {
    assign_public_ip = true
    security_groups  = [aws_security_group.frontend.id]
    subnets          = aws_subnet.public[*].id
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.http]
}

resource "aws_ecs_service" "backend" {
  name            = "${local.name_prefix}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  platform_version = "LATEST"

  network_configuration {
    assign_public_ip = true
    security_groups  = [aws_security_group.backend.id]
    subnets          = aws_subnet.public[*].id
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener_rule.backend]
}
