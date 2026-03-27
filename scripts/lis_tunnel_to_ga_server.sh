#!/usr/bin/env bash
# 공인 lis.* §0 — ga-server 호스트 :8000 을 로컬 uvicorn(기본 127.0.0.1:8000)으로 연결한다.
# 전제: 로컬에서 `uvicorn … --host 127.0.0.1 --port 8000` 가동, SSH Host(예: ga-server)에 GatewayPorts 허용.
# 백그라운드: nohup "$0" </dev/null >/tmp/lis-tunnel.log 2>&1 &
set -euo pipefail
LOCAL_PORT="${LOCAL_PORT:-8000}"
REMOTE_BIND="${REMOTE_BIND:-0.0.0.0}"
REMOTE_PORT="${REMOTE_PORT:-8000}"
SSH_HOST="${1:-ga-server}"
exec ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -R "${REMOTE_BIND}:${REMOTE_PORT}:127.0.0.1:${LOCAL_PORT}" "$SSH_HOST"
