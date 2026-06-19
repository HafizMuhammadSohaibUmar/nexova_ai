# Product Scope

## Purpose

`nexova_ai` is a custom Frappe app for ERPNext v15. Its purpose is to provide a secure AI and voice assistant that helps authorized ERPNext users ask questions, retrieve live ERP summaries, understand company knowledge, and eventually perform controlled ERP actions.

The product must not modify ERPNext core. All capabilities must be delivered through the custom app, Frappe APIs, explicit Python tools, and permission-aware backend services.

Mistral is the first LLM provider. It is used only for:

- Intent classification
- Parameter extraction
- Response formatting

ERPNext data is fetched only by explicit Python tools that enforce Frappe permissions.

## Product Principles

- ERPNext remains the system of record.
- Mistral never receives full ERP database dumps.
- Every ERP operation is permission-aware.
- Every assistant action is auditable.
- Read tools come before write tools.
- Write tools require confirmation and stricter controls.
- Multi-tenant SaaS support is planned from the start.
- RAG and voice share the same secure backend orchestration model.

## Production V1 Foundation Scope

The production v1 foundation establishes the assistant inside ERPNext Desk with a safe set of read-only capabilities.

### Foundation Goals

- Provide a Nexova AI Desk page.
- Accept typed user questions.
- Support browser voice input where available.
- Support browser text-to-speech where available.
- Classify simple ERP intents.
- Execute a small number of explicit read-only ERP tools.
- Return concise natural-language answers.
- Respect Frappe permissions.
- Avoid raw SQL and ERPNext core changes.

### Foundation Capabilities

- Today's submitted sales summary
- Stock balance summary
- Stock balance for a specific item
- Pending receivables summary
- Supported-capabilities fallback
- Basic permission denied response

### Foundation Non-Goals

- No write actions
- No document creation
- No workflow approvals
- No RAG
- No server-side speech-to-text
- No custom vector database
- No autonomous agent behavior
- No direct Mistral access from the browser

## v1 Scope

v1 turns the foundation into a structured assistant platform with a formal tool registry and Mistral integration.

### v1 Goals

- Add Mistral as the first LLM provider.
- Add an intent schema and validation layer.
- Add a formal ERP tool registry.
- Add audit logs for assistant requests and tool executions.
- Expand read-only ERP coverage across common modules.
- Add tenant-aware configuration foundations.
- Add admin settings for provider credentials and feature flags.

### v1 Capabilities

- Sales summaries
- Purchase summaries
- Stock summaries
- Receivables summaries
- Payables summaries
- Customer summaries
- Supplier summaries
- Item lookup
- Quotation summaries
- Sales order summaries
- Purchase order summaries
- Invoice summaries
- Profit and loss summary
- Cash flow summary
- HR summary
- Project summary
- Support ticket summary

### v1 Safety Boundaries

- Read-only tools only.
- No bulk exports through chat.
- No arbitrary doctype queries.
- No LLM-generated SQL.
- No raw database access by Mistral.
- Permission checks on every tool.
- Tool outputs are compact and schema-bound.

## v2 Scope

v2 adds knowledge retrieval and richer user assistance while preserving strict ERP data boundaries.

### v2 Goals

- Add future RAG support.
- Index approved company documents.
- Index ERP manuals, SOPs, and policies.
- Enforce role-based document retrieval.
- Improve explainability with source references.
- Add deeper voice assistant support.
- Add stronger observability and usage analytics.

### v2 Capabilities

- Ask questions over company documents.
- Ask questions over ERPNext manuals.
- Retrieve SOPs and policies by role.
- Combine ERP tool results with approved knowledge snippets.
- Support server-side speech-to-text if needed.
- Support server-side text-to-speech if needed.
- Add admin dashboards for assistant usage and failed intents.

### v2 Safety Boundaries

- RAG indexes are tenant-scoped.
- Document chunks retain access metadata.
- Live transactional ERP data is not indexed by default.
- Retrieved snippets are filtered by user permissions.
- Voice requests use the same backend permissions as text requests.

## v3 Scope

v3 introduces controlled actions and workflow-aware assistance.

### v3 Goals

- Add confirmation-gated write actions.
- Add workflow-aware ERP operations.
- Add approval-aware assistant behavior.
- Add proactive insights and scheduled summaries.
- Support mature multi-tenant SaaS operations.

### v3 Capabilities

- Draft quotations
- Draft sales orders
- Draft purchase orders
- Draft invoices
- Create support tickets
- Create tasks or project updates
- Prepare approval summaries
- Notify users about exceptions
- Generate scheduled business summaries
- Suggest next actions based on safe tool outputs

### v3 Safety Boundaries

- Write actions require explicit confirmation.
- High-risk actions require role checks and possibly second approval.
- Assistant must never submit, cancel, delete, or amend critical documents without a dedicated approval design.
- Action tools must be separate from read tools.
- Every write attempt must be logged with before and after metadata.

## Long-Term Direction

The long-term product is an ERP operating assistant that can answer, explain, retrieve, summarize, draft, and eventually execute approved workflows. Its value comes from combining natural language with ERPNext's permission system, not bypassing it.

The assistant should grow from safe read-only summaries into a governed operations layer for ERPNext.
