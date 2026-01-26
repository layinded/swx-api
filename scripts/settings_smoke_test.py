#!/usr/bin/env python3
"""
Settings Smoke Test
-------------------
Validates the runtime settings system:
- Settings load from DB
- Updates apply at runtime
- No redeploy required
- Cache invalidation works
- Audit logs created

Usage:
  API_URL=http://localhost:8001/api \\
  ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=changeme \\
  python scripts/settings_smoke_test.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

import httpx

API_URL = os.getenv("API_URL", "http://localhost:8001/api").rstrip("/")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", os.getenv("FIRST_SUPERUSER", "admin@example.com"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", os.getenv("FIRST_SUPERUSER_PASSWORD", "changeme"))
TIMEOUT = 30.0


def log(msg: str) -> None:
    print(f"[test] {msg}")


def fail(msg: str) -> None:
    log(f"FAIL: {msg}")
    sys.exit(1)


def req(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    token: str | None = None,
    json: dict | None = None,
    want: int = 200,
) -> dict | list | None:
    path = path if path.startswith("/") else f"/{path}"
    url = f"{API_URL.rstrip('/')}{path}"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json is not None:
        headers["Content-Type"] = "application/json"
    r = client.request(method, url, headers=headers, json=json, timeout=TIMEOUT)
    if r.status_code != want:
        fail(f"{method} {path} -> {r.status_code} (expected {want}) body={r.text[:500]}")
    if r.status_code == 204 or not r.content:
        return None
    return r.json()


def main() -> None:
    log("Settings Smoke Test")
    log(f"API_URL={API_URL} ADMIN_EMAIL={ADMIN_EMAIL}")
    
    with httpx.Client(timeout=TIMEOUT) as client:
        # Admin login
        r = client.post(
            f"{API_URL}/admin/auth/",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Accept": "application/json"},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            fail(f"Admin login -> {r.status_code} {r.text}")
        admin_token = r.json().get("access_token")
        if not admin_token:
            fail("No access_token")
        
        log("Admin logged in")
        
        # 1. List settings
        log("Test 1: List settings")
        settings = req(client, "GET", "/admin/settings/", token=admin_token, want=200)
        assert isinstance(settings, list), "settings list"
        log(f"  Found {len(settings)} settings")
        
        # 2. Get specific setting
        log("Test 2: Get setting by key")
        test_key = "auth.access_token_expire_minutes"
        setting = req(client, "GET", f"/admin/settings/key/{test_key}", token=admin_token, want=200)
        assert setting["key"] == test_key, "setting key"
        original_value = setting["value"]
        log(f"  {test_key} = {original_value}")
        
        # 3. Update setting
        log("Test 3: Update setting (runtime change)")
        new_value = str(int(original_value) + 1)  # Increment by 1 minute
        updated = req(
            client,
            "PATCH",
            f"/admin/settings/key/{test_key}",
            token=admin_token,
            want=200,
            json={"value": new_value},
        )
        assert updated["value"] == new_value, "updated value"
        log(f"  Updated {test_key} = {original_value} -> {new_value}")
        
        # 4. Verify update persisted
        log("Test 4: Verify update persisted")
        time.sleep(1)  # Small delay for cache/DB
        verify = req(client, "GET", f"/admin/settings/key/{test_key}", token=admin_token, want=200)
        assert verify["value"] == new_value, "value persisted"
        log("  Update persisted correctly")
        
        # 5. Check history
        log("Test 5: Check change history")
        history = req(client, "GET", f"/admin/settings/key/{test_key}/history", token=admin_token, want=200)
        assert isinstance(history, list), "history list"
        assert len(history) > 0, "history has entries"
        assert history[0]["new_value"] == new_value, "history entry"
        log(f"  Found {len(history)} history entries")
        
        # 6. Restore original value
        log("Test 6: Restore original value")
        req(
            client,
            "PATCH",
            f"/admin/settings/key/{test_key}",
            token=admin_token,
            want=200,
            json={"value": original_value},
        )
        log(f"  Restored {test_key} = {original_value}")
        
        # 7. Test cache invalidation (get again should show restored value)
        log("Test 7: Verify cache invalidation")
        time.sleep(1)
        restored = req(client, "GET", f"/admin/settings/key/{test_key}", token=admin_token, want=200)
        assert restored["value"] == original_value, "cache invalidated"
        log("  Cache invalidation working")
        
        # 8. Test validation guards
        log("Test 8: Test validation guards")
        # Try to set invalid value (negative expiration)
        r = client.patch(
            f"{API_URL}/admin/settings/key/{test_key}",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json", "Accept": "application/json"},
            json={"value": "-1"},
            timeout=TIMEOUT,
        )
        if r.status_code == 400:
            log("  Validation guard working (rejected negative value)")
        else:
            fail(f"Validation should reject negative value -> {r.status_code}")
        
        # 9. Test audit log
        log("Test 9: Verify audit log")
        audit = req(client, "GET", "/admin/audit/", token=admin_token, want=200)
        audit_data = audit.get("data", []) if isinstance(audit, dict) else audit
        assert isinstance(audit_data, list), "audit list"
        # Check for settings update in audit
        settings_updates = [a for a in audit_data if isinstance(a, dict) and a.get("action") == "system_config.update"]
        assert len(settings_updates) > 0, "audit log has settings updates"
        log(f"  Found {len(settings_updates)} settings update audit entries")
        
        log("")
        log("=== Settings Smoke Test Summary ===")
        log("✅ All tests passed")
        log("✅ Settings load from DB")
        log("✅ Updates apply at runtime")
        log("✅ No redeploy required")
        log("✅ Cache invalidation works")
        log("✅ Audit logs created")
        log("✅ Validation guards working")


if __name__ == "__main__":
    main()
