# Deployment Architecture

## Purpose

This document defines the recommended hosting and deployment architecture for Invoxia Assistant, delivered as the current `nexova_ai` custom Frappe app installed with ERPNext v15 using official `frappe_docker`.

The architecture supports a multi-client SaaS model where each client has a separate Frappe site and database. ERPNext core must not be modified. Invoxia Assistant is included through a custom Docker image.

## Exact Recommended Architecture

Recommended baseline:

- Official `frappe_docker` as the deployment foundation.
- Custom Docker image built from the official ERPNext v15 image.
- `nexova_ai` installed as a custom app inside the image.
- One client equals one Frappe site.
- One Frappe site equals one database.
- Shared Docker stack for small clients where acceptable.
- Dedicated VPS per client for larger or more privacy-sensitive clients.
- Reverse proxy with HTTPS for every site.
- Server-side AI orchestration only.
- Local-first AI mode by default where possible.
- Optional Mistral API mode per client/site.
- No CRUD in v1.
- v1 capabilities limited to navigation, live data Q&A, voice, and RAG.

Core services:

- ERPNext v15 containers from official `frappe_docker`.
- Custom app image containing `nexova_ai`.
- MariaDB database service.
- Redis services for cache and queue.
- Workers and scheduler.
- Websocket service.
- Reverse proxy and SSL termination.
- Backup storage outside the primary VPS.
- Optional local AI services on the same VPS or private network.
- Optional Mistral API access from backend only.

Tenant boundary:

- Site name
- Database name
- Site config
- Files directory
- Backups
- Assistant settings
- RAG index or namespace
- Audit logs

## Step-by-Step Deployment Flow

1. Prepare a VPS with sufficient CPU, RAM, disk, firewall rules, and SSH access.
2. Install the runtime dependencies required by official `frappe_docker`.
3. Clone or reference official `frappe_docker` deployment files.
4. Build a custom ERPNext v15 image that includes the `nexova_ai` app.
5. Push the custom image to a private registry or make it available to the VPS.
6. Configure environment values for the Docker stack.
7. Start the official `frappe_docker` stack using the custom image.
8. Create one Frappe site for each client.
9. Install ERPNext on the client site.
10. Install `nexova_ai` on the client site.
11. Configure the site domain and HTTPS.
12. Configure Invoxia Assistant site settings.
13. Choose AI mode for the client: local-first or optional Mistral API.
14. Configure backup policy for the site.
15. Run smoke checks for ERPNext, Desk, Invoxia Assistant, voice UI, live data Q&A, and RAG readiness.
16. Enable client access only after verification.

## Risks

- A shared VPS can create noisy-neighbor performance issues.
- Misconfigured site routing can expose the wrong site.
- Shared AI or RAG storage can leak data if tenant filters are missing.
- Mistral API mode can expose sensitive prompt content if tool output is too broad.
- Backups can become a privacy risk if stored without encryption.
- Custom image drift can make future upgrades harder.
- Voice transcripts can contain sensitive data.

## Rollback Strategy

- Keep the previous custom Docker image tag available.
- Keep pre-deployment database and files backups for every affected site.
- Roll back one site at a time where possible.
- Restore only the affected client site and database.
- Revert site config changes if the issue is configuration-related.
- Disable Invoxia Assistant at the site level if ERPNext itself is healthy.
- Disable optional Mistral mode and fall back to local-first or deterministic responses if provider issues occur.

## What Not To Do

- Do not modify ERPNext core.
- Do not install the app by manually editing containers after deployment.
- Do not use one Frappe site for multiple clients.
- Do not share one database between clients.
- Do not expose Mistral keys to the browser.
- Do not send full ERP database exports to Mistral.
- Do not mix RAG indexes between clients.
- Do not enable CRUD actions in v1.
- Do not delete client data when suspending a subscription.
- Do not run production without tested backups and restore steps.
