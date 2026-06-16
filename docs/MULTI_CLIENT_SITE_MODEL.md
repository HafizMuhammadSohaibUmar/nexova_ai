# Multi-Client Site Model

## Purpose

This document defines the multi-client SaaS model for Invoxia Assistant on ERPNext v15. One client must equal one Frappe site and one database.

This model protects client privacy, simplifies backups, and allows subscription suspension without deleting data.

## Exact Recommended Architecture

Recommended tenant model:

- One client equals one Frappe site.
- One Frappe site equals one database.
- Each client has separate files, private files, logs, backups, and site config.
- `nexova_ai` is installed per site.
- Assistant settings are stored per site.
- RAG storage is separated per site.
- AI mode is selected per site.
- Subscription state is tracked per site.

Example:

- Client A: `client-a.invoxia.example`, database `client_a_db`
- Client B: `client-b.invoxia.example`, database `client_b_db`
- Client C: `client-c.invoxia.example`, database `client_c_db`

Shared services may include:

- Docker host
- Reverse proxy
- ERPNext application containers
- Redis
- MariaDB server process

Client-specific isolation must still apply at the site, database, files, AI settings, and RAG layers.

## Step-by-Step Deployment Flow

1. Create a new Frappe site for the client.
2. Assign a unique database for the site.
3. Assign a unique domain or subdomain.
4. Install ERPNext on the site.
5. Install `nexova_ai` on the site.
6. Configure client company and users in ERPNext.
7. Configure Invoxia Assistant site settings.
8. Select local-first AI or optional Mistral API mode.
9. Create tenant-scoped RAG storage or namespace if RAG is enabled.
10. Configure site-specific backups.
11. Configure rate limits per site.
12. Run permission tests with representative client users.
13. Enable production access.

## Risks

- Incorrect site routing can send users to the wrong client site.
- Shared application containers can still create operational coupling.
- Misconfigured RAG namespaces can leak documents.
- Cross-site cache keys can leak data if tenant context is ignored.
- A heavy client can affect other clients on the same VPS.
- Admin mistakes can install or configure the wrong site.

## Rollback Strategy

- Restore only the affected client's database and files.
- Keep other client sites online where possible.
- Disable Invoxia Assistant for only the affected site if required.
- Revert site-specific config without changing shared infrastructure.
- Move a client to a dedicated VPS if shared hosting becomes risky.

## What Not To Do

- Do not place multiple clients in one Frappe site.
- Do not share one database across clients.
- Do not share RAG indexes without hard tenant separation.
- Do not use a global Mistral configuration when clients need separate privacy controls.
- Do not suspend a client by deleting the site.
- Do not use one admin account across all clients for daily operations.
- Do not assume Frappe roles replace tenant isolation.
