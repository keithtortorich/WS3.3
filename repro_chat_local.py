"""Minimal repro of /chat 500 against live production logic, using fake tenants."""
from __future__ import annotations

import os
import sys
import traceback

os.environ.pop("DATABASE_URL", None)
os.environ["GROK_API_KEY"] = os.environ.get("GROK_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webstaffr.workers.angel.router import create_app
from webstaffr.workers.angel.voice import GrokVoiceBackend
from starlette.testclient import TestClient

app = create_app(
    db_path=":memory:",
    voice_backend=GrokVoiceBackend(),
    ghl_client=None,
    retell_verifier=None,
    ghl_webhook_verifier=None,
    book_api_verifier=None,
)

client = TestClient(app)
for tenant_id in ("webstaffr_e2e_verification_co_d07dc1d1", "doesnotexist", "demo", "test"):
    resp = client.post(
        "/chat",
        json={"tenant_id": tenant_id, "message": "hi"},
    )
    print(f"{tenant_id!r:40s} -> {resp.status_code} {resp.text[:120]!r}")
