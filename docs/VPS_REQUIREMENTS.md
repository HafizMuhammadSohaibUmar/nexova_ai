# VPS Requirements

## Purpose

This document defines VPS requirements for hosting ERPNext v15 with Invoxia Assistant through official `frappe_docker` and a custom image containing the `nexova_ai` app.

The requirements support local development, VPS staging, VPS production, and future dedicated VPS per client.

## Exact Recommended Architecture

Baseline VPS roles:

- Staging VPS for deployment validation.
- Shared production VPS for early small clients.
- Dedicated production VPS for larger or more privacy-sensitive clients.

Minimum production expectations:

- Modern Linux server distribution supported by the operations team.
- Sufficient CPU for ERPNext workers and optional local AI.
- Sufficient RAM for ERPNext, MariaDB, Redis, workers, and RAG.
- SSD storage.
- Off-server backups.
- Static public IP.
- Domain and DNS access.
- HTTPS certificates.
- Firewall allowing only required ports.
- Monitoring for disk, RAM, CPU, backups, and SSL.

Local-first AI increases requirements because local models, embeddings, or speech components need more resources than API-only mode.

## Recommended VPS Sizes

Small shared production:

- Suitable for early clients with light usage.
- Prioritize stable SSD and enough RAM.
- Avoid enabling heavy local AI for many clients on a small server.

Privacy-sensitive or medium client:

- Dedicated VPS recommended.
- More RAM and CPU.
- Separate backup policy.
- Site-specific Mistral or local AI policy.

RAG-heavy or local-AI-heavy client:

- Dedicated VPS strongly recommended.
- Extra disk for documents and indexes.
- Extra CPU or GPU strategy if local models require it.

## Step-by-Step Deployment Flow

1. Estimate number of clients and expected users.
2. Decide shared VPS or dedicated VPS per client.
3. Choose VPS size based on ERPNext plus AI mode.
4. Provision VPS.
5. Configure firewall and SSH access.
6. Configure DNS.
7. Install required runtime for official `frappe_docker`.
8. Deploy staging first.
9. Validate custom image and site creation.
10. Deploy production stack.
11. Configure SSL.
12. Configure off-server backups.
13. Enable monitoring.
14. Add client sites one at a time.

## Risks

- Under-sized VPS can make ERPNext slow.
- Local-first AI can consume more resources than expected.
- Disk growth from backups and private files can fill the server.
- Multiple clients on one VPS can create noisy-neighbor issues.
- No monitoring means SSL or backup failures can go unnoticed.
- Weak firewall rules increase attack surface.

## Rollback Strategy

- Keep previous image tags available.
- Keep client site backups available off-server.
- Move a high-load client to dedicated VPS.
- Disable local AI features if resource pressure occurs.
- Disable RAG ingestion if disk or CPU pressure occurs.
- Scale VPS vertically before attempting complex architecture changes.

## What Not To Do

- Do not host production without backups.
- Do not host production without SSL.
- Do not put many privacy-sensitive clients on one under-sized VPS.
- Do not store all backups only on the same VPS.
- Do not expose database or Redis publicly.
- Do not enable local AI without capacity planning.
- Do not ignore disk usage growth from files, logs, backups, and RAG.
