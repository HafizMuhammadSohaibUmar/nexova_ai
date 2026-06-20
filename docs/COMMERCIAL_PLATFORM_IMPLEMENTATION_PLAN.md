# Invoxia AI Commercial Platform Implementation Plan

This app must remain a custom Frappe app installed beside ERPNext. It must not modify ERPNext core, patch Frappe core, or depend on monkey patches.

## Implemented Foundation

- Standard Frappe app structure, workspace, and Desk Page for Invoxia AI.
- Permission-aware live-data tools for common ERPNext modules.
- Dynamic navigation discovery for DocTypes, reports, pages, dashboards, workspaces, and modules.
- Dynamic readable DocType list/count query support.
- Audit logs, tool execution logs, rate limits, retention settings, subscription status checks, cloud/local provider settings, and RAG DocTypes.
- Browser voice input with transcript review before sending.
- Provider strategy scaffolding for local Whisper, local Vosk, Deepgram, Ollama, Mistral, OpenAI, and OpenAI-compatible providers.
- Metadata engine foundation for DocTypes, fields, required fields, link fields, child tables, permissions, and safe field sets.
- Query planner foundation for safe list/count/sum operations using metadata.
- Safe CRUD draft foundation. It can prepare previews, but confirmed write execution is intentionally disabled until the confirmation workflow is complete.
- License decision foundation for active, past-due, suspended, disabled, and offline-license scenarios.

## Next Development Milestones

1. LLM intent router
   - Add strict JSON schema output.
   - Allow only approved tool names and bounded arguments.
   - Use local Ollama by default for offline clients.
   - Add cloud Mistral/OpenAI-compatible mode only when clients accept cloud processing.
   - Add confidence thresholds and clarification prompts.

2. Safe CRUD workflow
   - Add draft storage DocType.
   - Add UI preview panel.
   - Add explicit confirmation button.
   - Add permission checks immediately before save.
   - Add audit log entry before and after write.
   - Support create first, then update, then submit/cancel much later.

3. Voice upgrade
   - Add local Whisper service integration.
   - Keep raw audio off by default.
   - Add language switching for English, Urdu, and Roman Urdu.
   - Add client-side noise guidance and transcript confirmation.

4. Local/offline package
   - Docker Compose profile for ERPNext, Invoxia AI, local STT, local LLM, backups, and monitoring.
   - Signed offline license file validation.
   - Local backup scripts and restore drill.
   - LAN-only HTTPS setup.

5. Cloud package
   - Per-client Frappe site isolation.
   - Central SMTP sender.
   - Cloud backups and restore testing.
   - Staging before production.
   - Release tags and rollback notes.

6. Subscription enforcement
   - Online license server for cloud clients.
   - Signed offline license renewal for local clients.
   - Read-only ERP mode for suspended local installs while keeping login, read access, and backup export available.

7. Testing and release readiness
   - Unit tests for English, Roman Urdu, and Urdu script commands.
   - Integration tests against a seeded ERPNext site.
   - Rate-limit, suspension, backup, restore, and migration tests.
   - Security review for every write-capable tool.

## Not Yet Client Ready

The app is usable for controlled internal testing, but it is not yet ready for paid client production because confirmed CRUD, local Whisper, real LLM schema routing, offline license files, backup automation, monitoring, and restore drills are still pending.
