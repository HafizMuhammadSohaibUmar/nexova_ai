#!/bin/sh
set -eu

MODEL_NAME="${WHISPER_MODEL:-small}"
PORT="${WHISPER_PORT:-9000}"
MODEL_FILE="/models/ggml-${MODEL_NAME}.bin"

if [ ! -f "$MODEL_FILE" ]; then
  echo "Downloading whisper.cpp model: ${MODEL_NAME}"
  cd /opt/whisper.cpp
  ./models/download-ggml-model.sh "$MODEL_NAME"
  cp "/opt/whisper.cpp/models/ggml-${MODEL_NAME}.bin" "$MODEL_FILE"
fi

if [ -x /opt/whisper.cpp/build/bin/whisper-server ]; then
  SERVER_BIN="/opt/whisper.cpp/build/bin/whisper-server"
elif [ -x /opt/whisper.cpp/build/bin/server ]; then
  SERVER_BIN="/opt/whisper.cpp/build/bin/server"
else
  echo "whisper.cpp server binary was not found." >&2
  exit 1
fi

exec "$SERVER_BIN" --host 0.0.0.0 --port "$PORT" -m "$MODEL_FILE"
