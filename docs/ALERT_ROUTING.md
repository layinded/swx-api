# Alert Routing Policy

This document describes how alerts are routed to different delivery channels based on their severity, source, and environment.

## 1. Delivery Channels

The system currently supports:
- `log`: Structured JSON logs (always enabled).
- `slack`: Slack webhook integration.
- `email`: SMTP-based email delivery.
- `sms`: Stub interface for SMS delivery.

## 2. Routing Rules

Routing is determined by the `AlertEngine._get_target_channels()` method.

| Severity | Environment | Source | Channels |
|----------|-------------|--------|----------|
| `info` | Any | Any | `log` |
| `warning` | Any | `auth`, `rbac` | `log`, `slack` |
| `warning` | Any | Others | `log` |
| `error` | `production`| Any | `log`, `slack` |
| `error` | Others | Any | `log` |
| `critical` | Any | Any | `log`, `slack`, `email` |

### 2.1 Rule Logic

1. **Always Log**: Every alert is sent to the `log` channel.
2. **Critical Priority**: Critical alerts are dispatched to `slack` and `email` regardless of environment.
3. **Production Guard**: Errors in `production` environment trigger `slack` notifications.
4. **Security Focus**: Authentication or Authorization alerts (`auth`, `rbac`) with `warning` severity or higher trigger `slack` notifications even in non-production environments.

## 3. Configuration

Channels are configured via environment variables:

| Variable | Description |
|----------|-------------|
| `SLACK_WEBHOOK_URL` | Webhook URL for Slack channel. |
| `ALERT_EMAIL_RECIPIENTS` | Comma-separated list of email addresses. |
| `SMTP_HOST`, etc. | Core SMTP settings (shared with system emails). |

## 4. Async Dispatch

Alert dispatching is non-blocking. The `AlertEngine` uses `asyncio.create_task` to send alerts in the background, ensuring request handling performance is never degraded by alerting latency or failures.
