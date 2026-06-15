# Security Model

## Purpose

This document defines the security model for `nexova_ai`, a secure AI assistant inside ERPNext v15. The assistant must respect Frappe permissions, tenant boundaries, and ERP data sensitivity while using Mistral only for language tasks.

## Security Principles

- Do not modify ERPNext core.
- Do not bypass Frappe permissions.
- Do not send full ERP data dumps to Mistral.
- Do not let Mistral execute ERP queries.
- Do not let Mistral generate SQL.
- Do not expose provider credentials to the browser.
- Default to read-only.
- Require confirmation for future actions.
- Audit every meaningful assistant request.

## Permission Model

The assistant must use the current Frappe user context.

Every ERP tool must check:

- User authentication
- User role
- Doctype read permission
- Document-level permissions where applicable
- Company access
- Tenant or site context
- Field sensitivity

Preferred query path:

- Use Frappe permission-aware APIs such as `frappe.get_list`.
- Use explicit doctypes and fields.
- Apply filters and limits.
- Avoid raw SQL.

If a future tool requires lower-level access, it must perform equivalent permission checks before returning any data.

## Role Model

Roles should map to ERPNext permissions rather than replacing them.

Common role categories:

- System Manager
- Accounts Manager
- Accounts User
- Sales Manager
- Sales User
- Purchase Manager
- Purchase User
- Stock Manager
- Stock User
- HR Manager
- HR User
- Projects Manager
- Projects User
- Support Team

Role checks should be tool-specific.

Examples:

- Profit and loss requires an accounts role and company access.
- HR summary requires an HR role.
- Stock balance requires stock or item read permissions.
- Support tickets require issue read permission.

The assistant should not grant access based only on natural language claims.

## Audit Logs

Every assistant request should produce audit metadata.

Recommended request audit fields:

- Timestamp
- Tenant or site
- User
- User roles
- Request channel, such as text or voice
- User message hash or redacted message
- Mistral provider request ID
- Intent
- Confidence
- Risk level
- Tool selected
- Tool parameters after validation
- Tool status
- Result row count
- Truncation flag
- Response status
- Latency
- Error message if any

Recommended tool audit fields:

- Tool name
- Tenant
- User
- Required permission
- Doctype names accessed
- Filters used
- Fields requested
- Row count returned
- Whether output was aggregated
- Whether output was redacted

Logs must not store secrets or unredacted sensitive data unless tenant policy explicitly permits it.

## Rate Limits

Rate limits should protect cost, performance, and abuse boundaries.

Recommended limits:

- Per user per minute
- Per user per day
- Per tenant per minute
- Per tenant per day
- Provider timeout limit
- Maximum input message length
- Maximum response size
- Maximum tool execution time
- Maximum date range per tool unless aggregation is used

When rate limits are exceeded, the assistant should return a clear message and avoid calling Mistral.

## Tenant Isolation

The future SaaS model should use one ERPNext site per client where practical.

Tenant isolation must apply to:

- Assistant settings
- Provider credentials
- Prompt logs
- Audit logs
- Tool results
- RAG documents
- RAG chunks
- Embeddings
- Cache entries
- Rate limits

No prompt, document chunk, embedding, cache entry, or tool output should be shared across tenants.

If shared infrastructure is used, every storage key and query must include tenant context.

## API Key Handling

Mistral API keys must:

- Be stored server-side only.
- Never be exposed to the browser.
- Never be committed to source code.
- Be configurable per site or tenant.
- Be readable only by authorized admin users.
- Be redacted in logs and errors.
- Support rotation.

Recommended storage:

- Frappe site config for deployment-level secrets
- Encrypted Frappe settings DocType later if admin UI is needed
- Environment variables where appropriate for hosting

The client should only call the Nexova AI backend endpoint. It should never call Mistral directly.

## Data Sent to Mistral

Allowed data:

- User's current message
- Accepted intent
- Validated extracted parameters
- Minimal user context such as locale or role category
- Compact ERP tool result
- Aggregated totals
- Counts
- Bounded status breakdowns
- Approved RAG snippets
- Source titles or section references

Mistral receives only the minimum context needed to classify or format an answer.

## Data Never Sent to Mistral

Never send:

- Full ERP database dumps
- Full tables
- Full invoice exports
- Full customer lists
- Full supplier lists
- Full item masters
- Payroll details
- Bank account details
- API keys
- Passwords
- Session cookies
- Raw SQL results from unrestricted queries
- Cross-tenant data
- Documents the user cannot access
- Embedding vectors
- Server environment variables

## Broad Request Handling

Requests for bulk data must be blocked or narrowed.

Examples of blocked requests:

- "Export all invoices"
- "Show every customer"
- "Dump the stock ledger"
- "Give me all employee records"
- "Show all supplier bank details"

Safe response pattern:

- State that bulk data cannot be provided through chat.
- Ask for a narrower filter such as date, company, customer, supplier, item, status, or project.
- Do not execute a broad ERP query.

## Confirmation Model for Future Actions

Future write actions require explicit confirmation.

Confirmation should include:

- Action name
- Target doctype
- Key parameters
- Business impact
- User identity
- Required role
- Final confirmation prompt

High-risk actions may require second approval.

Out of scope without a dedicated design:

- Submitting documents
- Cancelling documents
- Deleting documents
- Amending financial documents
- Changing permissions
- Creating users
- Modifying provider credentials

## Voice Security

Voice is a channel, not a separate permission model.

Voice safeguards:

- Transcribed text must use the same Assistant API.
- User identity must come from the authenticated ERPNext session.
- Sensitive responses should be concise.
- Highly sensitive values may need redaction before text-to-speech.
- Future write actions through voice require confirmation.
- Raw audio retention should be disabled by default.

## Incident and Failure Handling

If Mistral is unavailable:

- ERP tools should not be exposed directly unless a safe deterministic fallback exists.
- The assistant should return a temporary provider error.

If permission checks fail:

- Return a permission denied message.
- Do not reveal restricted values.

If an unsafe intent is detected:

- Do not execute tools.
- Log the event.
- Ask the user to narrow or rephrase if appropriate.
