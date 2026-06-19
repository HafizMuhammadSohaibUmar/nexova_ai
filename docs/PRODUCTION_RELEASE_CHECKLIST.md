# Invoxia Assistant Production Release Checklist

Use this checklist before rebuilding and deploying a production image.

## Source Control

- Confirm the release commit is pushed to GitHub.
- Confirm `git status` is clean locally.
- Create and push a release tag before deployment.
- Record the release tag, Git commit, image tag, site name, and deployment time.
- Confirm no ERPNext or Frappe core files are modified.
- Confirm no secrets are committed.
- Confirm no manual container hotfix exists without a matching Git commit.

## Build

- Build the custom image from `apps.json`.
- Use explicit Frappe and ERPNext branches.
- Use a versioned custom image tag.
- Build from GitHub source, not from edited files inside a running container.
- Do not hotfix app files inside running containers.

## Staging Gate

- Deploy the release image to staging before production.
- Run `bench --site <staging-site> migrate`.
- Run `bench --site <staging-site> clear-cache`.
- Run the full smoke test list on staging.
- Confirm rate limit behavior on staging.
- Confirm subscription suspended/disabled behavior on staging.
- Confirm audit retention cleanup behavior on staging or a disposable test site.
- Confirm backup and restore verification before production deployment.
- Do not deploy to production/client demo until staging passes.

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
- Record the latest verified backup timestamp before production deployment.
- Confirm rollback will use the pre-release backup if schema/data migration rollback is required.

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
