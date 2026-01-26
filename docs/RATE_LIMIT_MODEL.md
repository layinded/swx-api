# Rate Limit Model

**Date:** 2026-01-25  
**Status:** Design Complete

---

## Overview

Multi-layer rate limiting system that is:
- **Identity-aware** - Different limits per user/actor
- **Billing-aware** - Limits based on subscription plan
- **Feature-aware** - Different limits per feature
- **Endpoint-aware** - Different limits per endpoint class
- **Fail-closed** - Default deny if uncertain
- **Observable** - All decisions logged
- **Alertable** - Abuse triggers alerts

---

## Rate Limit Dimensions

### 1. Actor Type
Different limits based on who is making the request:
- **System** - Internal system calls (highest limits)
- **Admin** - Admin users (high limits)
- **User** - Regular users (plan-based limits)
- **Anonymous** - Unauthenticated requests (lowest limits)

### 2. Billing Plan
Limits scale with subscription:
- **Free** - Basic limits
- **Pro** - Higher limits
- **Team** - Shared limits per team
- **Enterprise** - Custom limits

### 3. Feature
Different limits per feature:
- **API Requests** - General API calls
- **Billing Operations** - Billing-related endpoints
- **Data Export** - Export operations
- **Search** - Search queries
- **Webhooks** - Webhook deliveries

### 4. Endpoint Class
Different limits per endpoint type:
- **Read** - GET requests (higher limits)
- **Write** - POST/PUT/PATCH (lower limits)
- **Delete** - DELETE requests (lowest limits)
- **Admin** - Admin endpoints (separate limits)

---

## Limit Types

### Burst Limits
Short-term spikes allowed:
- **Per-minute** - Immediate burst capacity
- Example: 100 requests/minute for Pro users

### Sustained Limits
Long-term average:
- **Per-hour** - Hourly average
- **Per-day** - Daily average
- Example: 10,000 requests/hour, 100,000 requests/day for Pro users

---

## Limit Structure

```python
{
    "actor_type": "user",
    "plan": "pro",
    "feature": "api_requests",
    "endpoint_class": "read",
    "limits": {
        "burst": {
            "window": "1m",
            "max": 100
        },
        "sustained": {
            "window": "1h",
            "max": 10000
        },
        "daily": {
            "window": "24h",
            "max": 100000
        }
    }
}
```

---

## Default Limits

### Free Tier
```python
{
    "api_requests": {
        "read": {"burst": 60, "sustained": 1000, "daily": 10000},
        "write": {"burst": 20, "sustained": 500, "daily": 5000},
        "delete": {"burst": 10, "sustained": 100, "daily": 1000}
    },
    "billing": {
        "read": {"burst": 10, "sustained": 100, "daily": 1000},
        "write": {"burst": 5, "sustained": 50, "daily": 500}
    }
}
```

### Pro Tier
```python
{
    "api_requests": {
        "read": {"burst": 200, "sustained": 10000, "daily": 100000},
        "write": {"burst": 100, "sustained": 5000, "daily": 50000},
        "delete": {"burst": 50, "sustained": 1000, "daily": 10000}
    },
    "billing": {
        "read": {"burst": 50, "sustained": 1000, "daily": 10000},
        "write": {"burst": 20, "sustained": 500, "daily": 5000}
    }
}
```

### Admin
```python
{
    "api_requests": {
        "read": {"burst": 1000, "sustained": 100000, "daily": 1000000},
        "write": {"burst": 500, "sustained": 50000, "daily": 500000},
        "delete": {"burst": 200, "sustained": 10000, "daily": 100000}
    }
}
```

---

## Limit Resolution

1. **Identity** - Determine actor type (system/admin/user/anonymous)
2. **Billing** - Get subscription plan (free/pro/team/enterprise)
3. **Feature** - Identify feature from endpoint
4. **Endpoint Class** - Determine from HTTP method
5. **Resolve Limit** - Lookup limit configuration
6. **Apply** - Check against current usage

---

## Limit Keys

Redis keys for tracking usage:
```
rate_limit:{actor_type}:{actor_id}:{feature}:{endpoint_class}:{window}
```

Examples:
```
rate_limit:user:123:api_requests:read:1m
rate_limit:user:123:api_requests:read:1h
rate_limit:user:123:api_requests:read:24h
rate_limit:team:456:api_requests:write:1m
```

---

## Limit Evaluation

### Token Bucket Algorithm
- Each limit has a bucket with tokens
- Tokens refill at a constant rate
- Request consumes tokens
- If bucket empty, request denied

### Sliding Window Algorithm
- Track requests in time windows
- Count requests in current window
- If count exceeds limit, deny
- Windows slide continuously

**Choice:** Token bucket for burst handling, sliding window for accuracy.

---

## Error Responses

### 429 Too Many Requests
```json
{
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded for api_requests:read",
    "limit": 100,
    "remaining": 0,
    "reset_at": "2026-01-25T12:00:00Z",
    "retry_after": 60
}
```

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706184000
Retry-After: 60
```

---

## Abuse Detection Signals

### 1. Credential Stuffing
- Multiple failed auth attempts from same IP
- Different credentials, same IP
- Threshold: 5 failures/minute

### 2. Endpoint Scanning
- Sequential requests to different endpoints
- 404 responses from same IP
- Threshold: 10 404s/minute

### 3. Token Abuse
- Same token used from multiple IPs
- Token used at unusual rate
- Threshold: 100 requests/minute from single token

### 4. Burst Abuse
- Sudden spike in requests
- Exceeding burst limit repeatedly
- Threshold: 3 violations in 5 minutes

---

## Abuse Response

### Automatic Actions
1. **Log** - All abuse events logged
2. **Alert** - Trigger alert for security team
3. **Temporary Ban** - Optional IP/token ban (configurable)
4. **Rate Limit Reduction** - Reduce limits for abusive actor

### Temporary Ban
- Duration: 15 minutes (configurable)
- Scope: IP address or token
- Redis key: `ban:ip:{ip}` or `ban:token:{token}`
- TTL: Ban duration

---

## Configuration

### Limit Registry
Central registry of all limits:
```python
RATE_LIMITS = {
    "free": {
        "api_requests": {...},
        "billing": {...}
    },
    "pro": {
        "api_requests": {...},
        "billing": {...}
    },
    "admin": {...}
}
```

### Dynamic Limits
- Limits stored in database (optional)
- Can be updated without code changes
- Fallback to code defaults

---

## Observability

### Metrics
- Rate limit checks (total, allowed, denied)
- Limit violations per actor/plan/feature
- Abuse detections per type
- Temporary bans issued

### Audit Logs
All rate limit decisions logged:
- `rate_limit.check` - Limit checked
- `rate_limit.exceeded` - Limit exceeded
- `abuse.detected` - Abuse detected
- `abuse.banned` - Temporary ban issued

---

## Success Criteria

✅ **Identity-aware** - Different limits per actor type  
✅ **Billing-aware** - Limits scale with plan  
✅ **Feature-aware** - Different limits per feature  
✅ **Endpoint-aware** - Different limits per endpoint class  
✅ **Fail-closed** - Default deny if limit unknown  
✅ **Observable** - All decisions logged and metered  
✅ **Alertable** - Abuse triggers alerts  
✅ **Configurable** - No hardcoded limits in code  

---

## Implementation Notes

1. **Redis Required** - All limit tracking in Redis
2. **Atomic Operations** - Use Redis INCR with TTL
3. **Fail-Closed** - If Redis unavailable, deny by default
4. **Performance** - Limit checks must be fast (<10ms)
5. **Scalability** - Support multiple workers/instances

---

## Next Steps

1. Implement rate limit engine (token bucket + sliding window)
2. Create FastAPI middleware
3. Integrate with billing system
4. Implement abuse detection
5. Add observability hooks
