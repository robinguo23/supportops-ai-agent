resource "aws_cloudwatch_dashboard" "security" {
  dashboard_name = "${local.name_prefix}-security"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 16
        height = 7

        properties = {
          title   = "WAF allowed and blocked requests"
          view    = "timeSeries"
          region  = var.aws_region
          stat    = "Sum"
          period  = 300
          stacked = false
          metrics = [
            [
              "AWS/WAFV2",
              "AllowedRequests",
              "WebACL",
              aws_wafv2_web_acl.application.name,
              "Region",
              var.aws_region,
              "Rule",
              "ALL",
              {
                color = "#2ca02c"
                label = "Allowed"
              }
            ],
            [
              ".",
              "BlockedRequests",
              ".",
              ".",
              ".",
              ".",
              ".",
              ".",
              {
                color = "#d62728"
                label = "Blocked"
              }
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 0
        width  = 8
        height = 7

        properties = {
          title  = "Blocked requests"
          view   = "singleValue"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            [
              "AWS/WAFV2",
              "BlockedRequests",
              "WebACL",
              aws_wafv2_web_acl.application.name,
              "Region",
              var.aws_region,
              "Rule",
              "ALL"
            ]
          ]
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 7
        width  = 12
        height = 7

        properties = {
          title  = "Blocked requests by rule"
          region = var.aws_region
          view   = "table"
          query = join(" ", [
            "SOURCE '${aws_cloudwatch_log_group.waf.name}'",
            "| filter action = 'BLOCK'",
            "| stats count() as requests by terminatingRuleId",
            "| sort requests desc"
          ])
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 7
        width  = 12
        height = 7

        properties = {
          title  = "Recent blocked requests"
          region = var.aws_region
          view   = "table"
          query = join(" ", [
            "SOURCE '${aws_cloudwatch_log_group.waf.name}'",
            "| filter action = 'BLOCK'",
            "| fields @timestamp, httpRequest.clientIp, httpRequest.httpMethod, httpRequest.uri, terminatingRuleId",
            "| sort @timestamp desc",
            "| limit 20"
          ])
        }
      }
    ]
  })
}
