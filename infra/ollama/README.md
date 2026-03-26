# 호스트 Ollama — Dify(Podman) 연동

Dify API 컨테이너는 `host.containers.internal`이 **호스트 LAN IP**로 풀리는 경우가 많습니다. Ollama가 **`127.0.0.1:11434`만** 리슨하면 해당 IP로의 접속이 거절됩니다.

## 적용 (systemd `ollama` 서비스)

프로젝트 루트에서:

```bash
chmod +x infra/ollama/apply-dify-host-bind.sh
./infra/ollama/apply-dify-host-bind.sh
```

또는:

```bash
make ollama-dify-host-bind
```

동작: `OLLAMA_HOST=0.0.0.0:11434` 를 `/etc/systemd/system/ollama.service.d/idr-dify.conf`에 설치한 뒤 `daemon-reload` 및 `ollama` 재시작.

## 검증

```bash
ss -tlnp | grep 11434
```

`0.0.0.0:11434` 또는 `*:11434` 가 보이면 됩니다.

## Dify UI

- Base URL: `http://host.containers.internal:11434` (또는 호스트 실제 IP 동일 포트)
- 방화벽에서 `11434/tcp` 가 막혀 있으면 허용

## 원복

```bash
sudo rm -f /etc/systemd/system/ollama.service.d/idr-dify.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama
```
