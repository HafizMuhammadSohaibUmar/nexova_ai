from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


DATA_FILE = Path(os.environ.get("INVOXIA_LICENSE_DB", "/data/licenses.json"))
SIGNING_SECRET = os.environ.get("INVOXIA_LICENSE_SIGNING_SECRET", "")
ADMIN_TOKEN = os.environ.get("INVOXIA_LICENSE_ADMIN_TOKEN", "")
PORT = int(os.environ.get("PORT", "8088"))


class LicenseServer(BaseHTTPRequestHandler):
    server_version = "InvoxiaLicenseServer/0.1"

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"ok": True})
            return

        self._send_json({"error": "not_found"}, status=404)

    def do_POST(self) -> None:
        if self.path == "/api/v1/issue":
            self._issue_license()
            return

        if self.path == "/api/v1/check":
            self._check_license()
            return

        self._send_json({"error": "not_found"}, status=404)

    def _issue_license(self) -> None:
        if not _admin_allowed(self.headers.get("X-Invoxia-License-Admin-Token", "")):
            self._send_json({"error": "unauthorized"}, status=401)
            return

        request = self._read_json()
        if not request:
            self._send_json({"error": "invalid_json"}, status=400)
            return

        license_key = request.get("license_key") or f"INV-{secrets.token_hex(8).upper()}"
        expires_on = request.get("expires_on") or str(date.today() + timedelta(days=30))
        payload = {
            "license_key": license_key,
            "site_id": request.get("site_id") or "",
            "company_id": request.get("company_id") or "",
            "plan": request.get("plan") or "Standard",
            "status": request.get("status") or "Active",
            "expires_on": expires_on,
            "issued_at": request.get("issued_at") or str(date.today()),
            "grace_period_days": int(request.get("grace_period_days") or 7),
            "features": request.get("features") or ["navigation", "live_data", "voice"],
        }

        if not payload["site_id"]:
            self._send_json({"error": "site_id_required"}, status=400)
            return

        signature = sign_license_payload(payload)
        db = _load_db()
        db[license_key] = {
            "payload": payload,
            "signature": signature,
            "past_due_since": request.get("past_due_since") or "",
        }
        _save_db(db)

        self._send_json(
            {
                "license_key": license_key,
                "offline_license_payload": json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "offline_license_signature": signature,
                "status": payload["status"],
                "plan": payload["plan"],
                "expires_on": payload["expires_on"],
                "grace_period_days": payload["grace_period_days"],
            }
        )

    def _check_license(self) -> None:
        request = self._read_json()
        license_key = request.get("license_key") or ""
        site_id = request.get("site_id") or ""
        record = _load_db().get(license_key)

        if not record:
            self._send_json({"status": "Disabled", "message": "License not found."}, status=404)
            return

        payload = record.get("payload") or {}
        if site_id and payload.get("site_id") != site_id:
            self._send_json(
                {"status": "Disabled", "message": "License is registered for a different site."},
                status=403,
            )
            return

        self._send_json(
            {
                "license_key": payload.get("license_key"),
                "status": payload.get("status") or "Active",
                "plan": payload.get("plan") or "",
                "expires_on": payload.get("expires_on") or "",
                "past_due_since": record.get("past_due_since") or "",
                "grace_period_days": int(payload.get("grace_period_days") or 7),
                "offline_license_payload": json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "offline_license_signature": record.get("signature") or "",
            }
        )

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or "0")
            body = self.rfile.read(length).decode("utf-8")
            parsed = json.loads(body or "{}")
        except (TypeError, ValueError):
            return {}

        return parsed if isinstance(parsed, dict) else {}

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def sign_license_payload(payload: dict[str, Any]) -> str:
    if not SIGNING_SECRET:
        raise RuntimeError("INVOXIA_LICENSE_SIGNING_SECRET is required")

    digest = hmac.new(
        SIGNING_SECRET.encode("utf-8"),
        _canonical_payload(payload),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    clean_payload = {key: value for key, value in payload.items() if key != "signature"}
    return json.dumps(
        clean_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _admin_allowed(token: str) -> bool:
    return bool(ADMIN_TOKEN) and hmac.compare_digest(token, ADMIN_TOKEN)


def _load_db() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {}

    try:
        parsed = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _save_db(data: dict[str, Any]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    if not SIGNING_SECRET:
        raise SystemExit("INVOXIA_LICENSE_SIGNING_SECRET is required")
    if not ADMIN_TOKEN:
        raise SystemExit("INVOXIA_LICENSE_ADMIN_TOKEN is required")

    server = ThreadingHTTPServer(("0.0.0.0", PORT), LicenseServer)
    print(f"Invoxia license server listening on :{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
