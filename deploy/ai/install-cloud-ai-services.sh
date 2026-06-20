#!/bin/sh
set -eu

PROJECT_NAME="${PROJECT_NAME:-invoxia}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
AI_ENV_FILE="${AI_ENV_FILE:-.env.ai}"

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Run this from your frappe_docker deployment directory, or set COMPOSE_FILE." >&2
  exit 1
fi

if [ ! -f "$AI_ENV_FILE" ]; then
  cp deploy/ai/.env.example "$AI_ENV_FILE"
fi

docker compose \
  -p "$PROJECT_NAME" \
  -f "$COMPOSE_FILE" \
  -f deploy/ai/docker-compose.ai.yml \
  --env-file "$AI_ENV_FILE" \
  up -d --build ollama whisper ollama-model-init

echo "Cloud/private AI services started."
echo "Configure Invoxia AI Settings:"
echo "  STT Provider: Local Whisper"
echo "  Local STT Endpoint: http://whisper:9000"
echo "  LLM Provider: Local Ollama"
echo "  Local LLM Endpoint: http://ollama:11434"
