# Invoxia AI Cloud and Local Deployment Modes

Invoxia AI must support two production models from one custom Frappe app:

- **Cloud Hosted** for clients who want access from anywhere, managed backups, easier support, and online subscription enforcement.
- **Local Offline** for privacy-sensitive clients who want ERP data, voice, documents, and AI processing to remain inside their office.

The internal package remains `nexova_ai`. The user-facing product is Invoxia AI.

## Mode 1: Cloud Hosted

Cloud Hosted is the default mode for normal SaaS clients.

Recommended settings:

- Deployment Mode: `Cloud Hosted`
- License Mode: `Online Subscription`
- STT Provider: `Browser` or `Cloud Deepgram`
- LLM Provider: `Deterministic`, `Cloud Mistral`, or `Cloud OpenAI`
- RAG Provider: `Disabled` or `Local` per site

Recommended architecture:

```text
Client browser
  -> HTTPS site such as client.invoxia.sohaib.systems
  -> ERPNext + Invoxia AI custom app
  -> Site database and files
  -> Optional cloud STT/LLM provider
```

Rules:

- One client should have one Frappe site and one database.
- ERP live data must always come from permission-aware Frappe tools.
- The LLM must never receive broad database dumps.
- Cloud STT/LLM providers must be optional and disclosed.
- Subscription checks can be online.
- Backups, monitoring, and restore tests are mandatory.

## Mode 2: Local Offline

Local Offline is for privacy-sensitive clients.

Recommended settings:

- Deployment Mode: `Local Offline`
- License Mode: `Signed Offline License`
- STT Provider: `Local Whisper`
- LLM Provider: `Local Ollama`
- RAG Provider: `Local`
- Local STT Endpoint: `http://127.0.0.1:9000`
- Local LLM Endpoint: `http://127.0.0.1:11434`
- Local RAG Endpoint: `local`

Recommended architecture:

```text
Client office LAN
  -> ERPNext + Invoxia AI on client-owned mini server
  -> Local MariaDB and site files
  -> Local Whisper STT service
  -> Local Ollama LLM service
  -> Local RAG/index storage
  -> Local backups
```

Rules:

- No public inbound port is required.
- No ERP data, voice audio, or documents should leave the client machine unless explicitly configured.
- Use local Whisper as the preferred Urdu/English STT path.
- Keep Vosk as an optional lightweight local command-mode fallback, not the main Urdu STT provider.
- Use local Ollama for intent routing and answer phrasing.
- Use a signed offline license file for 6-month or 12-month prepaid periods.
- If the license expires, disable Invoxia AI features only. Do not delete data and do not break ERPNext core.
- Local backups must be tested with restore drills.

## Mode 3: Hybrid

Hybrid is for clients who keep ERP data local but accept selected cloud AI services.

Example settings:

- Deployment Mode: `Hybrid`
- License Mode: `Signed Offline License` or `Online Subscription`
- STT Provider: `Cloud Deepgram`
- LLM Provider: `Local Ollama`
- RAG Provider: `Local`

Rules:

- Clearly disclose which data leaves the client environment.
- Prefer sending only audio to STT and only minimal intent text to LLM.
- Never send full ERP tables to external AI providers.

## Provider Responsibilities

STT providers convert speech to text.

- Browser: quick fallback, inconsistent across devices.
- Local Whisper: best local Urdu/English path.
- Local Vosk: private and lightweight, weaker for Urdu.
- Cloud Deepgram: preferred cloud Urdu/English path.
- Cloud OpenAI or Google: optional fallbacks.

LLM providers understand text and select safe tools.

- Deterministic: no LLM, rule-based only.
- Local Ollama: private local intent and answer phrasing.
- Cloud Mistral/OpenAI: optional cloud intelligence.
- OpenAI Compatible: self-hosted or third-party compatible endpoint.

RAG providers answer from approved documents.

- Disabled: no document Q&A.
- Local: client documents stay in the site/local store.
- Cloud: only for clients who explicitly accept cloud document processing.

## Safe Development Order

1. Keep current cloud demo stable.
2. Use the settings DocType as the single provider configuration source.
3. Implement LLM intent routing behind the existing tool registry.
4. Implement local Ollama provider.
5. Implement local Whisper STT provider.
6. Implement signed offline license verification.
7. Package a local Docker deployment profile.
8. Add cloud STT/LLM providers as optional premium settings.

## Non-Negotiables

- Do not modify ERPNext core.
- Do not patch Frappe core.
- Do not let any LLM directly query the database.
- Do not bypass Frappe permissions.
- Do not mix RAG answers with live ERP financial data.
- Do not store raw voice audio by default.
- Do not disable ERPNext core for license enforcement.
