# Invoxia Assistant Remaining Development Plan

Status date: 2026-06-20

This document is the working checklist for taking the current custom Frappe app from its present foundation to a production-ready Invoxia Assistant for ERPNext. It is intentionally detailed so development can proceed step by step without losing important security, product, deployment, or operational work.

The app must remain an ERPNext add-on only. Do not modify ERPNext core, do not patch Frappe core, and do not use monkey patches.

## Current Baseline

The repository currently has these foundations:

- Custom Frappe app package: `nexova_ai`.
- Workspace route: `/app/nexova-ai`.
- Assistant Page route: `/app/nexova-ai-assistant`.
- Standard Page export under `nexova_ai/nexova_ai/page/nexova_ai_assistant/`.
- Standard Workspace export under `nexova_ai/nexova_ai/workspace/nexova_ai/`.
- Backend endpoint: `nexova_ai.api.ask_ai`.
- Client config endpoint: `nexova_ai.api.get_client_config`.
- Settings DocType: `Nexova AI Settings`.
- Audit DocType: `Nexova AI Audit Log`.
- Tool execution DocType: `Nexova AI Tool Execution Log`.
- Knowledge source/document/chunk DocTypes.
- Basic request audit logging.
- Basic tool execution logging.
- Feature flags for assistant, navigation, live data, voice, RAG, rate limits, and subscription enforcement.
- Basic subscription status blocking.
- Basic per-user rate limiting with Frappe cache.
- Deterministic read-only live tools for common ERPNext questions.
- Dynamic readable DocType list/count foundation.
- Dynamic readable navigation discovery for DocTypes, Reports, and Workspaces.
- Multilingual command vocabulary foundation for English, Urdu, and Roman Urdu.
- Browser voice input and browser text-to-speech foundation.
- Voice transcript review before sending.
- App structure tests and JSON/compile validation.

## Production Readiness Status

| Area | Current Status | Production Status |
| --- | --- | --- |
| Custom app isolation | Mostly done | Needs periodic verification before every release |
| Page/workspace routing | Working foundation | Needs VM smoke test after every rebuild |
| Settings DocType | Partial | Needs more provider, retention, and security fields |
| Audit logs | Partial | Needs retention, redaction, indexes, and review workflow |
| Rate limits | Partial | Needs tests, site limits, admin reset, and telemetry |
| Subscription enforcement | Partial | Needs status matrix, tests, and provider/RAG blocking |
| Live data answers | Partial | Needs broader tool registry and stronger query planner |
| Dynamic ERPNext discovery | Partial | Needs field sensitivity, report support, and ambiguity UI |
| Navigation | Partial | Needs full ERPNext route inventory and permission tests |
| Urdu/English/Roman Urdu | Partial | Needs phrase test suite and LLM-backed intent option |
| Voice recognition | Basic | Needs server STT strategy and mobile HTTPS validation |
| RAG | Skeleton | Needs ingestion, extraction, embeddings, retrieval, citations |
| Mistral/cloud LLM | Not implemented | Needs provider wrapper and strict schema validation |
| Local/private LLM | Not implemented | Needs Ollama/Qwen wrapper and health checks |
| Monitoring | Not implemented | Needs health endpoints, alerts, logs, dashboards |
| Backups | Documentation only | Needs verified backup/restore runbook and scheduled checks |
| Staging/release flow | Documentation only | Needs tags, image versioning, and deployment gates |
| Tests | Partial | Needs Frappe integration tests and VM smoke scripts |

## Non-Negotiable Rules

- ERPNext and Frappe core must remain untouched.
- All assistant behavior must live in the custom app or deployment configuration.
- v1 remains read-only. No create, submit, cancel, amend, delete, import, export, or bulk-update actions.
- Every live ERP answer must go through approved backend tools or permission-aware dynamic read paths.
- No raw SQL unless separately reviewed, justified, bounded, permission-safe, and documented.
- No browser exposure of provider keys, database passwords, site secrets, or local LLM endpoints.
- No full table dumps, unrestricted exports, payroll data, bank details, private files, or unrestricted ledgers.
- All user-visible actions must pass through subscription, feature flag, role, rate limit, safety, and permission checks.
- Voice and text must share the same backend security model.
- RAG must use approved documents only, not unrestricted ERP database indexing.
- Each client must run in a separate Frappe site/database.
- Production deployments must use GitHub source, versioned image builds, migration, cache clear, and smoke tests.
- Manual hotfixes inside running containers are allowed only for emergency diagnosis and must be replaced by Git commits and rebuilds.

## Work Package 1: App Identity And Standards Cleanup

Goal: make naming, structure, docs, and app boundaries clean before deeper features.

### Remaining Tasks

- Decide final user-facing name:
  - Internal package can remain `nexova_ai`.
  - User-facing product can be `Invoxia Assistant`.
  - Avoid renaming Python package unless a migration plan is written.
- Update app metadata if needed:
  - `app_title`
  - `app_publisher`
  - descriptions
  - README labels
  - Workspace labels where desired
- Keep routes stable:
  - Workspace: `/app/nexova-ai`
  - Assistant Page: `/app/nexova-ai-assistant`
- Confirm no `app_include_js` or `page_js` confusion returns.
- Add a release check that asserts:
  - no ERPNext core files modified
  - no Frappe core files modified
  - no monkey patches
  - no secrets in Git
- Add a developer setup guide for local bench and Docker VM workflows.

### Acceptance Criteria

- A new developer can understand the package name versus product name.
- Standard Page and Workspace routes work after rebuild.
- Tests verify custom-app-only boundaries.
- README and docs agree on current supported ERPNext version.

## Work Package 2: Settings And Configuration Hardening

Goal: settings should support production control without storing secrets carelessly.

### Remaining Tasks

- Add settings for:
  - audit retention days
  - tool execution retention days
  - RAG retention policy
  - provider timeout seconds
  - max rows per tool
  - max dynamic rows
  - max prompt/result characters
  - enable cloud LLM
  - enable local LLM
  - enable server STT
  - enable server TTS
  - response language preference
  - spoken response redaction mode
  - site/client identifier
- Decide where secrets live:
  - Prefer `site_config.json` or Frappe encrypted password fields.
  - Never commit secrets.
  - Never send secrets to browser.
- Add validation for settings values.
- Add admin help text for high-risk settings.
- Add tests for default settings and disabled feature behavior.

### Acceptance Criteria

- Site settings are System Manager only.
- Feature flags disable their feature safely.
- Provider credentials are server-side only.
- Invalid settings fall back safely or are rejected.

## Work Package 3: Permission And Data Safety Layer

Goal: make the assistant safely respect ERPNext roles, permissions, fields, companies, and sensitive data boundaries.

### Remaining Tasks

- Expand permission helpers:
  - user role check
  - DocType read permission
  - report permission where possible
  - document-level permission checks
  - company restrictions
  - user permission records
  - field sensitivity checks
- Define sensitive fields and DocTypes:
  - salary/payroll
  - bank account
  - payment credentials
  - private notes
  - contact details where policy requires redaction
  - HR and employee records
- Add redaction helpers for:
  - audit logs
  - LLM prompts
  - voice replies
  - table outputs
- Add a safety decision object:
  - allowed
  - blocked
  - needs clarification
  - needs admin role
  - unsupported in v1
- Add denial messages that do not reveal restricted data existence.
- Add Frappe integration tests with at least:
  - System Manager
  - Sales User
  - Accounts User
  - Stock User
  - restricted/non-authorized user

### Acceptance Criteria

- A user cannot learn restricted data through summaries, suggestions, navigation, RAG, or errors.
- Permission tests pass for representative ERPNext roles.
- Sensitive fields are excluded from dynamic queries by default.
- Denied responses are safe and auditable.

## Work Package 4: Formal Tool Registry And Query Planner

Goal: move from a small tool set to a scalable, schema-based ERPNext tool layer.

### Current Tools

- Sales summary.
- Purchase summary.
- Stock balance.
- Receivables summary.
- Payables summary.
- Customer summary.
- Supplier summary.
- Item lookup.
- Quotation summary.
- Sales order summary.
- Purchase order summary.
- Invoice summary.
- Dynamic readable DocType list/count foundation.

### Remaining Tasks

- Define formal tool schemas:
  - input schema
  - output schema
  - required DocTypes
  - allowed fields
  - risk level
  - max rows
  - default date bounds
  - aggregation strategy
  - redaction policy
- Add parameter extraction:
  - date range
  - fiscal year
  - company
  - customer
  - supplier
  - item
  - item group
  - warehouse
  - territory
  - sales person
  - project
  - cost center
  - account
  - status
  - currency
- Add disambiguation:
  - multiple customers
  - multiple suppliers
  - multiple items
  - multiple companies
  - ambiguous invoice type
- Add tool categories:
  - Accounts
  - Selling
  - Buying
  - Stock
  - CRM
  - Projects
  - Support
  - Manufacturing
  - HR, disabled by default until stricter policy exists
- Add additional read-only tools:
  - sales by customer
  - sales by item
  - sales by territory
  - overdue receivables by aging bucket
  - top overdue customers
  - payable aging
  - stock by warehouse
  - low stock items
  - inactive items
  - open sales orders
  - open purchase orders
  - delivery notes summary
  - purchase receipts summary
  - payment entries summary
  - GL summary, restricted
  - P&L summary, restricted
  - cash/bank balance summary, highly restricted
  - project status summary
  - support ticket summary if module exists
  - manufacturing work order summary if module exists
- Add report-backed tools only after permission review:
  - Accounts Receivable
  - Accounts Payable
  - Stock Balance
  - General Ledger
  - Trial Balance
  - Profit and Loss Statement
- Add no-data responses that explain filters applied.
- Add output truncation notes.

### Acceptance Criteria

- Every tool is discoverable in the registry.
- Every tool has schema, required permissions, and tests.
- All outputs are bounded and compact.
- Broad requests are blocked or narrowed.
- Complex questions either answer safely or ask clarification.

## Work Package 5: Dynamic ERPNext Discovery

Goal: safely use ERPNext metadata so the assistant can support installed/custom modules without manually hardcoding everything.

### Remaining Tasks

- Cache readable DocType/report/workspace discovery per site and user for short TTL.
- Add field allowlist by fieldtype:
  - safe text fields
  - status fields
  - date fields
  - link fields where safe
  - currency/float/count fields where safe
- Exclude sensitive fieldtypes and fields:
  - Password
  - Code where risky
  - HTML where risky
  - Attach fields unless explicitly allowed
  - private, secret, token, password, key, bank, salary-like field names
- Add dynamic filter extraction:
  - status
  - date
  - link names
  - owner
  - modified range
- Add dynamic report navigation, not report execution, until report permissions and parameters are safe.
- Add ambiguity response UI with clickable options.
- Add tests for fuzzy matching and false positives.
- Add production guardrails:
  - never return more than configured limit
  - never expose fields outside safe allowlist
  - never infer unrestricted exports

### Acceptance Criteria

- Custom DocTypes can be listed/count-read if permitted.
- Sensitive fields are never displayed by dynamic fallback.
- Ambiguous requests ask for clarification.
- Discovery does not leak restricted DocTypes.

## Work Package 6: Navigation Assistant

Goal: support all practical ERPNext navigation patterns without bypassing permission checks.

### Remaining Tasks

- Build a complete route inventory:
  - Workspaces
  - DocType list views
  - DocType new forms, disabled in v1 unless only navigation is allowed
  - reports
  - dashboards
  - print formats where safe
  - module pages
  - Nexova/Invoxia pages
- Add aliases for ERPNext modules:
  - Accounting
  - Selling
  - Buying
  - Stock
  - CRM
  - HR
  - Payroll
  - Projects
  - Support
  - Manufacturing
  - Assets
  - Quality
  - Website
  - Users and Permissions
- Add English, Urdu, and Roman Urdu phrases for open/go/show/navigate.
- Add clarification cards in the UI.
- Add navigation audit details:
  - requested phrase
  - matched target
  - approved/denied/ambiguous
  - route returned
- Add route smoke tests on VM.

### Acceptance Criteria

- Users can navigate to readable ERPNext areas by text or voice.
- Restricted areas are not suggested or opened.
- Ambiguous navigation gives choices.
- Navigation is auditable.

## Work Package 7: Urdu, English, Roman Urdu, And Intent Quality

Goal: reduce lost commands and make the assistant tolerant of natural speech, mixed language, and voice recognition errors.

### Remaining Tasks

- Expand vocabulary test corpus:
  - English
  - Urdu script
  - Roman Urdu
  - mixed Urdu-English
  - common Pakistani business terms
  - common speech-to-text mistakes
- Add phrase categories:
  - ask/count/list/open/search/filter/top/compare/summarize
  - today/yesterday/week/month/fiscal year
  - receivable/payable/outstanding/due
  - invoice/order/quotation/delivery/receipt/payment
  - customer/supplier/item/warehouse/company/project
- Add confidence scoring:
  - high confidence execute
  - medium confidence clarify
  - low confidence suggest examples
- Add typo/fuzzy matching tests.
- Add response language policy:
  - answer in user's language where safe
  - keep ERPNext record names unchanged
  - avoid translating official DocType names when route/action depends on exact names
- Add optional LLM-based classifier later, but only after deterministic safety checks.

### Acceptance Criteria

- Common Urdu/Roman Urdu commands route correctly.
- Common voice mistakes are normalized.
- Low-confidence commands ask clarification instead of failing silently.
- Test corpus protects against regressions.

## Work Package 8: Voice Recognition And Voice Reply Strategy

Goal: improve voice beyond browser-only recognition and keep privacy clear.

### Current State

- Browser Web Speech API is used when available.
- Browser controls raw transcript quality.
- HTTPS is required for mobile microphone reliability.
- Transcript is shown for review before sending.
- Voice reply uses browser speech synthesis.

### Remaining Tasks

- Add frontend language selector:
  - English
  - Urdu
  - Auto/Mixed
- Add visible transcript confidence/alternatives where browser provides them.
- Add server STT provider interface:
  - provider name
  - timeout
  - max audio duration
  - retention policy
  - language hint
  - result confidence
- Add local STT option:
  - Whisper/faster-whisper or equivalent
  - deployment requirements
  - CPU/RAM expectations
- Add cloud STT option only with explicit client consent.
- Add TTS provider interface:
  - browser
  - local
  - cloud
- Add spoken response redaction:
  - financial summary short mode
  - no sensitive HR/bank speech unless explicitly allowed
- Add voice audit metadata:
  - channel
  - provider
  - language
  - confidence
  - raw audio stored yes/no
  - transcript redacted/hash option
- Add mobile browser test matrix:
  - Android Chrome
  - iPhone Safari
  - Edge mobile
  - HTTPS domain

### Acceptance Criteria

- Voice can be disabled per site.
- Browser voice works over HTTPS where supported.
- Server STT can be enabled without changing assistant security model.
- Raw audio is not stored by default.
- Voice and text produce equivalent permission behavior.

## Work Package 9: RAG And Knowledge

Goal: answer approved document questions safely with source citations.

### Current State

- Knowledge Source, Document, and Chunk DocTypes exist.
- Chunk rebuild foundation exists.
- Retrieval/provider flow is not production-ready.

### Remaining Tasks

- Add Knowledge Source admin UI workflow.
- Add document upload/register flow.
- Add file validation:
  - PDF
  - TXT
  - Markdown
  - DOCX later if extractor exists
- Add extraction pipeline:
  - text extraction
  - page/section metadata
  - error logging
  - re-ingestion status
- Add chunking:
  - chunk size
  - overlap
  - hash
  - title
  - section
  - page
  - version
- Add embedding provider abstraction:
  - local embeddings
  - cloud embeddings with consent
  - disabled mode
- Select vector storage strategy:
  - MariaDB text search for first local prototype
  - external vector DB only after tenant isolation review
- Add retrieval filters:
  - site
  - user
  - role
  - company
  - department
  - confidentiality
  - enabled/disabled document
- Add source citations in answers.
- Add governance actions:
  - re-index
  - disable source
  - disable document
  - delete document
  - delete embeddings/chunks
- Add tests for tenant isolation, role filtering, disabled documents, and citation presence.

### Acceptance Criteria

- RAG is disabled by default.
- No unapproved ERP transactional data is indexed.
- Retrieval is tenant and permission scoped.
- Answers cite sources.
- Deleted/disabled documents do not appear.

## Work Package 10: LLM Providers

Goal: add optional language intelligence without letting an LLM control data access.

### Mistral / Cloud Provider Tasks

- Add provider wrapper.
- Add server-side credential configuration.
- Add strict timeout and retry policy.
- Add structured JSON output contract.
- Validate intent output against local allowlist.
- Validate parameters locally before tool execution.
- Send only compact tool results and approved snippets to provider.
- Add provider usage logging:
  - provider
  - model
  - request ID
  - latency
  - token estimate if available
  - error status
- Add failure fallback.
- Add tests for invalid JSON, timeout, unsupported intent, unsafe intent, disabled provider.

### Local LLM Provider Tasks

- Add Ollama-compatible provider wrapper.
- Add model/base URL/timeout/context settings.
- Add health check.
- Add Qwen model guidance.
- Add local-only privacy mode docs.
- Add performance benchmark checklist.
- Ensure local endpoint is not public.

### Acceptance Criteria

- LLM providers are optional and off unless enabled.
- Providers never receive full ERP tables or unauthorized snippets.
- Providers cannot execute tools directly.
- Local validation always decides allowed action.
- Provider errors are safe and auditable.

## Work Package 11: Rate Limits, Subscription, Audit Retention

Goal: make production controls testable and enforceable.

### Rate Limit Remaining Tasks

- Add unit tests for:
  - under per-minute limit
  - over per-minute limit
  - over daily limit
  - disabled rate limit
- Add site-level/global limits if needed.
- Add admin reset action or documented cache clear method.
- Add audit event for rate limit blocked.
- Add metrics for rate limit hits.

### Subscription Remaining Tasks

- Define exact status behavior:
  - Active: allow enabled features.
  - Past Due: optionally warn or block provider/RAG.
  - Suspended: block assistant, providers, and RAG.
  - Disabled: block assistant.
  - Terminated Pending Retention: block assistant, preserve data until retention end.
- Add tests for every status.
- Ensure subscription check blocks:
  - assistant endpoint
  - provider calls
  - RAG retrieval
  - future voice server calls
- Add admin-facing status message.
- Add reactivation behavior.

### Audit Retention Remaining Tasks

- Add settings fields:
  - audit log retention days
  - tool log retention days
  - keep blocked request logs yes/no
- Add scheduled cleanup job.
- Add retention safety:
  - never delete before configured retention
  - disabled cleanup by default until configured
  - log cleanup summary
- Add indexes if logs grow:
  - creation
  - user
  - status
  - intent
  - tool name
- Add audit redaction policy:
  - no raw audio
  - optional question logging
  - optional response logging
  - redacted sensitive values

### Acceptance Criteria

- Rate limits are covered by tests.
- Subscription states are covered by tests.
- Audit retention cleanup is scheduled, configurable, and logged.
- Production operators know how to review and retain logs.

## Work Package 12: Error Monitoring And Health Checks

Goal: know when the assistant, workers, providers, backups, or deployment are unhealthy.

### Remaining Tasks

- Add health endpoint or bench command for:
  - app installed
  - settings readable
  - page exists
  - workspace exists
  - Redis/cache available
  - DB reachable
  - scheduler running
  - queue workers running
  - provider configured/disabled
  - RAG configured/disabled
- Add structured error logging categories:
  - assistant error
  - permission error
  - provider error
  - RAG error
  - voice error
  - rate limit block
  - subscription block
- Add monitoring docs for:
  - Docker containers
  - disk usage
  - memory/CPU
  - SSL expiry
  - MariaDB health
  - Redis health
  - Frappe scheduler
  - worker queues
  - assistant error counts
  - backup success
- Decide monitoring tool:
  - lightweight shell/cron and email first
  - Sentry or similar later if acceptable
  - Uptime monitoring for public site

### Acceptance Criteria

- Admin can run one command/checklist to confirm assistant health.
- Repeated assistant errors are visible without opening browser console.
- Provider failures do not break ERPNext Desk.

## Work Package 13: Backup, Restore, And Data Retention

Goal: production deployments must be recoverable before real clients use them.

### Remaining Tasks

- Document actual VM backup commands for current Docker setup.
- Schedule backups:
  - database
  - public files
  - private files
  - site config where safe
  - app version/commit reference
  - RAG source files/chunks/rebuild data
- Store backups off-server or externally replicated.
- Encrypt backups where appropriate.
- Add restore test process on staging.
- Add restore verification:
  - ERPNext login works
  - Invoxia page works
  - Settings preserved
  - Audit logs restored according to policy
  - RAG data restored or rebuildable
- Add client retention policy:
  - active
  - suspended
  - terminated pending retention
  - deletion after retention
- Add backup failure alert.

### Acceptance Criteria

- A backup can be restored on staging.
- Restore steps are documented and tested.
- Backups continue during subscription suspension unless contract says otherwise.
- No production deployment happens without a recent verified backup.

## Work Package 14: Staging, Release Tags, And Deployment Discipline

Goal: stop relying on manual VM edits and make every deployment repeatable.

### Remaining Tasks

- Define branches:
  - `main` for deployable code
  - feature branches for major work
  - optional staging branch if needed
- Add release tags:
  - `v0.1.0-foundation`
  - `v0.2.0-live-data`
  - `v0.3.0-voice`
  - etc.
- Add changelog.
- Add release checklist requiring:
  - tests pass
  - compile passes
  - JSON validation passes
  - no secrets
  - no core file modifications
  - tag created
  - image rebuilt from GitHub
  - migrate run
  - clear-cache run
  - smoke tests pass
- Add staging deployment before production.
- Add rollback plan:
  - previous image tag
  - pre-migration backup
  - rollback commands
  - restore commands
- Add VM deployment script/checklist for current `invoxia` Docker project.

### Acceptance Criteria

- Every deployment maps to a Git commit and image tag.
- No manual container hotfix remains uncommitted.
- Staging passes before production/client demo.
- Rollback path is known before deployment.

## Work Package 15: Test Strategy

Goal: protect the assistant from regressions before it touches real client data.

### Existing Tests

- Structure tests.
- Page/workspace tests.
- Hook hygiene tests.
- Basic architecture presence tests.

### Remaining Tests

- Pure Python unit tests:
  - vocabulary normalization
  - intent detection
  - date parsing
  - broad request blocking
  - settings defaults
  - voice strategy
  - rate limit behavior with mocked cache
  - subscription status behavior
- Frappe integration tests:
  - install/migrate
  - settings read
  - whitelisted endpoint
  - audit log insert
  - tool execution log insert
  - permissions by role
  - readable DocType discovery
  - navigation response
  - dynamic list/count
- VM smoke tests:
  - page loads
  - CSS loads
  - assistant API works
  - navigation works
  - voice button over HTTPS
  - subscription blocked
  - rate limited
  - audit log created
- Security tests:
  - broad export blocked
  - bank/payroll/secret fields blocked
  - non-authorized user denied
  - provider credentials not in client config
- RAG tests when implemented:
  - role filtering
  - source citations
  - disabled document excluded
  - tenant isolation

### Acceptance Criteria

- Tests must run before every release.
- Integration tests must run against a real ERPNext test site before client deployment.
- Security-sensitive features cannot ship without tests.

## Work Package 16: Client Onboarding And SaaS Operations

Goal: prepare for real clients without mixing tenants or operational responsibilities.

### Remaining Tasks

- Define one-site-per-client standard.
- Define domain naming:
  - `client.sohaib.systems`
  - or client-owned domains.
- Define Cloudflare/DNS process.
- Define HTTPS process.
- Define admin account policy.
- Define provider mode per client:
  - deterministic only
  - cloud LLM
  - local LLM
  - browser voice
  - server voice
- Define onboarding checklist:
  - site created
  - ERPNext installed
  - app installed
  - settings configured
  - backup enabled
  - smoke tests passed
  - subscription status active
  - client users/roles verified
- Define suspension checklist.
- Define reactivation checklist.
- Define offboarding and deletion checklist.
- Define support/debug data collection policy.

### Acceptance Criteria

- Client data is isolated by site/database/files/RAG namespace.
- Suspension is reversible and non-destructive.
- Onboarding cannot skip backup and permission tests.

## Recommended Development Order From Here

Use this order to avoid building advanced features on weak safety foundations.

1. Settings hardening and production control fields.
2. Rate limit and subscription tests.
3. Audit retention policy and scheduled cleanup.
4. Permission/data safety layer expansion.
5. Vocabulary and intent test corpus.
6. Dynamic discovery field safety and ambiguity UI.
7. Formal tool schema registry.
8. Broader live data tools by ERPNext module.
9. Navigation route inventory and tests.
10. Voice language selector and server STT provider interface.
11. Error monitoring and health checks.
12. Backup/restore verification runbook.
13. Release tagging and staging deployment process.
14. RAG ingestion and retrieval.
15. Mistral provider.
16. Local Ollama/Qwen provider.
17. SaaS onboarding/suspension/offboarding runbooks.

## Definition Of Production Ready

The app is production ready only when all of these are true:

- It installs and migrates cleanly on a fresh ERPNext v15 site.
- It runs from a versioned Docker image built from GitHub.
- It has HTTPS on the deployed domain.
- It has a verified database and files backup.
- A restore test has been completed on staging.
- The release has a Git tag.
- The app passes unit, structure, integration, and VM smoke tests.
- The assistant page, settings, audit logs, and workspace work after rebuild.
- Rate limit behavior is tested.
- Subscription suspended/disabled behavior is tested.
- Audit retention is configured and tested.
- Non-authorized user behavior is tested.
- Broad and sensitive data requests are blocked.
- Provider keys are not exposed to the browser or Git.
- Voice can be disabled and follows the same backend permission model.
- RAG is disabled by default or fully tenant-scoped and tested.
- Monitoring exists for containers, errors, disk, SSL, and backups.
- No ERPNext or Frappe core files are modified.

## Immediate Next Sprint

Recommended next sprint scope:

1. Add settings fields for audit/tool retention and max rows.
2. Add rate limit tests.
3. Add subscription status tests.
4. Add scheduled audit cleanup.
5. Add vocabulary/intent tests for English, Urdu, Roman Urdu, and voice mistakes.
6. Add deployment release checklist updates for tags and staging.

This sprint keeps the product moving toward production readiness before adding more flashy assistant abilities.
# Remaining Work To Reach The Full Invoxia AI Product

This file tracks what remains before Invoxia AI is ready for paid clients across both hosted cloud and local/offline installs.

## Already In Place

- Custom Frappe app only. ERPNext and Frappe core remain untouched.
- Invoxia AI Desk Page and Workspace.
- Permission-aware live data tools for core ERPNext areas.
- Dynamic navigation discovery for DocTypes, reports, dashboards, workspaces, pages, and modules.
- Metadata engine foundation for DocTypes, fields, child tables, links, permissions, and safe query fields.
- Query planner foundation for bounded read-only list/count/sum operations.
- Safe CRUD draft foundation, with actual write execution still disabled.
- Browser voice foundation and provider settings.
- Local/cloud AI deployment automation for Ollama/Qwen and whisper.cpp.
- Standard model profile: `qwen3:14b` and `large-v3-turbo-q5_0`.
- Audit logs, tool execution logs, retention settings, rate limits, and subscription status settings.
- Seven-day subscription grace period setting and backend policy foundation.

## Remaining Before Client Production

1. Whisper runtime connector
   - Upload audio from the Desk Page to Frappe.
   - Forward audio to whisper.cpp.
   - Return transcript.
   - Do not store raw audio by default.

2. Ollama/Qwen strict intent router
   - Send user text to Qwen.
   - Require strict JSON output.
   - Validate intent against approved registry only.
   - Reject unknown tools and unsafe arguments.
   - Ask clarification when confidence is low.

3. Safe CRUD workflow
   - Add draft action DocType.
   - Render preview in UI.
   - Require explicit user confirmation.
   - Recheck permissions immediately before write.
   - Log before and after every write.
   - Start with create-only, then update, then submit/cancel later.

4. Full ERPNext coverage
   - Expand dynamic metadata-driven actions across all installed modules.
   - Add report filters and dashboard opening.
   - Add specific document opening by human names and latest/last record requests.
   - Add ambiguity handling instead of guessing.

5. Urdu/English quality
   - Test English, Roman Urdu, and Urdu script command sets.
   - Add phrase aliases from real client usage.
   - Add transcript correction prompts.
   - Add noisy microphone guidance.

6. Subscription and licensing
   - Build central license server for hosted clients.
   - Build signed offline license files for local clients.
   - Store `past_due_since`.
   - Enforce seven-day grace period after billing failure.
   - Put local expired clients into read-only ERP mode while preserving login and backup export.

7. Backup and restore
   - Automated daily backups.
   - Encrypted offsite backup for hosted clients.
   - Local backup folder and optional external drive backup for offline clients.
   - Monthly restore drill.
   - Written recovery runbook.

8. Monitoring and support
   - Health checks for ERPNext, MariaDB, Redis, Ollama, and Whisper.
   - Error log reporting.
   - Disk and backup alerts.
   - Release tags and rollback notes.

9. Installer and deployment polish
   - Cloud deployment script for one client site.
   - Local installer flow for Docker-based offline clients.
   - Model profile selection: economy, standard, premium.
   - HTTPS setup for hosted and LAN/local installs.

10. Production validation
   - Seeded ERPNext test site.
   - Integration tests for navigation, live answers, STT, LLM routing, safe CRUD previews, rate limits, and suspension.
   - Security review for every tool that can read or write business data.
