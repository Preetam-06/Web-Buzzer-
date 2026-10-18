#!/bin/sh
set -eu

redis-server \
  --bind 127.0.0.1 \
  --protected-mode yes \
  --dir /app/redis-data \
  --appendonly yes &
redis_pid=$!

uvicorn main:app --host 0.0.0.0 --port 8000 &
backend_pid=$!

cleanup() {
  kill "$backend_pid" "$redis_pid" 2>/dev/null || true
}

trap cleanup INT TERM EXIT
wait "$backend_pid"
