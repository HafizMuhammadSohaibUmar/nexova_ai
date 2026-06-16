# Local Development to Production Flow

## Purpose

This document defines the release path from local development to production for Invoxia Assistant, currently developed in the `nexova_ai` app repository.

The flow uses official `frappe_docker`, a custom Docker image, staging validation, and controlled production rollout. Documentation only; no Docker commands are included.

## Exact Recommended Architecture

Environment path:

- Local development
- Staging VPS
- Production VPS
- Dedicated client VPS later when required

Release artifact:

- Versioned custom Docker image containing ERPNext v15 and `nexova_ai`.

Site model:

- One client equals one Frappe site and one database.
- Staging sites mirror production structure but use safe data.
- Production sites use site-specific settings and backups.

Feature scope for v1:

- Navigation
- Live data Q&A
- Voice
- RAG
- No CRUD
- No autonomous ERP actions

## Step-by-Step Deployment Flow

1. Develop documentation, app configuration, and future code changes locally.
2. Keep ERPNext core unchanged.
3. Commit changes in the `nexova_ai` repository.
4. Create a release version for the app.
5. Build a custom image from official ERPNext v15 image patterns.
6. Tag the image with a clear version.
7. Deploy the image to staging.
8. Create or update a staging site.
9. Install or migrate `nexova_ai` on staging.
10. Run smoke tests.
11. Test permissions with non-admin users.
12. Test English and Urdu assistant flows.
13. Test local-first AI mode.
14. Test optional Mistral API mode if enabled.
15. Test RAG with tenant-scoped documents.
16. Review audit logs.
17. Take production pre-deployment backups.
18. Deploy the same image tag to production.
19. Update one client site at a time.
20. Verify each site before moving to the next.
21. Keep rollback image and backups available.

## Production Smoke Checks

Run checks for:

- ERPNext login
- Desk access
- Invoxia Assistant page visibility
- Navigation intent
- Live data Q&A with permission-aware tool result
- Voice input where supported
- English response
- Urdu response
- RAG response with approved source
- Mistral disabled behavior
- Mistral enabled behavior where approved
- Subscription suspended behavior
- Backup completion

## Risks

- Skipping staging can push broken app versions to production.
- Different image versions between staging and production can hide bugs.
- Testing only with admin users can miss permission failures.
- Production data can leak if copied casually to staging.
- RAG behavior can differ if staging documents are not representative.
- Urdu and English voice support can vary by browser or provider.

## Rollback Strategy

- Stop rollout after the first affected site.
- Revert the stack to the previous image tag.
- Restore the affected site database and files from pre-deployment backup if migrations changed data.
- Disable Invoxia Assistant feature flags if ERPNext is otherwise healthy.
- Disable Mistral mode if provider integration is the problem.
- Keep unaffected client sites on the stable version until the issue is fixed.

## What Not To Do

- Do not deploy untested local changes directly to production.
- Do not modify ERPNext core.
- Do not use production client data in local development without approval and sanitization.
- Do not update all client sites at once for risky releases.
- Do not enable CRUD in v1.
- Do not enable Mistral API mode by default for privacy-sensitive clients.
- Do not skip permission tests.
- Do not remove rollback images immediately after deployment.
