# Invoxia Assistant Implementation Roadmap

## Project Goal

Invoxia Assistant is a custom Frappe app for ERPNext v15. It provides a privacy-first assistant for voice, Urdu and English interaction, ERP navigation, live ERP data answers, tenant-scoped knowledge retrieval, and multi-client SaaS operations.

The app must not modify ERPNext core. All behavior must be delivered through the custom app, Frappe APIs, explicit permission-aware tools, and deployment configuration. The app must survive ERPNext updates by avoiding core overrides, avoiding monkey patches, and using stable Frappe extension points.

## Product Boundaries

- No ERPNext core modifications.
- No CRUD in v1.
- One Frappe site per client.
- One Frappe site equals one database.
- ERPNext remains the system of record.
- Live ERP data is fetched only through explicit Python tools.
- RAG is for approved documents and knowledge, not unrestricted ERP database retrieval.
- Mistral mode is optional and backend-only.
- Local LLM mode with Ollama and Qwen is optional and preferred for privacy-sensitive clients.
- Voice is a channel over the same assistant backend, not a separate permission model.
- Every meaningful assistant request must be auditable.

## Target Architecture

The implementation should evolve into these app boundaries:

- `api`: whitelisted assistant endpoints.
- `orchestrator`: intent routing, policy checks, provider selection, and response flow.
- `tools`: explicit ERPNext read-only tools.
- `navigation`: safe route registry and navigation intent handling.
- `providers`: Mistral, local LLM, embeddings, speech-to-text, and text-to-speech wrappers.
- `schemas`: intent, tool input, and tool output contracts.
- `security`: permissions, tenant context, redaction, rate limits, and subscription checks.
- `audit`: assistant request logs and tool execution logs.
- `rag`: document ingestion, chunking, embeddings, retrieval, and source references.
- `settings`: site-specific Invoxia configuration.

## Phase 1: Installation

### Objective

Establish Invoxia Assistant as a clean, update-safe custom Frappe app installed beside ERPNext v15 using official `frappe_docker`.

### Deliverables

- Rebrand user-facing app metadata from Nexova AI to Invoxia Assistant where appropriate.
- Confirm app installs with ERPNext v15 using official `frappe_docker`.
- Confirm no ERPNext core files are modified.
- Create site-level Invoxia Assistant Settings DocType.
- Add feature flags for assistant enabled, navigation enabled, live data enabled, voice enabled, RAG enabled, Mistral enabled, and local LLM enabled.
- Add subscription state fields for `active`, `past_due`, `suspended`, and future retention states.
- Add provider mode setting: deterministic, Mistral API, local LLM.
- Add language preferences for English, Urdu, and mixed Urdu-English.
- Add a basic admin-only setup checklist inside the app or documentation.
- Verify Desk page, workspace, assets, and whitelisted endpoint load after install and migrate.

### Risks

- Incorrect app packaging can break image builds or app installation.
- Rebranding too aggressively may rename internal module paths and cause migration pain.
- Missing feature flags can make later rollback harder.
- Site settings may expose secrets if permissions are not strict.
- Custom image drift can make ERPNext upgrades harder.

### Dependencies

- ERPNext v15 and Frappe v15 compatibility.
- Official `frappe_docker` custom image flow.
- Working staging site.
- Admin access to install and migrate custom apps.

### Estimated Complexity

Medium.

### Estimated Timeline

1 to 2 weeks.

## Phase 2: Tool Registry

### Objective

Replace hardcoded assistant logic with a formal, permission-aware, read-only ERP tool registry.

### Deliverables

- Tool registry module with stable tool names, descriptions, risk levels, input schemas, and output schemas.
- Common tool response envelope with status, summary, data, and metadata.
- Intent schema and validation layer.
- Safe broad-request detection for export, dump, all-records, payroll, bank, and unrestricted ledger requests.
- Permission helper that checks current Frappe user, role, doctype read permission, company access, document-level access where applicable, and field sensitivity.
- Audit log DocTypes for assistant requests and tool executions.
- Rate limit foundations per user and per site.
- Initial read-only tools:
  - Sales summary
  - Purchase summary
  - Stock balance summary
  - Receivables summary
  - Payables summary
  - Customer summary
  - Supplier summary
  - Item lookup
  - Quotation summary
  - Sales order summary
  - Purchase order summary
  - Invoice summary
- Tests for permission denial, broad request blocking, parameter validation, and output limits.

### Risks

- Tool outputs may accidentally expose too much data.
- ERPNext permissions can vary by installed modules and custom roles.
- Broad summaries can become slow on large sites without careful limits.
- Tool schema drift can break provider prompts or response formatting.
- Audit logs can store sensitive text if redaction policy is weak.

### Dependencies

- Phase 1 settings and feature flags.
- Frappe permission APIs.
- Representative ERPNext sample data.
- Agreed tool output schemas.

### Estimated Complexity

High.

### Estimated Timeline

3 to 5 weeks.

## Phase 3: Navigation Assistant

### Objective

Allow users to navigate ERPNext safely through text or voice without granting new permissions or creating records.

### Deliverables

- Navigation registry for approved ERPNext routes.
- Route categories for modules, workspaces, list views, report views, form views, dashboards, and Invoxia pages.
- Permission-aware route filtering so users only navigate to allowed areas.
- Intent handling for English, Urdu, and mixed Urdu-English navigation phrases.
- Client-side route execution using Frappe Desk routing after backend approval.
- Safe fallback when a user asks for unsupported, ambiguous, or restricted navigation.
- Audit events for navigation intent, approved route, denied route, and ambiguity.
- Initial routes:
  - Sales Invoice list
  - Purchase Invoice list
  - Customer list
  - Supplier list
  - Item list
  - Stock Balance report
  - Accounts Receivable report
  - Accounts Payable report
  - General Ledger report
  - HR, Project, and Support areas where installed and permitted

### Risks

- Navigation can leak the existence of restricted modules if suggestions are not filtered.
- ERPNext route names may differ across versions, installed apps, or customizations.
- Ambiguous Urdu-English phrases may route users incorrectly.
- Client-side route changes must not bypass backend checks.

### Dependencies

- Phase 2 permission helpers and audit logs.
- Stable route registry.
- Desk page UI support for navigation responses.
- Language detection or language preference from Phase 1.

### Estimated Complexity

Medium.

### Estimated Timeline

2 to 3 weeks.

## Phase 4: Live Data Assistant

### Objective

Provide reliable, compact, permission-aware answers from live ERPNext data without CRUD and without bulk exports.

### Deliverables

- Orchestration layer that accepts a user question, validates subscription and feature flags, classifies intent, validates parameters, runs one or more approved tools, and returns a structured answer.
- Deterministic fallback mode for common live data questions without external AI.
- Optional Mistral provider for intent classification, parameter extraction, and response wording.
- Optional local LLM provider using Ollama and Qwen for local-first deployments.
- Provider abstraction so Mistral and local LLM modes share the same tool registry and safety checks.
- Urdu and English response formatting rules.
- Date range parsing and bounding.
- Company, customer, supplier, item, warehouse, and project disambiguation flow.
- Output redaction and truncation controls.
- Additional sensitive tools:
  - Profit and loss summary
  - Cash flow summary
  - HR summary
  - Project summary
  - Support ticket summary
- Automated tests for provider-disabled behavior, provider errors, permission filtering, and Urdu-English inputs.

### Risks

- LLM output may contain invented values if not constrained to tool output.
- Mistral API mode may expose sensitive prompts if compact output rules are weak.
- Local LLM quality can vary across VPS sizes and model choices.
- Financial and HR summaries are sensitive and require stricter access checks.
- Large ERP sites may need optimized report APIs instead of simple list queries.

### Dependencies

- Phase 2 tool registry.
- Phase 1 provider settings.
- Optional Mistral API credentials per site.
- Optional Ollama service and approved local model.
- Audit logging and rate limits.

### Estimated Complexity

High.

### Estimated Timeline

4 to 6 weeks.

## Phase 5: Voice Assistant

### Objective

Add voice input and voice output for English, Urdu, and mixed Urdu-English while preserving the same backend security model.

### Deliverables

- Voice feature flag per site.
- Browser voice mode for supported browsers as a lightweight option.
- Server-side speech-to-text provider abstraction.
- Optional local speech-to-text mode for privacy-sensitive deployments.
- Text-to-speech provider abstraction.
- Optional local text-to-speech mode.
- Language selection and auto-detection for English, Urdu, and mixed phrases.
- Voice transcript handling that sends only text to the Assistant API.
- No raw audio retention by default.
- Redaction rules for sensitive spoken responses.
- Voice-specific confirmation pattern for any future sensitive action, even though v1 remains no-CRUD.
- UI controls for microphone, listening state, transcript preview, language, and voice reply toggle.
- Audit fields for voice channel, transcript hash or redacted transcript, language, and provider mode.

### Risks

- Browser speech recognition may send audio to browser/vendor services.
- Urdu speech recognition quality may vary significantly.
- Local speech-to-text can require high CPU or GPU resources.
- Text-to-speech may read sensitive financial or HR data aloud in shared offices.
- Audio handling mistakes can create privacy incidents.

### Dependencies

- Phase 4 Assistant API and orchestration.
- Phase 1 language and feature settings.
- Local or remote speech provider decision.
- Site-specific privacy policy for transcript and audio retention.

### Estimated Complexity

High.

### Estimated Timeline

3 to 5 weeks.

## Phase 6: RAG

### Objective

Enable tenant-scoped, permission-aware answers from approved documents, SOPs, ERP manuals, policies, and implementation knowledge.

### Deliverables

- RAG feature flag per site.
- Invoxia Knowledge Source DocType.
- Invoxia Knowledge Document DocType.
- Invoxia Knowledge Chunk DocType or external vector metadata mapping.
- Document upload and registration workflow.
- File type validation and text extraction.
- Chunking strategy with heading, page, section, chunk index, and text hash metadata.
- Embedding provider abstraction.
- Optional local embedding mode.
- Tenant-scoped vector namespace per Frappe site.
- Role, user, company, department, and confidentiality metadata on documents and chunks.
- Permission-aware retrieval that filters before snippets reach the LLM.
- Source references in responses.
- Governance actions: re-index, disable document, delete document, delete embeddings, review ingestion status.
- RAG plus live ERP answer flow for mixed questions.
- Tests for tenant isolation, role filtering, deleted document removal, no-result handling, and source citation.

### Risks

- RAG snippets can leak restricted policies if metadata filters are wrong.
- Shared vector services can leak data without strict namespace enforcement.
- Ingesting live ERP exports would undermine the privacy model.
- Embedding indexes can become stale after document changes.
- Large documents can increase storage and compute costs.
- Source extraction quality may be poor for scanned or complex PDFs.

### Dependencies

- Phase 4 provider abstraction and orchestration.
- Phase 2 audit logs and permission helpers.
- Tenant/site context from Phase 1.
- Selected vector storage strategy.
- Selected embedding provider.
- Admin workflow for approved knowledge documents.

### Estimated Complexity

Very High.

### Estimated Timeline

5 to 8 weeks.

## Phase 7: Multi-Client SaaS

### Objective

Harden the product for multiple clients, each isolated by Frappe site, database, files, backups, settings, audit logs, and RAG storage.

### Deliverables

- One-client-one-site operational process.
- Site-specific Invoxia Assistant settings.
- Site-specific provider mode and credentials.
- Site-specific subscription state enforcement.
- Suspension behavior:
  - Block assistant endpoint.
  - Block AI provider calls.
  - Block RAG retrieval.
  - Keep ERPNext data intact.
  - Keep backups running.
  - Show account status message to authorized users.
- Tenant-aware cache keys.
- Tenant-aware rate limits.
- Tenant-aware audit log retention settings.
- Tenant-scoped RAG namespaces.
- Billing/admin runbook for active, past due, suspended, terminated pending retention, and deleted after retention states.
- Client onboarding checklist.
- Client offboarding and data retention checklist.
- Permission test checklist using representative non-admin users.
- Monitoring plan for per-site request volume, errors, provider usage, and rate limit events.

### Risks

- Wrong site routing can expose one client's ERP site to another client.
- Shared services can create noisy-neighbor performance issues.
- Suspension done at infrastructure level can affect other clients.
- Provider credentials can leak if shared globally without policy.
- Cross-site cache or RAG keys can leak data.
- Operational mistakes can restore the wrong backup to the wrong site.

### Dependencies

- Phase 1 site settings and subscription fields.
- Phase 4 provider usage controls.
- Phase 6 tenant-scoped RAG.
- Deployment model using one Frappe site per client.
- Backup and restore policy.

### Estimated Complexity

High.

### Estimated Timeline

4 to 6 weeks.

## Phase 8: Production Deployment

### Objective

Deploy Invoxia Assistant safely using official `frappe_docker`, a versioned custom image, HTTPS, backups, monitoring, and controlled rollout.

### Deliverables

- Versioned custom Docker image containing ERPNext v15, Frappe v15, and `nexova_ai`.
- Staging VPS deployment.
- Production VPS deployment.
- Custom image build process using `apps.json`.
- Environment configuration for shared small-client stack and dedicated client VPS.
- HTTPS for every site.
- Off-server encrypted backups for database, public files, private files, site config where safe, app version reference, audit logs according to policy, and RAG source/index rebuild data.
- Pre-deployment and post-deployment smoke tests.
- Rollback process by image tag and site restore.
- Monitoring for site availability, worker health, scheduler, disk, CPU, RAM, SSL expiry, backups, assistant errors, provider errors, and RAG ingestion.
- Production enablement checklist for each client:
  - ERPNext login
  - Desk access
  - Invoxia Assistant page
  - Navigation assistant
  - Live data assistant
  - Urdu and English text flows
  - Voice flow where enabled
  - RAG flow where enabled
  - Subscription suspended behavior
  - Backup success
  - Audit log review

### Risks

- Deploying untested local changes can break client sites.
- Missing backups can turn rollback into data loss.
- Production secrets can leak through image layers, logs, or committed files.
- Under-sized VPS resources can make ERPNext and local AI slow.
- Local LLM and voice services can consume more resources than planned.
- Updating all clients at once increases blast radius.
- ERPNext version drift can break assumptions if app compatibility is not tested.

### Dependencies

- Stable code from Phases 1 through 7.
- Official `frappe_docker` deployment process.
- VPS capacity planning.
- DNS and SSL access.
- Backup storage.
- Release tagging discipline.
- Staging validation before production.

### Estimated Complexity

High.

### Estimated Timeline

3 to 5 weeks for first production-ready deployment, then 1 to 3 days per additional small client site after the process is stable.

## Recommended Release Milestones

### Milestone A: Production Foundation

Includes Phase 1 and the first part of Phase 2.

Capabilities:

- App installs cleanly.
- Invoxia page loads.
- Settings exist.
- Audit logs exist.
- Small read-only tool set works.
- No AI provider required.

### Milestone B: Assistant v1

Includes Phases 2, 3, and 4.

Capabilities:

- Read-only live ERP assistant.
- Safe navigation assistant.
- English and Urdu text support.
- Optional Mistral mode.
- Optional local LLM mode.
- No CRUD.

### Milestone C: Voice and Knowledge

Includes Phases 5 and 6.

Capabilities:

- Voice input and output.
- Local-first voice option.
- Tenant-scoped RAG.
- Knowledge answers with source references.

### Milestone D: SaaS Production

Includes Phases 7 and 8.

Capabilities:

- One site per client.
- Subscription control.
- Privacy-first deployment.
- Backups, monitoring, rollback, and controlled rollout.

## Non-Negotiable Acceptance Criteria

- ERPNext core remains untouched.
- Invoxia Assistant can be installed, migrated, disabled, and upgraded as a custom app.
- No CRUD actions exist in v1.
- Every ERP data answer uses explicit tools and Frappe permissions.
- Every tool has bounded inputs and bounded outputs.
- No full ERP tables, dumps, payroll records, bank details, or unrestricted exports are sent to any LLM.
- Mistral keys and local provider endpoints are server-side only.
- Local LLM mode and Mistral mode are selected per site.
- RAG storage and retrieval are tenant-scoped.
- Voice transcripts follow the same permission and audit model as text.
- Subscription suspension is reversible and does not delete client data.
- Production deployment uses versioned images, staging validation, HTTPS, and tested backups.
