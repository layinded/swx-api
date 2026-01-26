# Alert Model Design

This document defines the structured alert model used in SwX-API for production-grade alerting and monitoring.

## 1. Alert Taxonomy

Alerts are structured events designed to supplemental audit logs with actionable information. Unlike audit logs which record every state change, alerts signify that something requires attention.

### 1.1 Severity Levels

| Level | Description | Recommended Channels |
|-------|-------------|----------------------|
| `info` | Normal but significant events. | Logs |
| `warning` | Potential issues that don't block service. | Logs, Slack (low priority) |
| `error` | Errors that affect a single request or user. | Logs, Slack |
| `critical` | System-wide issues or security breaches. | Logs, Slack, Email, Pager |

### 1.2 Alert Sources

- `api`: General API request handling errors.
- `auth`: Authentication failures, token issues.
- `rbac`: Authorization denials, permission escalations.
- `audit`: Failures in the audit logging system.
- `system`: Lifecycle events (startup, shutdown, background tasks).
- `infra`: Infrastructure issues (database connectivity, cache failure).

### 1.3 Event Types

Each source should define specific event types. Examples:
- `auth`: `LOGIN_FAILURE_BURST`, `TOKEN_REUSE_DETECTED`.
- `infra`: `DATABASE_CONNECTION_LOST`, `MIGRATION_FAILED`.
- `rbac`: `PERMISSION_DENIED_SENSITIVE_RESOURCE`.

## 2. Data Model

Every alert must contain the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `alert_id` | `UUID` | Unique identifier for the alert instance. |
| `timestamp` | `DateTime` | UTC timestamp when the alert was emitted. |
| `source` | `Enum` | Source of the alert (`api`, `auth`, etc.). |
| `event_type` | `String` | Specific type of event (e.g. `LOGIN_FAILURE`). |
| `severity` | `Enum` | Severity level (`info`, `warning`, `error`, `critical`). |
| `environment` | `String` | Deployment environment (`dev`, `staging`, `prod`). |
| `actor_type` | `Enum` | Type of actor (`system`, `admin`, `user`, `none`). |
| `actor_id` | `String` | ID of the actor if applicable. |
| `resource_type`| `String` | Type of resource affected. |
| `resource_id` | `String` | ID of the resource affected. |
| `message` | `String` | Short, human-readable summary. |
| `metadata` | `JSON` | Structured details (no secrets). |

## 3. Security Rules

- **No Secrets**: Metadata MUST NOT contain passwords, JWTs, API keys, or raw PII.
- **Redaction**: The alert engine should perform recursive redaction on metadata keys known to contain sensitive data.
- **Fail Safe**: Alerting failures must not block primary request handling.
