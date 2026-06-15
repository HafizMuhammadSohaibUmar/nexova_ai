# Hosting Strategy

## Purpose

This document defines an economical hosting path for `nexova_ai` as a custom Frappe app inside ERPNext v15. The strategy starts simple for local development, moves to VPS staging, and then supports production hosting for multiple clients.

No Docker commands are defined here. This is an architecture and operations plan only.

## Hosting Principles

- Do not modify ERPNext core.
- Keep `nexova_ai` as a custom app.
- Prefer one ERPNext site per client.
- Keep Mistral API keys server-side.
- Keep staging separate from production.
- Use automated backups.
- Use SSL for every public site.
- Scale only when usage requires it.

## Local Development

Purpose:

- Build and test `nexova_ai` safely before deployment.
- Validate app behavior against ERPNext v15.
- Develop docs, tools, and UI without touching production.

Recommended setup:

- Local bench or controlled development environment.
- Dedicated development site.
- Test data only.
- Local environment variables or site config for provider keys.
- No production customer data.
- No public exposure unless explicitly needed.

Local development should validate:

- Frappe app installation
- Desk page behavior
- Permission-aware tools
- Mistral provider configuration
- Audit logging
- RAG experiments later
- Voice browser compatibility

## VPS Staging

Purpose:

- Validate deployment behavior before production.
- Test migrations and app upgrades.
- Test provider credentials and SSL.
- Demonstrate features with safe or copied non-sensitive data.

Recommended setup:

- Low-cost VPS.
- One staging ERPNext bench.
- One or more staging sites.
- Separate staging domain or subdomain.
- SSL enabled.
- Staging Mistral API key or separate provider quota.
- Restricted admin access.

Staging rules:

- Do not use uncontrolled production data.
- Keep staging backups separate from production.
- Test app upgrades here before production.
- Test tenant/site isolation assumptions.

## VPS Production

Purpose:

- Host live ERPNext client sites with `nexova_ai` installed.

Recommended initial model:

- One production VPS for small clients or early rollout.
- One ERPNext bench.
- One site per client.
- Separate domain or subdomain per client.
- SSL for each site.
- Site-specific configuration.
- Site-specific Mistral key if required by contract.

One site per client provides strong operational separation while keeping hosting economical.

## One Site Per Client

Recommended site pattern:

- `client-a.example.com`
- `client-b.example.com`
- `client-c.example.com`

Each site should have:

- Separate database
- Separate files
- Separate site config
- Separate backups
- Separate assistant settings
- Separate audit logs
- Separate RAG indexes later

Benefits:

- Clear tenant boundary
- Easier backup and restore
- Easier client offboarding
- Easier dedicated migration later
- Reduced risk of cross-client data exposure

## Backups

Production backups should include:

- Database backups
- Private files
- Public files
- Site config where safe
- Custom app version reference
- RAG source documents later
- RAG index backup or rebuild plan later

Recommended backup policy:

- Daily automated backups.
- More frequent backups for active production sites if needed.
- Off-server backup storage.
- Periodic restore tests.
- Retention policy by client contract.
- Encryption for sensitive backups.

Do not store Mistral API keys in plain backup locations without encryption.

## SSL

Every staging and production site must use SSL.

Requirements:

- HTTPS only for ERPNext.
- HTTPS only for Nexova AI endpoints.
- Secure cookies.
- No provider keys in browser requests.
- Valid certificates per domain.
- Renewal monitoring.

SSL is required before enabling production AI features.

## Economical Scaling Path

### Stage 1: Single VPS, Few Clients

Use one production VPS with one ERPNext bench and one site per client.

Best for:

- Early clients
- Low to moderate usage
- Controlled assistant rollout
- Cost-sensitive operations

Watch:

- CPU
- RAM
- Disk usage
- Database size
- Background job queues
- Mistral usage cost
- Backup time

### Stage 2: Larger VPS

Move to a larger VPS when resource pressure is consistent.

Best for:

- More users
- Larger databases
- More background jobs
- RAG indexing later

### Stage 3: Split Services

Separate services when needed:

- Database on separate managed or dedicated host
- Redis on separate host
- Worker nodes for background jobs
- Separate RAG/vector service
- Separate monitoring and logging

### Stage 4: Dedicated VPS Per Client

Use a dedicated VPS per client when isolation, performance, or compliance requires it.

## When to Use Dedicated VPS Per Client

Use dedicated VPS hosting for a client when:

- The client has strict compliance requirements.
- The client requires strong infrastructure isolation.
- The client has high transaction volume.
- The client has heavy reporting or assistant usage.
- The client requires custom backup retention.
- The client needs custom network rules or VPN.
- The client needs dedicated Mistral/provider credentials.
- The client has large RAG document storage.
- One client's workload affects others.
- Contract value justifies dedicated infrastructure.

Dedicated VPS benefits:

- Stronger isolation
- Easier performance tuning
- Easier custom maintenance windows
- Easier client-specific compliance
- Lower blast radius

Dedicated VPS tradeoffs:

- Higher cost
- More operational overhead
- More monitoring requirements
- More backup management

## Mistral Provider Hosting Considerations

Mistral API calls should originate from the server.

Requirements:

- Provider keys stored server-side.
- Rate limits per site and user.
- Timeout controls.
- Retry controls.
- Provider request IDs in audit logs.
- Tenant-aware provider configuration.

Cost controls:

- Limit message length.
- Limit response length.
- Avoid sending bulk ERP data.
- Cache safe static RAG retrieval results later if appropriate.
- Track usage per tenant.

## RAG Hosting Considerations

RAG can start simple and grow later.

Initial approach:

- Store source documents per tenant.
- Store chunks and metadata in tenant-scoped tables.
- Use an economical vector storage option.
- Rebuild indexes from source documents if needed.

Scaling path:

- Move vector search to a dedicated service.
- Use separate storage for large document sets.
- Add background workers for ingestion.
- Add per-tenant index management.

RAG should not be enabled for a tenant until document permissions and deletion workflows are ready.

## Monitoring

Monitor:

- ERPNext site availability
- Worker queue health
- Database size
- Disk usage
- Backup success
- SSL expiry
- Mistral API errors
- Mistral API latency
- Assistant request volume
- Tool execution failures
- Permission denied events
- Rate limit events

Operational alerts should go to the maintainers responsible for hosting.

## Deployment Policy

Recommended deployment flow:

1. Develop locally.
2. Commit and tag app changes.
3. Deploy to staging.
4. Run migration and smoke tests in staging.
5. Review assistant behavior and audit logs.
6. Deploy to production during a maintenance window.
7. Verify production site health.
8. Verify Nexova AI assistant endpoint.

No production deployment should be made directly from untested local changes.
