import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/security-api", tags=["security"])


def get_setting(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise HTTPException(
            status_code=503,
            detail="Security observability is not configured in this environment.",
        )

    return value


def run_aws_call(call):
    try:
        return call()
    except (BotoCoreError, ClientError) as error:
        print(f"Security observability AWS request failed: {error}")
        raise HTTPException(
            status_code=502,
            detail="Security observability data is temporarily unavailable.",
        ) from error


def waf_dimensions(web_acl_name: str, region: str) -> list[dict[str, str]]:
    return [
        {"Name": "WebACL", "Value": web_acl_name},
        {"Name": "Region", "Value": region},
        {"Name": "Rule", "Value": "ALL"},
    ]


def metric_sum(
    client,
    metric_name: str,
    dimensions: list[dict[str, str]],
    start_time: datetime,
    end_time: datetime,
) -> int:
    response = run_aws_call(
        lambda: client.get_metric_statistics(
            Namespace="AWS/WAFV2",
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=["Sum"],
        )
    )

    return round(
        sum(point.get("Sum", 0) for point in response.get("Datapoints", []))
    )


def rule_action(rule: dict[str, Any]) -> str:
    if rule.get("Action"):
        return next(iter(rule["Action"])).upper()

    if rule.get("OverrideAction"):
        override = next(iter(rule["OverrideAction"])).upper()
        return "MANAGED" if override == "NONE" else f"MANAGED ({override})"

    return "UNKNOWN"


@router.get("/summary")
def security_summary():
    region = get_setting("AWS_REGION")
    web_acl_name = get_setting("WAF_WEB_ACL_NAME")
    cloudwatch = boto3.client("cloudwatch", region_name=region)

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=24)
    dimensions = waf_dimensions(web_acl_name, region)

    allowed = metric_sum(
        cloudwatch,
        "AllowedRequests",
        dimensions,
        start_time,
        end_time,
    )
    blocked = metric_sum(
        cloudwatch,
        "BlockedRequests",
        dimensions,
        start_time,
        end_time,
    )
    total = allowed + blocked

    return {
        "window_hours": 24,
        "allowed": allowed,
        "blocked": blocked,
        "total": total,
        "block_rate": round((blocked / total * 100) if total else 0, 2),
        "generated_at": end_time.isoformat(),
    }


@router.get("/rules")
def security_rules():
    region = get_setting("AWS_REGION")
    web_acl_name = get_setting("WAF_WEB_ACL_NAME")
    web_acl_id = get_setting("WAF_WEB_ACL_ID")
    waf = boto3.client("wafv2", region_name=region)

    response = run_aws_call(
        lambda: waf.get_web_acl(
            Name=web_acl_name,
            Scope="REGIONAL",
            Id=web_acl_id,
        )
    )

    rules = response.get("WebACL", {}).get("Rules", [])

    return {
        "rules": [
            {
                "name": rule.get("Name", "Unknown"),
                "priority": rule.get("Priority", 0),
                "action": rule_action(rule),
                "statement_type": next(
                    iter(rule.get("Statement", {"Unknown": {}}))
                ),
            }
            for rule in sorted(rules, key=lambda item: item.get("Priority", 0))
        ]
    }


@router.get("/events")
def security_events(limit: int = Query(default=50, ge=1, le=100)):
    region = get_setting("AWS_REGION")
    log_group_name = get_setting("WAF_LOG_GROUP_NAME")
    logs = boto3.client("logs", region_name=region)

    response = run_aws_call(
        lambda: logs.filter_log_events(
            logGroupName=log_group_name,
            limit=limit,
            interleaved=True,
        )
    )

    events = []

    for log_event in response.get("events", []):
        try:
            event = json.loads(log_event.get("message", "{}"))
        except json.JSONDecodeError:
            continue

        request = event.get("httpRequest", {})
        timestamp_ms = event.get("timestamp", log_event.get("timestamp", 0))

        events.append(
            {
                "timestamp": datetime.fromtimestamp(
                    timestamp_ms / 1000,
                    tz=timezone.utc,
                ).isoformat(),
                "source_ip": request.get("clientIp", "unknown"),
                "method": request.get("httpMethod", "unknown"),
                "uri": request.get("uri", "/"),
                "action": event.get("action", "UNKNOWN"),
                "rule": event.get("terminatingRuleId", "unknown"),
                "country": request.get("country", "unknown"),
            }
        )

    events.sort(key=lambda item: item["timestamp"], reverse=True)

    return {"events": events[:limit]}
