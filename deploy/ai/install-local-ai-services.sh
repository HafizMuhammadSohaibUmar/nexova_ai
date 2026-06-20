#!/bin/sh
set -eu

PROJECT_NAME="${PROJECT_NAME:-invoxia-local}"
AI_ENV_FILE="${AI_ENV_FILE:-.env.ai}"

if [ ! -f "$AI_ENV_FILE" ]; then
  cp deploy/ai/.env.example "$AI_ENV_FILE"
fi

docker compose \
  -p "$PROJECT_NAME" \
  -f deploy/ai/docker-compose.ai.yml \
  -f deploy/ai/docker-compose.ai-local-ports.yml \
  --env-file "$AI_ENV_FILE" \
  up -d --build ollama whisper ollama-model-init

echo "Local AI services started with localhost-only ports."
echo "Configure Invoxia AI Settings:"
echo "  STT Provider: Local Whisper"
echo "  Local STT Endpoint: http://127.0.0.1:9000"
echo "  LLM Provider: Local Ollama"
echo "  Local LLM Endpoint: http://127.0.0.1:11434"
