# Docker Custom Image Plan

## Purpose

This document defines how Invoxia Assistant should be included in ERPNext v15 through a custom Docker image based on official `frappe_docker`.

The current app repository is `nexova_ai`. The future product name is Invoxia Assistant. ERPNext core must remain unchanged.

## Exact Recommended Architecture

Recommended image model:

- Use official `frappe_docker` as the base deployment pattern.
- Build a custom application image for ERPNext v15.
- Include `nexova_ai` in the image build process.
- Pin ERPNext, Frappe, and app versions.
- Tag every image with a release version.
- Use the same image for all sites in one stack.
- Configure client-specific settings per Frappe site, not per image.

Image responsibilities:

- Contain ERPNext v15.
- Contain Frappe v15 compatible with ERPNext v15.
- Contain the `nexova_ai` custom app.
- Contain Python dependencies required by the app.
- Contain static assets for the app.

Image must not contain:

- Client database data
- Site private files
- Mistral API keys
- Tenant-specific secrets
- RAG indexes
- Backups
- Hardcoded client configuration

## Step-by-Step Deployment Flow

1. Select the official ERPNext v15 image or build context recommended by `frappe_docker`.
2. Add the `nexova_ai` app as a custom app source during image build.
3. Install app dependencies during the image build.
4. Build assets as required by the Frappe app lifecycle.
5. Assign a versioned image tag.
6. Push the image to a private registry.
7. Update the Docker stack configuration to use the custom image.
8. Deploy the stack to staging first.
9. Create or migrate a staging site.
10. Install or update `nexova_ai` on the staging site.
11. Verify app availability in Desk.
12. Promote the same image tag to production.
13. Install or update the app per client site.
14. Keep the previous image tag available for rollback.

## Risks

- Unpinned dependencies can produce inconsistent images.
- Building directly on production can make deployments hard to reproduce.
- Storing secrets in the image can leak credentials.
- Manually installing apps inside running containers can be lost on redeploy.
- A bad image can affect all sites sharing the stack.
- Version mismatch between ERPNext v15 and the app can break migrations.

## Rollback Strategy

- Repoint the stack to the previous known-good image tag.
- Restore affected site database and files if migrations changed data.
- Keep app schema migrations backward-aware where possible.
- Roll back staging first to validate the procedure.
- If only Invoxia Assistant fails, disable the app feature flag for affected sites while keeping ERPNext running.

## What Not To Do

- Do not modify ERPNext core files.
- Do not manually copy app files into live containers.
- Do not build untagged or `latest`-only production images.
- Do not bake client secrets into the image.
- Do not store backups inside the app image.
- Do not use different untracked images across clients without release records.
- Do not run Docker commands as part of documentation creation.
