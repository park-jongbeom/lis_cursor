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
- **HEADless 자체 검증(API 동선)**: FastAPI `:8000` 기동 후 리포 루트에서 `PYTHONPATH=idr_analytics poetry run python scripts/verify_demo_user_journey_local.py` — 로그인·`scm_sample.csv` 업로드·프로필·`GET /ide/docs/rules/` 를 순서대로 확인한다. **`APP_ENV=development` 일 때만** dev DB의 `admin` 비밀번호를 위 데모 문자열로 **맞춘다**(기존 `admin` 해시를 덮어씀).
- 샘플 CSV: `demo/sample_data/README.md` (`scm_sample.csv`, `crm_sample.csv`, `bi_sample.csv`)

## 공인 URL (`https://lis.qk54r71z.freeddns.org/`) — **엣지만 ga-server**

**운영 인프라(IDR FastAPI·Postgres·Redis·Dify 등)는 로컬**에서 `docker-compose.prod.yml`·`.env.prod`·호스트 uvicorn 으로 띄운다. [`infra/deploy/local-prod/README.md`](../infra/deploy/local-prod/README.md) 가 단일 원본이다.

공인 도메인으로 브라우저에서 열기만 할 때는, DNS/TLS 가 묶인 **역프록시 한 대(ga-server 의 `ga-nginx`)** 가 있고, 여기서만 **동일 호스트에서 경로만** 나눈다(정본: **`docs/plans/lis_public_url_path_map.md`**).

- **`/`**·**`/index.html`** → **같은 FastAPI** 업스트림이 `demo/index.html` 서빙(`StaticFiles`, `idr_analytics/app/main.py`),
- **`/api/v1/`**, **`/health`**, **`/docs`**, **`/ide/`** → 위와 **동일** FastAPI(교육용 규칙·ZIP은 `demo/ide` 마운트),
- **`/apps`** 등 그 외 → **Dify**

데모 페이지 **제목 바로 아래**와 하단에 **`/ide/docs/rules/`** 교육생 가이드 링크가 있다. ZIP 갱신 후 배포하려면 `make package-student-rules` → 공인/엣지에 동기화된 `demo/ide` 포함 여부 확인(정본 §6 체크리스트).

브라우저 열기: **`make open-lis`** 또는 Cursor 작업 **「LIS 데모 URL 브라우저 열기」**.  
공인 URL이 §0(터널·로컬 uvicorn)로 떠 있을 때 HTTP 동선 자동 점검: **`make verify-lis-public`** (`scripts/verify_lis_public_smoke.py`). Tier2 에이전트까지 보려면 Dify가 강의 PC에서 도달 가능하게 잡힌 뒤 `python3 scripts/verify_lis_public_smoke.py --with-agent`.

엣지 nginx·프록시 참고: [`infra/remote-proxy/`](../infra/remote-proxy/) (`patch_lis_nginx_remote.py`, `patch_lis_root_to_fastapi_proxy.py`, `ga-server-append-lis.qk54r71z.conf.snippet` — **공인 URL용으로만** 사용).

**데모 HTML 갱신(공인)**: 로컬 리포의 `demo/index.html`을 고친 뒤, **§0** 기준으로 그 코드가 돌아가는 **uvicorn 프로세스**를 재기동하거나(또는 패턴 A 시 `idr-fastapi` 이미지·볼륨에 반영) 하면 된다. **엣지에 `scp` 로 `lis-demo` 디렉터리만 갱신하는 방식은 사용하지 않는다** — 루트는 nginx 정적이 아니라 FastAPI 프록시다. 기존 ga-server에 남아 있는 `location = / { root ... lis-demo; }` 블록은 `infra/remote-proxy/patch_lis_root_to_fastapi_proxy.py` 로 FastAPI 프록시로 치환한다.

`idr-fastapi`(엣지) DB의 `admin` 비밀번호는 데모 자동 로그인(`LiveDemo2026!`)과 맞출 것.

CORS: 로컬 `.env` / `.env.prod`에 `https://lis.qk54r71z.freeddns.org` 포함(`env.prod.example` 참고).

### 로그인·API 가 안 될 때 (502 / 네트워크 오류)

**공인 `https://lis…/`** 의 API·`/ide/` 업스트림은 [`docs/plans/lis_public_url_path_map.md`](../docs/plans/lis_public_url_path_map.md) **§0** — **운영 표준은 오직 로컬 우회(터널)** 이다. ga-nginx Docker 는 호스트 게이트웨이 + 터널 포트(게이트웨이는 `docker exec ga-nginx ip route show default` 로 실측; 예: **172.18.0.1**)로 **동일 업스트림**을 쓴다. **패턴 A**(`idr-fastapi:8000`)는 문서상 예외·합의 시에만. 502 면 터널·로컬 uvicorn 가동 여부를 먼저 본다.

**Dify AI 요약(Tier2)**: 브라우저는 공인 `lis`만 보지만, **Dify API 호출은 uvicorn 프로세스가 실행 중인 PC**에서 나간다. `.env`의 `DIFY_API_BASE_URL`은 **그 PC에서** `curl`로 응답이 오는 주소여야 한다. `http://localhost:8080/v1`은 **같은 머신에** `make dify-up`(등)으로 Dify가 떠 있을 때만 맞고, Dify가 원격(전용 서버·Tailscale만)이면 예: `http://100.x.x.x:8080/v1`처럼 **그 PC에서 도달 가능한 URL**로 바꾼다. 주소가 틀리면 Dify 콘솔에는 실행 로그가 거의 안 남고, API는 `DIFY_REQUEST_ERROR` 등 502로 떨어질 수 있다. 워크플로 입력에 `period`가 필수인 경우, 데이터에서 월을 못 추리면 API가 **UTC 기준 당월 `YYYY-MM`** 을 넣어 보낸다.

로컬만(역프록시 없이) 쓸 때는 [`infra/deploy/local-prod/`](../infra/deploy/local-prod/README.md) 의 `make prod-up`·uvicorn.

공개 URL에서 쓰는 **admin 비밀번호**는 배포 시 서버에서만 시드·보관하고, 공개 전후로 반드시 변경할 것(`public-edge` README).

## 로컬 «운영형» 스택 (`APP_ENV=production`)

테스트용 compose(`make test`)·일상 dev(`make dev-up`)와 **별도**인 Postgres/Redis·`.env.prod` 절차는 [`infra/deploy/local-prod/README.md`](../infra/deploy/local-prod/README.md) 를 보라. 한 주소로 데모+API를 쓰려면 같은 디렉터리의 `nginx-local-demo.conf`(기본 `http://127.0.0.1:9080/`)를 참고한다.

## P9-1 환경 점검(강의 직전)

`docs/plans/plan.md` §P9-1 과 동일합니다. Dify·JWT Bearer·워크플로 Publish 상태를 강의 전에 한 번 확인하세요.

## 보안

- 우회 토큰·`index.html`에 입력한 Bearer는 **강의 노트북 한정**입니다.
- 프로덕션에서는 `INTERNAL_BYPASS_ENABLED=false`를 유지하고, 데모 HTML을 배포하지 마세요.
