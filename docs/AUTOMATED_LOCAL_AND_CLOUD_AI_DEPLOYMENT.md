# Automated Local and Cloud AI Deployment

Invoxia AI should not require manual installation of Whisper, Ollama, or Qwen for each client. The production direction is to ship them as deployment services.

## What Gets Installed Automatically

- Ollama runtime.
- Configured Qwen model, default `qwen3:14b`.
- whisper.cpp server.
- Configured Whisper model, default `large-v3-turbo-q5_0`.
- Private Docker volumes for model storage.

## Cloud Hosted Mode

Cloud AI services run beside the ERPNext containers on the private Docker network.

Expected Invoxia AI settings:

```text
Deployment Mode: Cloud Hosted
STT Provider: Local Whisper
Local STT Endpoint: http://whisper:9000
LLM Provider: Local Ollama
Local LLM Endpoint: http://ollama:11434
License Mode: Online Subscription
```

Run from the deployment directory that contains the ERPNext `docker-compose.yml`:

```bash
cp /path/to/nexova_ai/deploy/ai/.env.example .env.ai
cp -R /path/to/nexova_ai/deploy ./deploy
sh deploy/ai/install-cloud-ai-services.sh
```

The services are not published publicly. They are only reachable by containers on the Compose network.

## Local Offline Mode

Local AI services run on the client machine or local office server. Host bindings are localhost-only.

Expected Invoxia AI settings:

```text
Deployment Mode: Local Offline
STT Provider: Local Whisper
Local STT Endpoint: http://127.0.0.1:9000
LLM Provider: Local Ollama
Local LLM Endpoint: http://127.0.0.1:11434
License Mode: Signed Offline License
```

Run from the repository root:

```bash
cp deploy/ai/.env.example .env.ai
sh deploy/ai/install-local-ai-services.sh
```

## Model Selection

Use the Invoxia standard profile first:

```text
OLLAMA_MODEL=qwen3:14b
WHISPER_MODEL=large-v3-turbo-q5_0
```

For weak machines:

```text
OLLAMA_MODEL=qwen3:4b
WHISPER_MODEL=base
```

For premium GPU-backed installs:

```text
OLLAMA_MODEL=qwen3:30b
WHISPER_MODEL=large-v3-turbo
```

## Security Rules

- Never expose port `11434` to the public internet.
- Never expose port `9000` to the public internet.
- For cloud, use Docker service names: `ollama` and `whisper`.
- For local desktop testing, bind only to `127.0.0.1`.
- Keep raw audio retention disabled unless the client explicitly approves recording retention.

## Current App Integration Status

This repository now includes automated service deployment files. The next development step is adding runtime connector code in the Frappe app:

- Audio upload API.
- Call whisper.cpp for STT.
- Call Ollama/Qwen for strict JSON intent routing.
- Validate intent against the tool registry.
- Execute only approved read tools or safe confirmed action drafts.
