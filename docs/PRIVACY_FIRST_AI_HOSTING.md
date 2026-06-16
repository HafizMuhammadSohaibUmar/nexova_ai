# Privacy-First AI Hosting

## Purpose

This document defines the privacy-first AI hosting model for Invoxia Assistant. The assistant must support local-first mode and optional Mistral API mode while protecting ERPNext data for privacy-sensitive clients.

In v1, the assistant supports navigation, live data Q&A, voice, and RAG. It does not perform CRUD actions.

## Exact Recommended Architecture

AI modes:

- Local-first mode: preferred default for privacy-sensitive clients.
- Optional Mistral API mode: enabled per site only when approved.

Local-first mode may include:

- Local intent classification where feasible.
- Local speech-to-text where feasible.
- Local embeddings where feasible.
- Local or deterministic response formatting for simple ERP summaries.
- Tenant-scoped local RAG retrieval.

Mistral API mode may include:

- Intent classification.
- Parameter extraction.
- Response formatting.

Mistral must not receive:

- Full ERP tables
- Full data exports
- Database dumps
- Credentials
- Cross-client data
- RAG chunks from unauthorized documents
- Raw private files

Mistral may receive:

- User question
- Validated compact tool output
- Approved RAG snippets
- Non-sensitive formatting instructions
- Minimal locale context for Urdu or English response

## Urdu and English Support

The assistant must support:

- English input and output.
- Urdu input and output.
- Mixed Urdu-English business phrasing.
- Locale-aware response formatting.
- Voice transcript handling for both languages where provider support exists.

Language handling rules:

- Detect requested language from user message or user preference.
- Preserve ERP values exactly.
- Do not translate document names, invoice numbers, item codes, or customer IDs unless explicitly requested.
- Use local-first speech components where privacy requires it.

## Step-by-Step Deployment Flow

1. Create the client site.
2. Configure Invoxia Assistant settings for the site.
3. Select AI mode: local-first or Mistral API.
4. If local-first, configure approved local models or deterministic mode.
5. If Mistral API, configure server-side site credentials.
6. Configure allowed data sharing policy for the site.
7. Enable language preferences for English, Urdu, or both.
8. Configure RAG storage as tenant-scoped if RAG is enabled.
9. Test a live data Q&A request with minimal tool output.
10. Test a RAG question with approved documents.
11. Test voice input and output in English and Urdu where supported.
12. Review audit logs before production enablement.

## Risks

- Optional API mode can send sensitive prompt content if prompts are too broad.
- Voice transcripts may contain confidential business details.
- RAG snippets can leak policy content if permissions are wrong.
- Urdu transcription quality may vary by provider or local model.
- Local AI can require more CPU and RAM.
- Shared local AI services can accidentally mix tenant context without strict request isolation.

## Rollback Strategy

- Disable Mistral API mode per site.
- Revert to local-first or deterministic response mode.
- Disable RAG per site if retrieval permissions are suspect.
- Disable voice features while keeping text Q&A available.
- Rotate provider API keys if exposure is suspected.
- Purge tenant-specific AI cache or RAG cache if required.

## What Not To Do

- Do not call Mistral directly from the browser.
- Do not send full ERP data to any AI provider.
- Do not use one shared prompt cache across clients.
- Do not store raw voice audio by default.
- Do not index live transactional ERP data into RAG by default.
- Do not enable Mistral API mode without client approval.
- Do not translate ERP identifiers in a way that changes meaning.
- Do not enable CRUD actions in v1.
