# AWS WAF security controls

The regional web ACL is associated directly with the SupportOps Application Load Balancer.

## Rule order

| Priority | Rule | Behaviour |
| --- | --- | --- |
| 0 | ChatRateLimit | Blocks a source IP after the configured request threshold to `/chat` |
| 10 | AmazonIpReputation | Uses the AWS IP reputation managed rule group |
| 20 | CommonThreats | Uses the AWS core rule set for common application attacks |
| 30 | KnownBadInputs | Blocks request patterns associated with exploitation and discovery |
| 40 | SQLInjection | Adds the AWS SQL database managed rule group |

The web ACL allows requests that do not match a blocking rule.

## Logging and privacy

Only non-allowed requests are retained in the dedicated CloudWatch log group. The `authorization` and `cookie` headers are redacted before delivery. Retention defaults to 14 days.

The CloudWatch dashboard includes:

- allowed and blocked request totals
- a five-minute blocked-request single value
- blocked requests grouped by terminating rule
- the 20 most recent blocked requests with IP, method, URI, and rule

## Tuning workflow

1. Deploy rules to the dev environment.
2. Send known benign application traffic.
3. Review sampled requests and blocked-event logs.
4. Identify the exact managed sub-rule responsible for any false positive.
5. Add the narrowest possible rule action override or scope-down condition.
6. Run the security regression suite again.
7. Record the reason for the exception in the pull request.

Avoid disabling an entire managed group to fix one false positive. Never paste production authorization headers, cookies, or request bodies into issues or pull requests.

## Cost note

AWS WAF requests, CloudWatch log ingestion, retention, and Logs Insights queries can incur charges after deployment. Logging is filtered to omit allowed traffic to reduce volume.
