# Backup and Restore Policy

## Purpose

This document defines backup and restore policy for Invoxia Assistant as a custom app installed with ERPNext v15. The policy supports privacy-sensitive clients, one site per client, subscription suspension, and safe rollback.

## Exact Recommended Architecture

Backup scope per client site:

- Database backup
- Public files
- Private files
- Site config where safe
- Installed app version reference
- Invoxia Assistant settings
- Audit logs where required by policy
- RAG source documents if enabled
- RAG chunk metadata and embeddings, or a documented rebuild path

Storage model:

- Backups stored outside the primary VPS.
- Encrypted backup storage for production.
- Separate backup paths per client.
- Retention controlled per client contract.
- Restore tests performed regularly.

Suggested retention:

- Daily backups for all production sites.
- More frequent backups for high-activity clients.
- Weekly and monthly retained snapshots for longer recovery windows.
- Staging backups kept separate from production backups.

## Step-by-Step Deployment Flow

1. Define the client's retention requirement.
2. Configure site-specific backup location.
3. Enable database, files, and private files backup.
4. Ensure backups are transferred off the VPS.
5. Encrypt backups or store them in encrypted storage.
6. Record app image tag and app version with each deployment.
7. Schedule periodic restore tests.
8. Document the exact restore target for each client.
9. Monitor backup success and failure alerts.
10. Review backup size growth monthly.

## Restore Flow

1. Identify the client site to restore.
2. Confirm restore point with the client or internal owner.
3. Disable access to the affected site if needed.
4. Preserve current broken state if forensic review is required.
5. Restore database backup.
6. Restore public and private files.
7. Restore or reconfigure site config.
8. Confirm app image version compatibility.
9. Restore or rebuild RAG indexes if enabled.
10. Run smoke tests.
11. Re-enable user access.
12. Log restore action and outcome.

## Risks

- Backups without private files may restore incomplete ERP documents.
- Backups stored on the same VPS can be lost with the server.
- Unencrypted backups can expose sensitive ERP data.
- RAG indexes can become inconsistent with restored documents.
- Restoring the wrong site can overwrite another client's data.
- App version mismatch can break restored sites.

## Rollback Strategy

- Use the latest pre-change backup for the affected client site.
- Roll back app image to the previous compatible tag if needed.
- Restore only the affected client's site and database.
- Keep a copy of the failed state before restore when practical.
- Disable Invoxia Assistant if the core ERPNext site is otherwise healthy.

## What Not To Do

- Do not store production backups only on the production VPS.
- Do not mix backups from different clients in one unlabeled folder.
- Do not restore one client's backup into another client's site.
- Do not rely on database backups alone.
- Do not store API keys in unencrypted backup exports.
- Do not delete suspended client backups unless retention policy allows it.
- Do not skip restore testing.
