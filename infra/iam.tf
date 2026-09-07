data "aws_iam_policy_document" "ecs_task_execution_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${local.name_prefix}-ecs-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "application_secrets" {
  count = length(local.application_secret_arns) > 0 ? 1 : 0

  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = local.application_secret_arns
  }
}

resource "aws_iam_role_policy" "application_secrets" {
  count = length(local.application_secret_arns) > 0 ? 1 : 0

  name   = "${local.name_prefix}-application-secrets"
  role   = aws_iam_role.ecs_task_execution.id
  policy = data.aws_iam_policy_document.application_secrets[0].json
}

resource "aws_iam_role" "backend_task" {
  name               = "${local.name_prefix}-backend-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json
}

resource "aws_iam_role" "frontend_task" {
  name               = "${local.name_prefix}-frontend-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json
}

data "aws_iam_policy_document" "backend_security_observability" {
  statement {
    sid       = "ReadWafMetrics"
    actions   = ["cloudwatch:GetMetricStatistics"]
    resources = ["*"]
  }

  statement {
    sid       = "ReadSanitizedWafEvents"
    actions   = ["logs:FilterLogEvents"]
    resources = [aws_cloudwatch_log_group.waf.arn]
  }

  statement {
    sid       = "ReadWebAclConfiguration"
    actions   = ["wafv2:GetWebACL"]
    resources = [aws_wafv2_web_acl.application.arn]
  }
}

resource "aws_iam_role_policy" "backend_security_observability" {
  name   = "${local.name_prefix}-security-observability"
  role   = aws_iam_role.backend_task.id
  policy = data.aws_iam_policy_document.backend_security_observability.json
}
