# Audit Log Security & Privacy

This document outlines the security and privacy measures implemented in the SwX-API audit logging system to ensure data protection and compliance.

## Sensitive Data Protection

### Automatic Redaction
The `AuditLogger` service automatically filters and redacts sensitive information from the `context` metadata before it is persisted to the database. The following keys (case-insensitive) are always redacted:
- `password`
- `hashed_password`
- `token`
- `access_token`
- `refresh_token`
- `secret`
- `secret_key`
- `client_secret`
- `authorization`
- `cookie`

### No PII in Unstructured Fields
Explicit effort must be made to avoid logging Personally Identifiable Information (PII) in unstructured fields like `action` or `resource_type`. Actor IDs and Resource IDs are logged as identifiers, which should be cross-referenced with the main identity system under appropriate access controls.

## Data Integrity & Immutability

### Append-Only Storage
The `audit_log` table is designed to be append-only. 
- **No Updates**: The API does not provide any endpoints to update existing audit logs.
- **No Deletes**: The API does not provide any endpoints to delete audit logs.
- **Database Constraints**: In production, it is recommended to enforce these rules at the database level using triggers or user permissions.

### Server-Side Timestamps
All timestamps are generated server-side using UTC to prevent manipulation by clients and ensure consistency across distributed systems.

## Access Control

### Role-Based Access Control (RBAC)
Access to audit logs is strictly controlled via RBAC:
- **System Operators**: Can view all audit logs across the entire system for forensic and compliance purposes.
- **Admin Users**: Can view audit logs scoped to their tenant or domain.
- **Normal Users**: Generally do not have access to the raw audit log API, though specific application-level logs (e.g., "login history") may be exposed via dedicated, restricted endpoints.

### Read-Only API
The audit log API endpoints are strictly read-only (`GET` only). No `POST`, `PUT`, `PATCH`, or `DELETE` operations are permitted on the audit log resource.

## Forensic Analysis

### Request Tracing
The `AuditMiddleware` ensures that every request is assigned a unique `request_id`. This ID is captured in the audit log and returned in the `X-Request-ID` response header, allowing for end-to-end tracing of actions across different system components.

### Comprehensive Context
Where appropriate, the system captures additional context such as:
- IP Address
- User-Agent
- Outcome (Success/Failure)
- Actor Type and ID
- Detailed (but safe) metadata about the action performed
