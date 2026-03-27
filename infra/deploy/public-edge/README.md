# 공개 URL 엣지용 IDR 스택 (ga-server Docker)

**공인 `lis.*` 운영 표준**: FastAPI 업스트림은 **`docs/plans/lis_public_url_path_map.md` §0** — **오직 로컬 우회(터널)**. ga-server 에 `idr-fastapi` 컨테이너를 두는 본 compose 는 **DB·워커·(선택) 예외 업스트림** 용이며, **공인 트래픽의 기본 대상으로 삼는다고 문서에 적지 않는다.**

**단일 호스트 경로 정본**: `https://lis…/` 데모·`/apps` Dify·`/ide/…` — 같은 파일 §1·§2. 엣지 nginx 의 `proxy_pass` 는 **§0에 맞는 단일 주소**(로컬 터널 끝점 등)로 `/api`·`/ide` 를 **같이** 넘긴다.

**참고(패턴 A 예외)**: 같은 Docker 네트워크에서 `idr-fastapi:8000` 으로 넘기는 구성은 **합의된 예외**일 때만 해당한다.

## 절차

1. **가정**: `ga-nginx` 가 이미 `ga-api-platform` compose 로 띄워져 있고, 네트워크 이름이 `ga-api-platform_ga-network` 이다.
2. 리포 루트에서 `cp infra/deploy/public-edge/env.idr.example .env.idr` 후 `SECRET_KEY`·`POSTGRES_PASSWORD`·`ALLOWED_ORIGINS`·Dify URL 등 수정.
3. **기동** (리포 루트 `lis_cursor`) — 호스트에 `docker-compose` 바이너리 기준:
   ```bash
   docker-compose -p idr-edge -f infra/deploy/public-edge/docker-compose.idr-stack.yml --env-file .env.idr up -d --build
   ```
   (`docker compose` v2 플러그인 환경이면 동일 인자로 치환.)
   이 스택에는 `idr-fastapi` 외에 ARQ 잡 소비용 `idr-arq-worker`가 포함되어야 하며, 없으면 SCM/CRM 폴링이 `pending`에 고착된다.
4. **마이그레이션**:
   ```bash
   docker exec idr-fastapi alembic -c alembic/alembic.ini upgrade head
   ```
   (이미지에 `PYTHONPATH=/app` 가 없으면 `docker exec -e PYTHONPATH=/app idr-fastapi alembic ...` — 현재 `Dockerfile` 에 반영됨.)
5. **admin 사용자** (최초 1회):
   ```bash
   docker exec idr-fastapi python -c "
   import asyncio, uuid
   from sqlalchemy import select
   from app.core.security import hash_password
   from app.db.session import async_session_factory
   from app.models.user import User
   async def main():
       async with async_session_factory() as db:
           r = await db.execute(select(User).where(User.username == 'admin'))
           if r.scalar_one_or_none():
               print('admin already exists'); return
           db.add(User(id=uuid.uuid4(), username='admin', hashed_password=hash_password('YOUR_PASSWORD'), role='admin'))
           await db.commit()
           print('ok')
   asyncio.run(main())
   "
   ```
6. **nginx(공인 `lis.*`)**: 팀 표준(§0)은 **호스트 터널 끝점**이다. `ga-nginx` 컨테이너에서 `ip route show default` 로 **게이트웨이 IP**를 확인한 뒤, `lis` 블록의 `/api/v1/`·`/health`·`/docs`·`/openapi.json`·`/ide/` 가 **모두** `http://<게이트웨이>:8000/…` (또는 터널 포트에 맞게)로 **동일**한지 맞춘다. `docker exec ga-nginx nginx -t && docker exec ga-nginx nginx -s reload`. (`infra/remote-proxy/patch_lis_nginx_remote.py` — 예외 시에만 `idr-fastapi:8000`)
7. **워커 확인**:
   ```bash
   docker ps --format '{{.Names}}' | grep -E 'idr-fastapi|idr-arq-worker|idr-edge-redis'
   docker logs --tail=50 idr-arq-worker
   ```
   `idr-arq-worker`가 없거나 오류로 반복 재시작하면, 데모 UI의 SCM/CRM "예측 실행→폴링/클러스터→폴링"은 완료되지 않는다.

로그인: 데모 페이지에서 사용자 **`admin`**, 비밀번호는 시드 스크립트에 넣은 값(배포 담당자만 보관). **공개 전·강의 후 반드시 변경**한다.

## Dify

`location /` 나머지는 기존처럼 Tailscale 등 Dify 호스트로 둘 수 있다. `DIFY_API_BASE_URL` 은 컨테이너에서 도달 가능한 주소여야 한다.

## `/ide/…` 가 `{"detail":"Not Found"}` 일 때 (§0 기준)

1. **ga-nginx**: `location /ide/` + `proxy_pass …/ide/` 가 **`/api/v1/` 과 동일 업스트림**인지, Dify용 `location /` 보다 **위**인지 확인한다.
2. **운영 표준(§0)**: 업스트림은 **로컬**에서 띄운 uvicorn + 리포 `demo/ide` + SSH `-R`(또는 동등) 터널. JSON 404면 **로컬 프로세스**에 `curl http://127.0.0.1:8000/ide/docs/rules/` 등으로 먼저 재현한다.
3. **패턴 A 예외**(합의로 nginx가 `idr-fastapi:8000` 을 볼 때만): 그때는 컨테이너 안 `/app/demo/ide`·이미지·마운트를 본다.

```bash
# 예외(패턴 A) 합의 시에만 — 컨테이너 쪽 정적 확인
docker exec idr-fastapi ls -la /app/demo/ide/docs/rules
docker exec idr-fastapi ls -la /app/demo/ide/downloads
```

`docker-compose.idr-stack.yml` 의 `demo/ide` 마운트·`idr-fastapi` 재기동은 **서버 측 API 스택** 절차이지, **§0 공인 URL의 기본 운영 절차가 아니다.**
