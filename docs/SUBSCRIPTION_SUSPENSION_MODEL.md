# Subscription Suspension Model

## Purpose

This document defines how Invoxia Assistant subscriptions can be suspended without deleting client data. The model supports privacy-sensitive multi-client SaaS where one client equals one Frappe site and database.

Suspension must be reversible.

## Exact Recommended Architecture

Subscription state should be site-specific.

Recommended states:

- `active`
- `past_due`
- `suspended`
- `terminated_pending_retention`
- `deleted_after_retention`

Suspension should disable Invoxia Assistant access and optionally restrict ERPNext access according to contract, but it must not delete:

- Client site
- Client database
- Files
- Private files
- Backups
- RAG documents
- Audit logs within retention period
- Site configuration

Recommended suspension behavior:

- Block Invoxia Assistant chat endpoint.
- Block AI provider calls.
- Block RAG retrieval.
- Keep ERPNext data intact.
- Keep backups running unless contract says otherwise.
- Show an account status message to authorized users.
- Allow admin or billing recovery.

## Step-by-Step Deployment Flow

1. Detect billing or contract condition requiring suspension.
2. Mark the client site subscription state as `suspended`.
3. Disable Invoxia Assistant features for that site.
4. Stop optional Mistral API calls for that site.
5. Stop or pause RAG ingestion for that site.
6. Keep backups active.
7. Keep site data intact.
8. Notify the client according to billing policy.
9. Allow authorized recovery once payment or contract status is resolved.
10. Reactivate features by returning the site to `active`.
11. Record suspension and reactivation in audit logs.

## Risks

- Suspending by deleting a site can cause permanent data loss.
- Suspending shared services can affect other clients.
- Forgetting to block AI calls can create unpaid provider costs.
- Stopping backups during suspension can violate data retention promises.
- RAG indexes may become stale during suspension.
- Users may confuse assistant suspension with ERP data deletion.

## Rollback Strategy

- Change subscription state back to `active`.
- Re-enable Invoxia Assistant features for the site.
- Re-enable Mistral API mode only if previously allowed.
- Resume RAG ingestion and refresh stale indexes if needed.
- Run a smoke test for chat, live Q&A, voice, and RAG.
- Confirm backups continued during suspension.

## What Not To Do

- Do not delete the client site for suspension.
- Do not delete the client database for suspension.
- Do not delete backups before retention expiry.
- Do not disable shared containers in a way that affects other clients.
- Do not keep charging Mistral usage while suspended.
- Do not expose other clients' status or data in suspension messages.
- Do not use suspension as a substitute for legal termination and data deletion policy.
