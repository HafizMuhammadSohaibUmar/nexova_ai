# Invoxia License Server

This is the first production-oriented license service for Invoxia AI. It issues:

- online subscription status responses for cloud-hosted sites
- signed offline license payloads for local/offline installs

It does not modify ERPNext or Frappe. Client sites verify licenses inside the `nexova_ai` custom app.

## Run Locally

```bash
cp .env.example .env
docker compose up -d --build
curl http://127.0.0.1:8088/health
```

## Issue an Offline License

```bash
curl -s http://127.0.0.1:8088/api/v1/issue \
  -H "Content-Type: application/json" \
  -H "X-Invoxia-License-Admin-Token: $INVOXIA_LICENSE_ADMIN_TOKEN" \
  -d '{
    "site_id": "client-site.local",
    "company_id": "client-001",
    "plan": "Local Standard",
    "status": "Active",
    "expires_on": "2026-12-31",
    "grace_period_days": 7,
    "features": ["navigation", "live_data", "voice"]
  }'
```

Copy the returned `offline_license_payload` and `offline_license_signature` into
`Nexova AI Settings` on the client site. The `License Verification Secret` must
match this server's signing secret for the current HMAC-based implementation.

## Check an Online License

```bash
curl -s http://127.0.0.1:8088/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{"license_key":"INV-EXAMPLE","site_id":"client-site.local"}'
```

## Security Notes

- Keep this server private behind HTTPS and firewall rules.
- Keep `INVOXIA_LICENSE_SIGNING_SECRET` outside Git.
- Rotate per-client secrets before broad rollout.
- This initial implementation uses HMAC-SHA256. A future SaaS control panel can
  replace it with asymmetric public/private signing while keeping the client
  verification interface stable.
