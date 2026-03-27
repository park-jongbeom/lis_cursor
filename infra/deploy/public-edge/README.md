# 공개 URL 엣지용 IDR 스택 (ga-server Docker)

`lis` 도메인의 nginx 는 **같은 Docker 네트워크** `ga-api-platform_ga-network` 안의 컨테이너 `idr-fastapi:8000` 으로 `/api/v1`·`/health` 등을 넘길 수 있다. (Tailscale 에만 떠 있는 로컬 uvicorn 은 꺼지면 502)

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
6. **nginx**: `lis` 서버 블록의 FastAPI `proxy_pass` 를 `http://idr-fastapi:8000` 으로 맞춘 뒤 `docker exec ga-nginx nginx -t && docker exec ga-nginx nginx -s reload`. (`infra/remote-proxy/patch_lis_nginx_remote.py` 참고)
7. **워커 확인**:
   ```bash
   docker ps --format '{{.Names}}' | grep -E 'idr-fastapi|idr-arq-worker|idr-edge-redis'
   docker logs --tail=50 idr-arq-worker
   ```
   `idr-arq-worker`가 없거나 오류로 반복 재시작하면, 데모 UI의 SCM/CRM "예측 실행→폴링/클러스터→폴링"은 완료되지 않는다.

로그인: 데모 페이지에서 사용자 **`admin`**, 비밀번호는 시드 스크립트에 넣은 값(배포 담당자만 보관). **공개 전·강의 후 반드시 변경**한다.

## Dify

`location /` 나머지는 기존처럼 Tailscale 등 Dify 호스트로 둘 수 있다. `DIFY_API_BASE_URL` 은 컨테이너에서 도달 가능한 주소여야 한다.
