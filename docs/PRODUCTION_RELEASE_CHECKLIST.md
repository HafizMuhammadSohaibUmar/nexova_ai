# Invoxia Assistant Production Release Checklist

Use this checklist before rebuilding and deploying a production image.

## Source Control

- Confirm the release commit is pushed to GitHub.
- Confirm `git status` is clean locally.
- Tag the release before deployment.
- Confirm no ERPNext or Frappe core files are modified.
- Confirm no secrets are committed.

## Build

- Build the custom image from `apps.json`.
- Use explicit Frappe and ERPNext branches.
- Use a versioned custom image tag.
- Do not hotfix app files inside running containers.

## Migration

- Run `bench --site <site> migrate`.
- Confirm Nexova AI DocTypes are created.
- Confirm Workspace shortcuts point to `/app/nexova-ai-assistant`.
- Run `bench --site <site> clear-cache`.

## Smoke Tests

- Log in as System Manager.
- Open `/app/nexova-ai`.
- Open `/app/nexova-ai-assistant`.
- Ask for sales, purchases, stock, receivables, payables, customers, suppliers, items, orders, and invoices.
- Ask a navigation request such as `open customers`.
- Confirm blocked broad requests do not return exports or raw tables.
- Confirm audit logs are created.
- Confirm tool execution logs are created.
- Confirm disabled subscription status blocks the assistant.
- Confirm non-authorized users cannot access restricted answers.

## Voice

- Confirm HTTPS is active before testing microphone access.
- Test desktop browser voice input.
- Test mobile browser voice input.
- Confirm raw audio is not stored.
- Confirm voice can be disabled in settings.

## RAG

- Confirm RAG is disabled by default.
- Create a test knowledge source.
- Create an approved knowledge document.
- Rebuild chunks.
- Confirm chunks are tenant/site scoped and admin restricted.

## Security

- Rotate any exposed database passwords before production.
- Use HTTPS only.
- Keep Cloudflare DNS/proxy settings documented.
- Confirm provider credentials are server-side only.
- Confirm assistant settings are System Manager only.
- Confirm audit logs do not store more text than policy allows.

## Backup

- Confirm database backup succeeds.
- Confirm public files backup succeeds.
- Confirm private files backup succeeds.
- Confirm backup storage is off-server or externally replicated.
- Test restore on staging before relying on production backups.

## Monitoring

- Monitor frontend, backend, websocket, scheduler, queue-short, queue-long, Redis, and MariaDB containers.
- Monitor disk, CPU, RAM, and Docker volume usage.
- Monitor SSL certificate expiry.
- Monitor assistant error logs.
- Monitor backup success.

## Rollback

- Keep the previous image tag available.
- Keep the pre-release database backup.
- Document the exact command used for deployment.
- Roll back image first if no migration changed schema.
- Restore database only when schema/data migration rollback is required.
