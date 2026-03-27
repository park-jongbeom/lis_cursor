# IDR Analytics 강의 데모 UI

단일 HTML(`index.html`)로 FastAPI 백엔드(`http://127.0.0.1:8000`)를 호출합니다. Chart.js·Axios는 CDN을 사용합니다.

## 사전 준비

### 1. 백엔드 `.env`

- `APP_ENV=development`
- `INTERNAL_BYPASS_ENABLED=true`
- `INTERNAL_BYPASS_BEARER_TOKEN=<강의용 비밀 문자열>` — **이 값을 `index.html` 상단 입력란에도 동일하게 입력**하거나, 첫 실행 후 입력란에 저장(localStorage).
- `INTERNAL_BYPASS_USERNAME=admin`(기본) — **DB에 동일한 `username`의 활성 사용자가 있어야** 우회가 동작합니다.

DB에 `admin` 사용자가 없으면(마이그레이션만 한 새 환경) 프로젝트 루트에서:

```bash
cd /path/to/lis_cursor
PYTHONPATH=idr_analytics poetry run python -c "
import asyncio
import uuid

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.user import User


async def main() -> None:
    async with async_session_factory() as db:
        r = await db.execute(select(User).where(User.username == 'admin'))
        if r.scalar_one_or_none() is not None:
            print('admin 사용자가 이미 있습니다.')
            return
        u = User(
            id=uuid.uuid4(),
            username='admin',
            hashed_password=hash_password('강의용-비밀번호'),
            role='admin',
        )
        db.add(u)
        await db.commit()
        print('admin 사용자 생성 완료')


asyncio.run(main())
"
```

위 스크립트의 `hash_password('강의용-비밀번호')`는 실제 비밀번호 문자열로 바꿔도 되고, 우회 토큰만 쓸 때는 로그인에 쓰이지 않습니다.

### 2. CORS

VS Code Live Server(예: `http://localhost:5500`)를 쓰면 `ALLOWED_ORIGINS` JSON 배열에 해당 출처를 넣습니다. `env.example` 참고.

HTML 파일을 **파일 경로로 직접 연 경우**(`file://`) 브라우저는 `Origin: null`을 보냅니다. 이 때는 `ALLOWED_ORIGINS`에 문자열 `"null"`을 포함해야 합니다.

### 3. 인프라·앱 기동(3-step 요약)

1. `make dev-up` — PostgreSQL·Redis(및 필요 시 기타 dev 컨테이너)
2. `alembic upgrade head` 또는 `make migrate` — 스키마 적용
3. `PYTHONPATH=idr_analytics poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` — API 기동  
4. **(SCM·CRM 잡 시연 시)** 별도 터미널에서 ARQ 워커:
   `PYTHONPATH=idr_analytics poetry run arq app.workers.arq_worker.WorkerSettings`  
   (`.env`의 `REDIS_URL`과 동일한 Redis에 연결되어야 합니다.)

### 5. 데모 페이지 열기

- **권장**: VS Code «Live Server»로 `demo/index.html` 서빙(CORS에 5500 등록)
- 또는 `file://` + `ALLOWED_ORIGINS`에 `"null"` 포함
- **API 베이스 URL**: 데모 HTML과 **같은 호스트가 아닙니다.** Live Server(5500)·Dify Studio(8080)에서 페이지를 열어도 요청은 **IDR FastAPI**로 가야 합니다(로컬 기본 `http://127.0.0.1:8000/api/v1`). Dify(:8080)나 Live Server 오리진을 API로 쓰면 로그인 응답이 JSON이 아니라 **HTML(Next.js)** 로 보일 수 있다.
- **404 방지**: 페이지 스크립트가 API 베이스를 **`원본 오리진 + /api/v1`** 으로 고칩니다. `http://127.0.0.1:8000` 만 입력해도 됩니다. 이 전에는 여기에 `/api/v1` 없이 `/auth/login` 만 붙어 **404** 가 자주 났습니다.
- **강의 데모 자동 로그인**: 현재 `demo/index.html`은 데모 편의를 위해 `admin / LiveDemo2026!`를 코드에 고정하고 페이지 진입 시 자동 로그인한다(로컬 강의 전용).
- 샘플 CSV: `demo/sample_data/README.md` (`scm_sample.csv`, `crm_sample.csv`, `bi_sample.csv`)

## 공인 URL (`https://lis.qk54r71z.freeddns.org/`) — **엣지만 ga-server**

**운영 인프라(IDR FastAPI·Postgres·Redis·Dify 등)는 로컬**에서 `docker-compose.prod.yml`·`.env.prod`·호스트 uvicorn 으로 띄운다. [`infra/deploy/local-prod/README.md`](../infra/deploy/local-prod/README.md) 가 단일 원본이다.

공인 도메인으로 브라우저에서 열기만 할 때는, DNS/TLS 가 묶인 **역프록시 한 대(ga-server 의 `ga-nginx`)** 가 있고, 여기서만:

- `/` → 데모 정적(`index.html` 사본),
- `/api/v1/` 등 → **Tailscale(또는 LAN) 너머의 로컬** FastAPI 포트,
- 나머지 → 같은 맥락의 Dify 포트

로 **URL 접근 경로만** 나눈다. API 본체는 ga-server 위 **`idr-fastapi`(Docker)** 나, 순수 로컬이면 로컬 uvicorn 중 하나에 맞춘다.

브라우저 열기: **`make open-lis`** 또는 Cursor 작업 **「LIS 데모 URL 브라우저 열기」**.  
엣지 설정·정적 사본 동기화 참고: [`infra/remote-proxy/`](../infra/remote-proxy/) (`patch_lis_nginx_remote.py`, `ga-server-append-lis.qk54r71z.conf.snippet` — **공인 URL용으로만** 사용).

**정적 데모 HTML 갱신(엣지)**: 로컬에서 `demo/index.html`을 고친 뒤 공인 `/` 에 반영하려면, `ga-nginx`가 마운트하는 호스트 경로로 복사한다. (SSH `Host ga-server` 가 있다는 가정 예시)

```bash
scp demo/index.html ga-server:/home/ubuntu/ga-api-platform/docs/nginx/static/lis-demo/index.html
```

`idr-fastapi`(엣지) DB의 `admin` 비밀번호는 데모 자동 로그인(`LiveDemo2026!`)과 맞출 것.

CORS: 로컬 `.env` / `.env.prod`에 `https://lis.qk54r71z.freeddns.org` 포함(`env.prod.example` 참고).

### 로그인·API 가 안 될 때 (502 / 네트워크 오류)

**공인 `https://lis…/`** 는 ga-nginx 가 **`idr-fastapi:8000`** Docker 스택([`infra/deploy/public-edge/`](../infra/deploy/public-edge/README.md))으로 넘긴다. 502 면 `idr-fastapi`·Postgres·Redis 컨테이너와 `docker exec ga-nginx wget -qO- http://idr-fastapi:8000/health` 를 확인한다.

로컬만(역프록시 없이) 쓸 때는 [`infra/deploy/local-prod/`](../infra/deploy/local-prod/README.md) 의 `make prod-up`·uvicorn.

공개 URL에서 쓰는 **admin 비밀번호**는 배포 시 서버에서만 시드·보관하고, 공개 전후로 반드시 변경할 것(`public-edge` README).

## 로컬 «운영형» 스택 (`APP_ENV=production`)

테스트용 compose(`make test`)·일상 dev(`make dev-up`)와 **별도**인 Postgres/Redis·`.env.prod` 절차는 [`infra/deploy/local-prod/README.md`](../infra/deploy/local-prod/README.md) 를 보라. 한 주소로 데모+API를 쓰려면 같은 디렉터리의 `nginx-local-demo.conf`(기본 `http://127.0.0.1:9080/`)를 참고한다.

## P9-1 환경 점검(강의 직전)

`docs/plans/plan.md` §P9-1 과 동일합니다. Dify·JWT Bearer·워크플로 Publish 상태를 강의 전에 한 번 확인하세요.

## 보안

- 우회 토큰·`index.html`에 입력한 Bearer는 **강의 노트북 한정**입니다.
- 프로덕션에서는 `INTERNAL_BYPASS_ENABLED=false`를 유지하고, 데모 HTML을 배포하지 마세요.
