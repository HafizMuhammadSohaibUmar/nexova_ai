# RAG Architecture

## Purpose

Future RAG support will allow `nexova_ai` to answer questions using approved company knowledge, ERP manuals, SOPs, and policies. RAG must be separate from live ERP data access.

Live ERP data should continue to be fetched only through explicit Python tools. RAG provides document knowledge, not unrestricted database retrieval.

## Knowledge Sources

Supported future sources:

- Company documents
- ERPNext manuals
- Internal SOPs
- HR policies
- Finance policies
- Procurement policies
- Sales playbooks
- Support playbooks
- Training documents
- Nexova implementation guides

Excluded by default:

- Full ERP database tables
- Full transaction ledgers
- Payroll records
- Bank statements
- Raw invoice exports
- Unapproved personal files

## Tenant Isolation

Each tenant or Frappe site must have isolated RAG storage.

Isolation requirements:

- Separate vector namespace per tenant.
- Separate document metadata per tenant.
- Tenant ID stored on every document and chunk.
- Tenant ID included in every retrieval filter.
- No cross-tenant shared retrieval results.
- Deletion by tenant must remove documents, chunks, and embeddings.

For future SaaS, one ERPNext site per client is the preferred isolation model. If multiple tenants ever share infrastructure, the RAG layer must still enforce tenant keys at storage, retrieval, and audit layers.

## Role-Based Access

Every indexed document must include access metadata.

Recommended metadata:

- `tenant_id`
- `site_name`
- `document_id`
- `source_type`
- `title`
- `version`
- `department`
- `allowed_roles`
- `allowed_users`
- `company`
- `confidentiality`
- `created_at`
- `updated_at`
- `source_url`

Retrieval must filter chunks by:

- Current tenant
- Current user
- Current roles
- Company access
- Department access if configured
- Document confidentiality level

Mistral should only receive snippets that pass these filters.

## Document Ingestion Flow

1. Admin or authorized user uploads or registers a document.
2. Backend validates file type and tenant context.
3. Backend extracts text.
4. Backend detects or assigns document metadata.
5. Backend chunks text into retrieval-sized pieces.
6. Backend generates embeddings for each chunk.
7. Backend stores chunks and embeddings in tenant-scoped storage.
8. Backend records document version and ingestion audit metadata.

## Chunking Strategy

Chunking should preserve meaning and source traceability.

Recommended approach:

- Split by headings where possible.
- Keep chunks around a configurable token or character size.
- Add overlap between adjacent chunks.
- Store source page, section, or heading when available.
- Keep each chunk linked to the parent document.
- Store role and tenant metadata on every chunk.

Chunk metadata should include:

- `chunk_id`
- `document_id`
- `tenant_id`
- `heading`
- `page_number`
- `chunk_index`
- `text_hash`
- `allowed_roles`
- `allowed_users`
- `company`
- `source_type`

## Embeddings

Embeddings convert document chunks into vectors for similarity search.

Requirements:

- Embedding provider must be configurable.
- Embeddings must be tenant-scoped.
- Embedding requests should not include unnecessary sensitive metadata.
- Embedding indexes must support deletion and re-indexing.
- Embedding storage must be backed up or reproducible from source documents.

Potential storage options:

- PostgreSQL with vector support if available in the hosting stack
- Dedicated vector database on VPS
- Managed vector database later if scale requires it

The first implementation should favor operational simplicity and cost control.

## Retrieval Flow

1. User asks a question.
2. Assistant API authenticates the user and resolves tenant context.
3. Orchestrator classifies the request.
4. If knowledge retrieval is needed, the retriever builds a search query.
5. Retriever searches only tenant-scoped indexes.
6. Retriever applies role and document access filters.
7. Top matching chunks are returned with source metadata.
8. Orchestrator combines approved snippets with any ERP tool result.
9. Mistral generates the final response using only provided snippets and tool output.
10. Response includes source references when useful.

## ERP Tool and RAG Combination

Some questions need both live ERP data and document knowledge.

Example:

- User asks, "What are our overdue receivables and what is the collection SOP?"

Safe flow:

1. Intent detection identifies receivables plus policy lookup.
2. ERP tool returns compact receivables summary.
3. RAG retrieves approved collection SOP snippets.
4. Mistral formats an answer from both approved inputs.

The ERP result remains compact. RAG does not replace ERP tools.

## Prompt Context Rules

Mistral may receive:

- User question
- Approved RAG snippets
- Source titles and section references
- Compact ERP tool output
- Response instructions

Mistral must not receive:

- Full document collections
- Full ERP exports
- Chunks the user is not allowed to access
- Cross-tenant snippets
- Raw embedding vectors
- Secrets or credentials

## Source References

Responses should cite or mention sources when answering from documents.

Reference style can include:

- Document title
- Section heading
- Page number if available
- Version if relevant

The assistant should clearly distinguish:

- ERP live data from Python tools
- Knowledge snippets from RAG
- General unsupported questions

## Governance

RAG requires administrative controls:

- Enable or disable RAG per tenant.
- Configure allowed source types.
- Re-index documents.
- Delete documents and embeddings.
- View ingestion status.
- Review retrieval logs.
- Set retention policies.
- Set confidentiality levels.

## Failure Modes

If no relevant document is found:

- The assistant should say it could not find an approved source.
- It should not invent policy details.

If the user lacks document access:

- The assistant should not reveal the existence or contents of restricted documents unless policy allows it.

If embeddings are unavailable:

- ERP tools should continue to work.
- RAG answers should gracefully degrade.
