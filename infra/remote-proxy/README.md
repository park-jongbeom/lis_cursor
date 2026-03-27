# infra/remote-proxy

**역할**: 공인 도메인(예: `https://lis.qk54r71z.freeddns.org/`)으로 들어오는 **HTTP(S) 엣지** 설정만. TLS 종료·`/` vs `/api` vs **`/ide/`** vs Dify 경로 분배.

**운영 표준(필독)**: 공인 `lis.*` 의 IDR **FastAPI** 업스트림은 **`docs/plans/lis_public_url_path_map.md` §0** — **오직 로컬 우회(터널 등)**. `idr-fastapi` 컨테이너를 공인 기본 업스트림으로 두는 설명·스크립트 기본값은 **예외(합의 시)** 로만 취급한다.

**경로 의미(정본)**: 동일 호스트에서 **`/` = 데모**, **`/apps` = Dify**, **`/ide/…` = 교육용 규칙·다운로드(FastAPI `demo/ide`)** — 상세는 **`docs/plans/lis_public_url_path_map.md`**.

## 단일 FastAPI `proxy_pass` (§0·§2.1)

- **`/api/v1/` · `/health` · `/docs` · `/openapi.json` · `/ide/`** 는 **같은 업스트림**(로컬 터널 끝점). **경로마다 다른 업스트림 금지.**
- ga-nginx가 **Docker**이면 `127.0.0.1:8000` 은 컨테이너 자신 — **호스트 게이트웨이**로 터널 포트에 연결한다. 게이트웨이는 네트워크마다 다름: `docker exec ga-nginx ip route show default` 의 `via` (예: docker0 **172.17.0.1**, compose 브리지 **172.18.0.1** — 현재 ga-server는 후자).
- **Dify**는 별도 URL — `ga-server-append-lis.qk54r71z.conf.snippet`·`patch_lis_nginx_remote.py` 참고.

## Cursor MCP (`user-ga-server-ssh`) — **ga-nginx(Docker)만**

팀에서 고정한 범위: ga-server에 SSH MCP로 붙을 때는 **엣지용 nginx가 Docker 컨테이너(예: `ga-nginx`)로 떠 있는 그 안의 설정**을 **읽고**, 사용자가 **명시적으로** nginx 설정 변경을 요청한 경우에만 **그 conf** 를 다룬다.

- **하지 않음**: `idr-fastapi`·DB·Redis·Dify 등 **다른 컨테이너** 조작, 호스트에 정적 파일·compose·이미지 빌드로 404 처리.
- **404가 JSON `{"detail":"Not Found"}`**: 엣지 `location /ide/`·`proxy_pass` 가 맞는지 **ga-nginx conf로만** 확인한 뒤, 남으면 **§0** 기준 **로컬** uvicorn·`demo/ide`·터널. (패턴 A 예외일 때만 컨테이너 쪽 `demo/ide`·이미지.)
- 규정 원본: `docs/rules/project_context.md`, `docs/rules/error_analysis.md`(2026-03-28 MCP 재발 항목), `.cursor/skills/idr-session-workflow/SKILL.md`.

**하지 않는 것**: IDR Postgres·Redis·FastAPI·Dify 컨테이너를 이 서버에 올리는 «백엔드 배포». 그 부분은 [`../deploy/local-prod/README.md`](../deploy/local-prod/README.md) 의 **로컬 운영형** 스택이 담당한다.

**`/ide/docs/rules`**: 교육용 정적 페이지는 **로컬에서 뜬 FastAPI**의 `StaticFiles` mount 로 서빙한다. ga-server(역프록시)에는 `/api/v1/` 과 **같은** `proxy_pass` 대상으로 `location /ide/` 만 추가하면 된다(`ga-server-append-lis.qk54r71z.conf.snippet`, `ga-server-location-ide.snippet.conf` 참고).

**`{"detail":"Not Found"}` 가 나올 때(§0 기준)**: (1) nginx `proxy_pass` · (2) **로컬** uvicorn·`demo/ide`·터널. **공인 운영 표준에서 먼저 `idr-fastapi` 이미지 재빌드를 제시하지 않는다** (예외 합의 시만).

**설정 반영 확인**: 호스트에서 `go-almond.swagger.conf` 등을 고친 뒤에도 공인 동작이 옛내용이면, **`md5sum` 호스트 파일**과 **`docker exec ga-nginx md5sum /etc/nginx/conf.d/default.conf`** 를 비교한다. 다르면 `docker restart ga-nginx` 후 재확인(`docs/rules/error_analysis.md` 2026-03-28 항목).

ga-nginx 등과 연동할 때만 이 디렉터리를 본다. 로컬 단독이면 `local-prod/nginx-local-demo.conf`(9080)로 충분하다.
