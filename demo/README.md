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

## P9-1 환경 점검(강의 직전)

`docs/plans/plan.md` §P9-1 과 동일합니다. Dify·JWT Bearer·워크플로 Publish 상태를 강의 전에 한 번 확인하세요.

## 보안

- 우회 토큰·`index.html`에 입력한 Bearer는 **강의 노트북 한정**입니다.
- 프로덕션에서는 `INTERNAL_BYPASS_ENABLED=false`를 유지하고, 데모 HTML을 배포하지 마세요.
