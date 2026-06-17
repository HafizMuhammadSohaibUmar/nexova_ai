# Invoxia Assistant Implementation Backlog

## Project Scope

Invoxia Assistant is a custom Frappe app for ERPNext v15. The v1 scope includes navigation, live ERP data answers, voice interaction, RAG, Urdu and English support, multi-tenant SaaS foundations, and subscription control.

No ERPNext core modifications are allowed. No CRUD actions are included in v1. Each client must run in a separate Frappe site and database. The app must remain update-safe by using Frappe extension points, explicit backend tools, and site-specific settings.

## Backlog Principles

- ERPNext remains the system of record.
- Invoxia Assistant must never bypass Frappe permissions.
- Live ERP data must come from explicit permission-aware tools.
- RAG must use approved documents only, not unrestricted ERP tables.
- Voice must use the same backend security model as text.
- Cloud AI mode and private AI mode must be optional per site.
- Subscription suspension must be reversible and must not delete client data.
- Every meaningful assistant request must be auditable.

## Phase 1: Installable Frappe App

### Deliverables

- Installable custom Frappe app for ERPNext v15.
- Invoxia Assistant Desk page and workspace.
- Site-level Invoxia Assistant Settings.
- Feature flags for navigation, live data, voice, RAG, Mistral, Ollama/Qwen, and subscription enforcement.
- Language settings for English, Urdu, and mixed Urdu-English.
- Subscription status fields for active, past due, suspended, terminated pending retention, and deleted after retention.
- Basic audit log DocTypes for assistant requests and tool executions.
- Official `frappe_docker` compatible packaging.
- Installation and verification documentation.

### Tasks

- Rebrand user-facing labels from Nexova AI to Invoxia Assistant where appropriate.
- Keep internal package naming stable unless a migration plan is created.
- Add Invoxia Assistant Settings as a single site-level configuration DocType.
- Add secure fields or site config references for provider credentials.
- Add basic request audit and tool execution audit DocTypes.
- Add app hooks, fixtures, roles, workspace, and page assets required for installation.
- Confirm install, migrate, clear-cache, and uninstall behavior on a test ERPNext v15 site.
- Confirm static assets build and load through Frappe.
- Add deployment checklist reference for official `frappe_docker`.

### Dependencies

- ERPNext v15 and Frappe v15.
- Existing `nexova_ai` app scaffold.
- Official `frappe_docker` custom image workflow.
- Test VPS or local bench environment.

### Risks

- Renaming internal modules can break Frappe imports and migrations.
- Settings may expose secrets if permissions are too broad.
- Missing fixtures can cause pages or workspaces not to appear after install.
- App packaging errors can break Docker image builds.
- Uninstall behavior may remove data unexpectedly if not reviewed.

### Acceptance Criteria

- App installs on a clean ERPNext v15 site without ERPNext core changes.
- App survives `bench migrate` and `bench clear-cache`.
- Invoxia Assistant page is accessible to authorized users.
- Settings DocType exists and is restricted to authorized admins.
- Audit DocTypes exist and can store non-sensitive metadata.
- Feature flags can disable assistant capabilities per site.
- App can be included in a custom `frappe_docker` image.

### Estimated Effort

Medium, 1 to 2 weeks.

## Phase 2: Navigation Assistant

### Deliverables

- Permission-aware navigation assistant.
- Safe route registry for approved ERPNext pages, lists, reports, dashboards, and Invoxia pages.
- English, Urdu, and mixed Urdu-English navigation intent patterns.
- Backend-approved route response.
- Client-side route execution after backend approval.
- Navigation audit events.
- Restricted and ambiguous route fallback responses.

### Tasks

- Define navigation route registry structure.
- Add route categories for modules, workspaces, list views, reports, dashboards, and forms.
- Add permission checks for each route category.
- Add route aliases in English and Urdu.
- Add ambiguity handling when multiple routes match.
- Add backend response format for route approval, denial, and clarification.
- Add frontend handling for approved navigation responses.
- Add audit logging for approved, denied, and ambiguous navigation attempts.
- Add tests for users with different roles.

### Dependencies

- Phase 1 settings and audit logs.
- Frappe route conventions.
- ERPNext module and report route inventory.
- User roles and permissions on test site.

### Risks

- Route suggestions may reveal restricted modules.
- Custom ERPNext installations may have different enabled modules.
- Urdu-English phrases can map to the wrong route if aliases are weak.
- Client-side routing could be misused if backend approval is skipped.

### Acceptance Criteria

- User can ask to open common ERPNext areas in English.
- User can ask to open common ERPNext areas in Urdu or mixed Urdu-English.
- User is not routed to restricted pages.
- Ambiguous navigation requests ask for clarification.
- Denied navigation requests do not reveal sensitive details.
- Every navigation request is auditable.
- No documents are created, edited, submitted, cancelled, amended, or deleted.

### Estimated Effort

Medium, 2 to 3 weeks.

## Phase 3: Live Data Assistant

### Deliverables

- Formal read-only ERP tool registry.
- Intent schema and parameter validation.
- Permission-aware live data tools.
- Deterministic fallback for common questions.
- Compact, schema-bound responses.
- Broad request blocking.
- Urdu and English live data answers.
- Audit logs for intent, tool, parameters, row count, truncation, and response status.

### Tasks

- Define common tool response envelope.
- Implement tool registry with tool name, purpose, inputs, output schema, required permissions, and safety notes.
- Add permission helper for user, role, doctype read permission, company access, and document-level access where possible.
- Add parameter validators for dates, companies, customers, suppliers, items, warehouses, projects, statuses, and currencies.
- Add broad request detector for export, dump, all records, payroll, bank details, unrestricted ledgers, and raw table requests.
- Implement initial read-only tools:
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
- Implement sensitive summary tools after stricter access checks:
  - Profit and loss summary
  - Cash flow summary
  - HR summary
  - Project summary
  - Support ticket summary
- Add response formatting for English and Urdu.
- Add tests for permissions, output limits, broad request blocking, and mixed-language prompts.

### Dependencies

- Phase 1 settings and audit logs.
- ERPNext test data.
- Phase 2 language handling patterns.
- Frappe permission APIs.
- Agreed tool schemas.

### Risks

- Live data tools may expose too much information if output schemas are loose.
- Large sites may experience slow queries without date limits and aggregation.
- ERPNext permissions can vary across roles, companies, and customizations.
- Financial and HR summaries are high sensitivity.
- Raw SQL or unrestricted report access can undermine the security model.

### Acceptance Criteria

- Live data answers use explicit backend tools only.
- All tools respect Frappe permissions.
- All outputs are compact and bounded.
- Broad data export requests are blocked or narrowed.
- No raw SQL is used unless separately reviewed and documented.
- Tool results can be formatted in English and Urdu.
- Mistral or Ollama/Qwen is not required for core deterministic tools.
- No CRUD actions exist.

### Estimated Effort

High, 4 to 6 weeks.

## Phase 4: Voice Assistant

### Deliverables

- Voice input and output interface.
- Voice feature flag per site.
- Browser voice mode for lightweight deployments.
- Server-side speech-to-text abstraction.
- Text-to-speech abstraction.
- English, Urdu, and mixed Urdu-English transcript support.
- Voice transcript audit metadata.
- No raw audio retention by default.
- Redaction controls for spoken responses.

### Tasks

- Add frontend microphone controls, listening state, transcript preview, and voice reply toggle.
- Keep all voice transcripts routed through the same Assistant API as text.
- Add voice channel metadata to audit logs.
- Add configurable speech-to-text provider interface.
- Add configurable text-to-speech provider interface.
- Add site setting for browser-only, cloud, or local voice mode.
- Add language preference and auto-detection behavior.
- Add redaction rules for sensitive spoken data.
- Add policy that raw audio is not stored by default.
- Add tests for transcript submission, permission handling, disabled voice mode, and redacted responses.

### Dependencies

- Phase 1 settings and feature flags.
- Phase 3 Assistant API and live data flow.
- Cloud or local speech provider decision.
- Urdu speech recognition evaluation.

### Risks

- Browser speech recognition may send audio to browser or vendor services.
- Local speech-to-text can be resource-heavy.
- Urdu transcription quality may be inconsistent.
- Spoken financial or HR data can create privacy issues in shared workplaces.
- Audio retention mistakes can violate client privacy expectations.

### Acceptance Criteria

- Voice can be disabled per site.
- Voice transcript uses the same permission checks as typed questions.
- English and Urdu voice inputs can reach the assistant backend.
- Raw audio is not stored by default.
- Sensitive responses can be redacted or shortened before TTS.
- Voice mode does not enable CRUD or bypass confirmations.
- Voice events are auditable without storing unnecessary sensitive audio.

### Estimated Effort

High, 3 to 5 weeks.

## Phase 5: RAG Assistant

### Deliverables

- Tenant-scoped RAG foundation.
- Knowledge source, document, and chunk metadata models.
- Document ingestion workflow.
- Chunking and source traceability.
- Embedding provider abstraction.
- Tenant-scoped vector namespace.
- Permission-aware retrieval.
- Source references in answers.
- RAG governance controls.

### Tasks

- Define Knowledge Source DocType.
- Define Knowledge Document DocType.
- Define Knowledge Chunk DocType or external vector metadata mapping.
- Add document upload and registration flow.
- Validate file type, source type, tenant, roles, users, company, department, and confidentiality.
- Extract text from approved document types.
- Chunk text with heading, page, section, chunk index, and hash metadata.
- Add embedding provider interface.
- Store chunks and embeddings in a site-specific namespace.
- Retrieve only chunks allowed for the current user, role, company, and tenant.
- Add RAG response flow with source title, section, page, and version where available.
- Add admin controls for re-index, disable, delete, and review ingestion status.
- Add tests for tenant isolation, role filtering, no-result behavior, deleted documents, and source references.

### Dependencies

- Phase 1 tenant settings.
- Phase 3 Assistant API and audit logs.
- Phase 6 or Phase 7 embedding provider.
- Selected vector storage strategy.
- Document access policy.

### Risks

- Misconfigured retrieval filters can leak private documents.
- Shared vector indexes can create cross-client leakage.
- Indexing ERP exports can accidentally expose transactional data.
- Document extraction from scanned PDFs may be incomplete.
- Embedding storage and deletion must stay consistent with source documents.
- RAG can hallucinate if responses are not constrained to approved snippets.

### Acceptance Criteria

- RAG is disabled by default until configured.
- Every document and chunk is tenant-scoped.
- Retrieval filters by current site, user, role, company, and document access metadata.
- Live ERP transactional data is not indexed by default.
- Answers include source references when using RAG.
- No unauthorized snippets reach Mistral or local LLM context.
- Deleted or disabled documents are not retrieved.

### Estimated Effort

Very High, 5 to 8 weeks.

## Phase 6: Cloud AI Mode (Mistral)

### Deliverables

- Optional Mistral provider mode.
- Server-side Mistral credential storage.
- Intent classification prompt.
- Parameter extraction prompt.
- Response formatting prompt.
- Strict schema validation for Mistral outputs.
- Provider timeout, retry, and failure handling.
- Provider usage audit metadata.
- Site-level enablement and disablement.

### Tasks

- Add Mistral provider wrapper.
- Store Mistral API key in site config or encrypted settings.
- Ensure keys are never exposed to the browser.
- Add site setting to enable or disable Mistral mode.
- Build structured intent classification request.
- Validate returned intent against local allowlist.
- Validate extracted parameters locally before tool execution.
- Send only compact tool results and approved RAG snippets for response formatting.
- Add timeout and provider error handling.
- Add provider request ID, latency, status, and error metadata to audit logs.
- Add tests for invalid JSON, unsupported intent, low confidence, blocked risk, provider timeout, and disabled provider.

### Dependencies

- Phase 1 settings and audit logs.
- Phase 3 tool registry and schemas.
- Phase 5 RAG snippets for knowledge answers where enabled.
- Mistral account and API key for test site.

### Risks

- Sensitive data can leave the VPS if prompts include too much context.
- LLM output can be invalid, incomplete, or fabricated.
- Provider downtime can break assistant responses if fallback is weak.
- API usage can create unexpected costs.
- Shared API keys can complicate tenant-level cost tracking and privacy promises.

### Acceptance Criteria

- Mistral mode is off unless enabled per site.
- Browser never receives Mistral credentials.
- Mistral never receives full ERP tables, exports, credentials, private files, or unauthorized RAG chunks.
- Mistral outputs never execute tools unless validated locally.
- Provider failure returns a safe, clear response.
- Usage and errors are auditable per site and user.
- Deterministic live data tools still work when Mistral is disabled where supported.

### Estimated Effort

Medium to High, 2 to 4 weeks.

## Phase 7: Private AI Mode (Ollama/Qwen)

### Deliverables

- Optional local LLM mode using Ollama and Qwen.
- Local provider endpoint configuration per site or deployment.
- Local intent classification and response formatting path.
- Local embedding option where selected.
- Local-first privacy mode documentation.
- Resource and performance guidelines.
- Health checks for local model availability.

### Tasks

- Add local LLM provider wrapper compatible with Ollama-style HTTP endpoints.
- Add provider settings for base URL, model name, timeout, context length, and enabled status.
- Add Qwen model configuration guidance.
- Reuse the same intent schema, validation, tool registry, and safety checks as Mistral mode.
- Add local provider health check.
- Add local timeout and fallback behavior.
- Add local embedding provider option if RAG uses local embeddings.
- Add deployment guidance for same-VPS or private-network model service.
- Add tests for provider unavailable, slow response, invalid output, and disabled local mode.
- Benchmark common English and Urdu prompts on target VPS sizes.

### Dependencies

- Phase 1 settings.
- Phase 3 tool registry and schemas.
- Phase 5 RAG embedding needs.
- Ollama service or compatible local LLM runtime.
- Approved Qwen model selection.
- VPS resource plan.

### Risks

- Local models may require more RAM and CPU than the ERPNext VPS can spare.
- Model quality for Urdu and ERP-specific terms may vary.
- Slow responses can hurt user adoption.
- Shared local model services must not mix tenant context.
- Local model endpoints can become a security risk if exposed publicly.

### Acceptance Criteria

- Private AI mode is optional per site.
- Local LLM endpoint is server-side only and not exposed publicly.
- Local mode uses the same backend validation as cloud mode.
- No client data leaves the VPS or private network in private mode.
- Assistant degrades safely if the local model is unavailable.
- Urdu and English test prompts meet acceptable quality for navigation and live data phrasing.
- Resource requirements are documented before production enablement.

### Estimated Effort

Medium to High, 3 to 5 weeks.

## Phase 8: Multi-tenant SaaS

### Deliverables

- One-client-one-site operational model.
- Site-specific settings, credentials, audit logs, rate limits, and RAG namespaces.
- Subscription control enforcement.
- Client onboarding checklist.
- Client suspension and reactivation flow.
- Client offboarding and retention flow.
- Backup and restore runbook.
- Production monitoring and smoke checks.
- Shared VPS and dedicated VPS deployment guidance.

### Tasks

- Define client site creation workflow.
- Define domain, database, files, private files, backups, site config, and RAG namespace naming conventions.
- Enforce subscription state at assistant endpoint, provider calls, and RAG retrieval.
- Add account status message for suspended sites.
- Keep backups active during suspension unless contract says otherwise.
- Add tenant-aware cache keys and rate limits.
- Add audit retention settings per site.
- Add provider usage tracking per site.
- Add onboarding checklist for new clients.
- Add suspension checklist for past due clients.
- Add reactivation checklist after payment recovery.
- Add offboarding checklist for retention and deletion.
- Add restore testing checklist.
- Add production smoke tests for assistant, navigation, live data, voice, RAG, provider modes, and suspension behavior.

### Dependencies

- Phase 1 site settings and subscription fields.
- Phase 3 live data tools.
- Phase 5 RAG tenant isolation.
- Phase 6 and Phase 7 provider mode controls.
- Official `frappe_docker` deployment model.
- Backup and restore policy.

### Risks

- Wrong site routing can expose another client's site.
- Shared services can cause noisy-neighbor performance issues.
- Misconfigured RAG namespace can leak documents.
- Global provider credentials can violate client-specific privacy agreements.
- Suspension by infrastructure shutdown can affect other clients.
- Deleting sites or backups during suspension can cause data loss.
- Restore mistakes can overwrite the wrong client site.

### Acceptance Criteria

- Each client runs in a separate Frappe site and database.
- Invoxia settings are site-specific.
- RAG storage is site-specific.
- Provider mode is site-specific.
- Subscription suspension blocks assistant access without deleting data.
- Reactivation restores assistant access without data restoration.
- Backups continue according to policy.
- Permission tests pass with representative non-admin users.
- Production smoke checks pass before each client is enabled.

### Estimated Effort

High, 4 to 6 weeks.

## v1 Completion Criteria

- Invoxia Assistant installs as a custom app on ERPNext v15.
- ERPNext core remains untouched.
- Navigation assistant works with permission-aware route approval.
- Live ERP data assistant works through explicit read-only tools.
- Voice assistant routes transcripts through the same backend as text.
- RAG retrieves only approved tenant-scoped documents.
- Urdu and English are supported for text, navigation, and voice where provider quality allows.
- Mistral mode is optional and backend-only.
- Ollama/Qwen mode is optional and private-network/local-first.
- Multi-client SaaS uses one Frappe site per client.
- Subscription suspension is reversible and non-destructive.
- No CRUD actions exist in v1.
