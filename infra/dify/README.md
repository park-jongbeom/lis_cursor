# Dify Self-hosted (공식 1.13.2 벤더 + IDR 오버레이)

## 구성

| 경로 | 설명 |
|------|------|
| `vendor/` | [langgenius/dify](https://github.com/langgenius/dify) 태그 **1.13.2**의 `docker/` 디렉터리 + **IDR 필수 패치** (아래 참고) |
| `docker-compose.idr.yml` | Podman(RHEL)·Postgres `15434`·`postgres:15-bookworm`·`security_opt` |
| `.env` | **직접 생성** (아래 초기화) |

### `vendor/docker-compose.yaml` IDR 패치 (재동기화 시 재적용)

1. **podman-compose**: `depends_on`에 `db_mysql` / `oceanbase` / `seekdb`(required:false)가 있으면 `KeyError` → **api / worker / worker_beat / plugin_daemon** 에서 해당 항목 제거, `db_postgres`는 `required:false` 제거.
2. **rootless**: nginx 의 호스트 **443** 매핑 제거(한 줄만 남김).
3. **이미지 pull**: 루트 파티션 부족 시 `TMPDIR=$HOME/tmp` 사용(`Makefile`이 기본 설정).

### `.env` 권장

- `COMPOSE_PROFILES=weaviate,postgresql` (문자열 그대로; `${VECTOR_STORE}` 형식은 podman-compose에서 프로필 미적용될 수 있음)
- `EXPOSE_NGINX_PORT=8080`

### Dify API와 `idr-net`

Podman에서 **api/worker에 `idr-net`을 동시에 붙이면** 내부 DNS가 `redis` 호스트를 못 찾는 경우가 있다. 현재 오버레이는 **Dify 백엔드에 idr-net을 붙이지 않는다.** Workflow의 HTTP Request는 `host.containers.internal:8000` 등으로 호스트 FastAPI를 호출하면 된다.

## 0.15.x 스택을 켜 둔 경우

이전 `docker-compose.dify.yml`으로 뜬 컨테이너(`dify-api` 등)는 **먼저 내린 뒤** 1.13 스택을 올리세요. 포트 **8080**·**15434**가 겹치면 기동에 실패합니다.

```bash
# 예: 예전 파일이 있던 시절의 컨테이너만 골라 중지 (이름은 환경마다 다름)
podman stop dify-nginx dify-api dify-worker dify-web dify-db dify-redis dify-weaviate dify-sandbox 2>/dev/null || true
```

## 최초 설정

```bash
cd infra/dify
cp vendor/.env.example .env
```

`.env`에서 최소 확인:

- **`EXPOSE_NGINX_PORT=8080`** — rootless 환경에서 80 대신 호스트 `8080` (기본값 80이면 실패할 수 있음)
- **`SECRET_KEY`**, **`DB_PASSWORD`**, **`REDIS_PASSWORD`** — 기본값 그대로 두지 말 것
- **`COMPOSE_PROFILES`** — `vendor/.env.example` 기본(`VECTOR_STORE`·`DB_TYPE` 연동) 유지 시 `postgresql`+`weaviate` 프로필 활성

프로젝트 루트에서:

```bash
make dify-up
```

브라우저: `http://localhost:8080`

FastAPI `DIFY_API_BASE_URL`은 로컬에서 `http://localhost:8080/v1` 로 두면 됩니다.

### 호스트 Ollama를 Dify에 붙일 때

Podman에서 Dify API가 `host.containers.internal:11434`로 접속하려면, 호스트의 Ollama가 **루프백 전용이 아니라** `0.0.0.0:11434`(또는 LAN)에서 리슨해야 합니다. systemd `ollama` 서비스 기준 절차는 [`infra/ollama/README.md`](../ollama/README.md) — 한 줄: `make ollama-dify-host-bind` (sudo 필요).

### 워크플로 DSL (IDR Tier2)

CRM·BI compact 호출 + LLM 요약 워크플로는 [`workflows/idr_crm_bi_tier2.yml`](workflows/idr_crm_bi_tier2.yml) 로 가져올 수 있습니다. 절차·가져온 뒤 수정 사항: [`workflows/README.md`](workflows/README.md).

### FastAPI JWT (Dify HTTP 노드용)

DB에 등록된 사용자로 로그인해 토큰을 받습니다. 루트 `.env`에 `IDR_LOGIN_USERNAME` / `IDR_LOGIN_PASSWORD`(선택 `IDR_API_BASE_URL`)를 넣은 뒤 환경에 노출하고:

```bash
make dify-fastapi-jwt-bearer
```

`Makefile`은 `.env`를 자동으로 읽지 않으므로, 같은 셸에서 `export IDR_LOGIN_USERNAME=...` 하거나 `set -a && . ./.env && set +a`(`.env` 문법 주의) 후 실행하세요. 스크립트: [`scripts/fetch_fastapi_jwt.py`](scripts/fetch_fastapi_jwt.py).

## 업그레이드 (0.15.x → 1.13.x) 시 주의

- 이전 `docker-compose.dify.yml` 스택의 **이름 있는 볼륨(`dify-pgdata` 등)과 데이터 경로가 다릅니다.**  
  공식 스택은 `vendor/volumes/` 아래 **바인드 마운트**를 씁니다.
- **관리자·앱·워크플로 데이터를 이어 받으려면** Postgres 덤프/복원 등 별도 마이그레이션이 필요합니다.  
  그냥 올리면 **새 설치**로 시작합니다.

## 벤더 동기화 (새 Dify 패치 반영)

`vendor/`는 태그 고정 스냅샷입니다. 새 버전으로 바꿀 때:

```bash
# 예: 1.13.3 출시 시
rm -rf vendor
curl -sSL -o /tmp/dify.tgz https://github.com/langgenius/dify/archive/refs/tags/1.13.3.tar.gz
mkdir -p vendor && tar -xzf /tmp/dify.tgz -C vendor --strip-components=2 dify-1.13.3/docker
```

이후 `docker-compose.idr.yml`과 공식 `docker-compose.yaml`의 서비스명·의존성 차이를 수동 점검합니다.

## ga-server / `X-Forwarded-Proto`

1.13은 `vendor/nginx/` 템플릿을 사용합니다. 상위 리버스 프록시(HTTPS) 뒤에 두는 경우 공식 문서·`nginx` 템플릿의 `X-Forwarded-Proto` 설정을 따르세요.

레거시 단일 `nginx.conf`는 **0.15.x 전용**이었습니다 → `nginx.conf.legacy-dify-0.15` 참고만 하세요.
