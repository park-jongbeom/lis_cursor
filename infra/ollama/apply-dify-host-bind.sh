#!/usr/bin/env bash
# Ollama systemd 서비스에 OLLAMA_HOST=0.0.0.0:11434 적용 (Dify 컨테이너 연동용)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="${ROOT}/infra/ollama/systemd/ollama.service.d/idr-dify.conf"
DST_DIR="/etc/systemd/system/ollama.service.d"
DST="${DST_DIR}/idr-dify.conf"

if [[ ! -f "$SRC" ]]; then
  echo "오류: $SRC 없음" >&2
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "오류: systemctl 없음 (systemd 환경에서 실행하세요)" >&2
  exit 1
fi

echo "다음 파일을 설치합니다 (sudo 필요):"
echo "  $SRC"
echo "  -> $DST"
sudo mkdir -p "$DST_DIR"
sudo cp "$SRC" "$DST"
sudo systemctl daemon-reload
sudo systemctl restart ollama
echo "완료. 확인: ss -tlnp | grep 11434  (0.0.0.0:11434 또는 *:11434 기대)"
echo "Dify Ollama Base URL 예: http://host.containers.internal:11434"
