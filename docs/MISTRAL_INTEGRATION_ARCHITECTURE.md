# Mistral Integration Architecture for Nexova AI

## Purpose

This document defines the target architecture for integrating Mistral into `nexova_ai`, a Frappe / ERPNext assistant. The design keeps ERP data access deterministic, permission-aware, and auditable while using Mistral only where language intelligence is useful:

- Intent detection
- Response generation

Mistral must not query ERPNext directly, receive bulk ERP exports, generate database queries, or decide which records to access without passing through explicit server-side Python tools.

## Core Principles

1. Mistral is a language layer, not a data layer.
2. ERPNext remains the system of record.
3. All ERP data access goes through explicit Python functions with fixed permissions, filters, limits, and return schemas.
4. Tenant, site, company, and user permissions are enforced before and during every ERP tool execution.
5. Only minimal, task-specific data is shared with Mistral.
6. Every assistant action must be traceable to a user, tenant, intent, tool, and response.
7. The architecture should support future RAG and voice features without changing the ERP data safety model.

## High-Level Architecture

The assistant should be split into five layers:

1. Client Interface
2. Assistant API
3. Orchestration Layer
4. ERP Tool Layer
5. AI Provider Layer

### Client Interface

The client interface is the Frappe Desk page for Nexova AI. It sends the user's message to the backend and displays the response.

Current browser voice input and text-to-speech can remain client-side for the MVP. Future voice features should still route transcribed user intent through the same backend assistant API.

Responsibilities:

- Capture user text or voice transcript
- Send one user request at a time to the assistant API
- Display response text and structured metadata
- Optionally play response audio in future voice mode
- Never call Mistral directly from the browser
- Never receive secrets or provider credentials

### Assistant API

The Assistant API is the only public backend entrypoint for chat requests.

Responsibilities:

- Authenticate the Frappe user
- Resolve tenant context from the current Frappe site
- Resolve allowed companies, roles, and user permissions
- Validate request size and input type
- Create an audit record for the request
- Pass sanitized text and context to the orchestration layer
- Return the final assistant response

The API should not contain ERP business logic directly. It should delegate business operations to the ERP Tool Layer.

### Orchestration Layer

The Orchestration Layer controls the assistant workflow. It decides when to call Mistral and when to call ERP tools.

Responsibilities:

- Build the intent detection prompt
- Call Mistral for intent classification only
- Validate the returned intent against an allowlist
- Select the matching Python ERP tool
- Execute the ERP tool with explicit parameters
- Build the response generation prompt
- Call Mistral for final wording only
- Apply output safety checks
- Return a structured response to the API

The orchestrator must treat Mistral output as untrusted. It may use Mistral's intent result as a suggestion, but only after validating it against local schemas and allowed tools.

### ERP Tool Layer

The ERP Tool Layer is the only layer allowed to query ERPNext data.

Each supported ERP capability should be implemented as an explicit Python function. A tool should have:

- Stable name
- Narrow purpose
- Typed input schema
- Typed output schema
- Permission checks
- Tenant and company scoping
- Fixed query implementation
- Row and field limits
- Safe aggregation behavior
- Audit metadata

Examples of future tools:

- Get today's submitted sales totals
- Get stock balance for a specific item
- Get pending receivables summary
- Get customer outstanding summary
- Get purchase order status
- Get item availability by warehouse

Tools should return compact summaries, not full record dumps. If a user asks for broad data, the tool should return aggregated totals, counts, and a message asking for a narrower filter.

### AI Provider Layer

The AI Provider Layer wraps calls to Mistral.

Responsibilities:

- Store provider configuration outside source code
- Inject tenant-safe system prompts
- Apply request and response limits
- Attach provider request IDs to audit logs
- Handle retries and timeouts
- Normalize provider errors
- Allow future provider replacement without changing ERP tools

Mistral must only receive:

- User message text
- Minimal authenticated context, such as role category or locale
- Tool result summaries selected by the backend
- No bulk tables
- No raw document exports
- No unrestricted record lists
- No credentials
- No cross-tenant identifiers

## Request Flow

### Standard Chat Flow

1. User enters a message in the Nexova AI Desk page.
2. Client sends the message to the Assistant API.
3. Assistant API authenticates the user and resolves tenant context.
4. Orchestrator sends a minimal intent detection request to Mistral.
5. Mistral returns a structured intent candidate.
6. Orchestrator validates the intent against local allowlists.
7. Orchestrator calls one explicit Python ERP tool.
8. ERP tool checks permissions and queries ERPNext through Frappe APIs.
9. ERP tool returns a compact, structured result.
10. Orchestrator sends only the compact result to Mistral for response generation.
11. Mistral returns a natural-language response.
12. Orchestrator applies final safety checks.
13. Assistant API returns the answer to the client.
14. Audit logs store the request, intent, tool name, tenant, user, and response metadata.

### Unknown Intent Flow

If Mistral returns an unsupported or low-confidence intent:

1. The orchestrator rejects the intent.
2. No ERP tool is executed.
3. The assistant returns a clarification or supported-capabilities message.
4. The event is logged for future improvement.

### Broad Data Request Flow

If the user asks for bulk data, such as all invoices, all customers, or full stock ledger exports:

1. Intent detection may classify the domain.
2. The orchestrator detects the request as too broad.
3. No bulk ERP query is executed.
4. The response asks the user to narrow by date, item, customer, company, or status.

## Data Safety Rules

### Data Sent to Mistral

Allowed:

- User's direct question
- Intent labels
- Small tool result summaries
- Aggregated totals
- Counts
- Currency codes
- Date ranges requested by the user
- Non-sensitive labels needed to answer the question

Restricted:

- Full invoice lists
- Full customer lists
- Full item masters
- Ledger dumps
- Payroll records
- Credentials
- API keys
- Session cookies
- Raw database rows beyond the explicit tool result schema
- Cross-tenant data
- Data from companies the user cannot access

### ERP Query Rules

ERP queries must:

- Be implemented in Python tools
- Use permission-aware Frappe APIs wherever possible
- Apply tenant and company filters
- Use explicit fields
- Use bounded result limits
- Prefer aggregation over record lists
- Avoid raw SQL unless reviewed and justified later
- Never be generated by Mistral

## Intent Detection Design

Intent detection should produce structured output with:

- Intent name
- Confidence
- Extracted parameters
- Missing parameters
- Safety classification

Example intent categories:

- `sales_today_summary`
- `stock_balance_lookup`
- `receivables_summary`
- `unsupported`
- `needs_clarification`
- `unsafe_bulk_request`

The orchestrator should only accept intent names registered in a local allowlist. Extracted parameters must be validated locally before tool execution.

## Response Generation Design

Mistral may generate the final response after ERP tool execution. It should receive:

- The original user question
- The accepted intent
- A compact tool result
- Formatting instructions
- Safety instructions

The response generation prompt should instruct Mistral to:

- Answer only from the provided tool result
- Avoid inventing ERP values
- State when data is unavailable
- Ask for clarification when the result requires narrower filters
- Keep financial and operational answers concise

The backend should return both:

- `message`: user-facing answer
- `data`: structured result for future UI rendering

## Multi-Tenant SaaS Design

Nexova AI should treat each Frappe site as a tenant boundary.

Tenant context should include:

- Site name
- Tenant ID if introduced later
- User
- Roles
- Allowed companies
- Locale
- Currency defaults
- Feature flags
- Provider configuration reference

Multi-tenant safeguards:

- Never share prompts, tool results, logs, cache entries, embeddings, or provider configuration across tenants.
- Include tenant identifiers in audit logs and storage keys.
- Scope future RAG indexes by tenant and company.
- Scope rate limits by tenant and user.
- Support tenant-level feature flags for Mistral, RAG, and voice.
- Allow tenant-specific Mistral credentials or a shared provider account with strict metadata isolation.

## Future RAG Support

RAG should be added as a separate retrieval layer, not mixed directly into ERP querying.

Recommended RAG sources:

- Help documentation
- SOPs
- Company policies
- ERPNext user guides
- Nexova-specific knowledge base articles
- Non-sensitive configuration explanations

RAG should not index live transactional ERP data by default.

Future RAG flow:

1. User asks a question.
2. Orchestrator classifies whether the request needs ERP data, knowledge retrieval, or both.
3. RAG retriever searches tenant-scoped knowledge indexes.
4. Retrieved snippets are filtered by tenant, role, and document permissions.
5. Mistral receives only the top relevant snippets and any compact ERP tool result.
6. Final response cites or references the retrieved knowledge where appropriate.

RAG safeguards:

- Tenant-isolated vector indexes
- Permission-aware document ingestion
- Source metadata on every chunk
- Chunk-level access checks
- No ingestion of unrestricted ERP tables
- Separate indexes for public docs, tenant docs, and private docs
- Configurable retention and deletion per tenant

## Future Voice Assistant Support

Voice should be an input and output channel over the same assistant backend.

Voice architecture:

- Speech-to-text converts audio to text.
- The text is sent to the existing Assistant API.
- The normal orchestration, tool execution, and Mistral response flow runs unchanged.
- Text-to-speech converts the final answer to audio.

Voice-specific safeguards:

- Confirm before executing sensitive or write-capable actions if those are added later.
- Keep ERP data access read-only unless a future approval workflow is designed.
- Log transcript text, not raw audio, unless tenant policy explicitly enables audio retention.
- Redact or avoid reading highly sensitive values aloud.
- Support tenant-level enablement and user-level permissions.

## Audit, Observability, and Governance

Each assistant request should log:

- Timestamp
- Tenant or site
- User
- Roles or permission profile
- User message hash or stored message according to tenant policy
- Mistral provider request ID
- Accepted intent
- Confidence
- Tool executed
- Tool parameters
- Result size summary
- Final response status
- Errors and latency

Sensitive logs should be redacted and retention-controlled.

Recommended operational controls:

- Per-user and per-tenant rate limits
- Provider timeout limits
- Circuit breaker for provider failures
- Admin setting to disable AI per tenant
- Admin setting to disable RAG or voice per tenant
- Review dashboard for unsupported intents
- Test fixtures for intent classification and tool permission behavior

## Security Boundaries

Mistral must not:

- Access the database
- Receive credentials
- Generate SQL
- Choose arbitrary doctypes or fields
- Receive bulk ERP exports
- See data outside the current tenant
- Override local permission checks
- Execute tools not registered by the backend

The backend must:

- Validate every intent
- Validate every parameter
- Enforce tenant and user permissions
- Use explicit tool allowlists
- Limit tool result sizes
- Redact sensitive fields before response generation
- Treat AI output as untrusted text

## Recommended Implementation Phases

### Phase 1: Safe Mistral Wrapper

- Add provider configuration
- Add Mistral client wrapper
- Add intent detection prompt
- Add response generation prompt
- Keep existing ERP capabilities as explicit tools
- Add audit logging

### Phase 2: Tool Registry

- Move ERP capabilities into a formal tool registry
- Define input and output schemas
- Add intent-to-tool routing
- Add parameter validation
- Add automated tests for permissions and broad-data rejection

### Phase 3: Multi-Tenant Hardening

- Add tenant-aware configuration
- Add tenant and user rate limits
- Add feature flags
- Add tenant-scoped audit records
- Add provider key isolation strategy

### Phase 4: RAG Foundation

- Add tenant-scoped document ingestion
- Add vector index abstraction
- Add permission-aware retrieval
- Add source-aware response generation
- Keep live ERP data outside the RAG index unless explicitly approved later

### Phase 5: Voice Assistant

- Add server-compatible speech-to-text option if browser speech is not enough
- Keep the same Assistant API
- Add text-to-speech provider abstraction if needed
- Add voice-specific confirmations and redaction rules

## Target Module Boundaries

Suggested future boundaries:

- `api`: public whitelisted endpoints
- `orchestrator`: assistant workflow and routing
- `providers`: Mistral and future AI provider wrappers
- `tools`: explicit ERP Python tools
- `schemas`: intent, tool input, and tool output schemas
- `security`: tenant, role, permission, and redaction helpers
- `rag`: future retrieval interfaces
- `voice`: future speech interfaces
- `audit`: request and tool execution logging

These boundaries are architectural only. No code should be added until the design is approved.

## Final Position

The recommended design keeps Mistral behind a narrow AI Provider Layer and uses it only for intent detection and response wording. ERPNext data stays protected behind explicit Python tools that enforce permissions, tenant boundaries, field selection, row limits, and audit logging.

This gives Nexova AI a safe MVP path while leaving clear extension points for RAG, voice, and multi-tenant SaaS growth.
