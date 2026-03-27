# 공인 URL `lis.*` — 단일 호스트·경로 역할 정본

> **목적**: `https://lis.qk54r71z.freeddns.org` 처럼 **하나의 호스트**로 브라우저를 열었을 때, **`/` · `/apps` · `/ide/…`** 가 각각 무엇을 보여 주어야 하는지 **한곳에서 고정**한다.  
> **이 문서가 틀리면**: 강의 안내·교육생 URL·엣지 nginx 스니펫·MCP 범위 설명을 **이 파일 기준으로 재정렬**한다.

---

## 0. 팀 운영 원칙 (고정 — 동일 오류 반복 방지)

**공인 `https://lis…` 로 들어오는 IDR FastAPI 트래픽** — 즉 **`/api/v1/` · `/health` · `/docs` · `/openapi.json` · `/ide/`** — 의 업스트림은 **오직 로컬 우회(§2.1 패턴 B)** 만을 운영 표준으로 한다.

| 고정 | 설명 |
|------|------|
| **표준** | SSH `-R`(또는 동등)·Tailscale 등으로 **운영 PC에서 띄운 uvicorn**이 응답한다. ga-server의 **엣지 nginx만** `proxy_pass` 로 그 끝점(호스트 게이트웨이·사설 IP 등)을 본다. |
| **`demo/ide`·ZIP** | **로컬 리포**에만 두고 갱신한다. 공인 `/ide` 404의 **1차 원인**은 터널·로컬 기동·nginx 업스트림 불일치다. |
| **비표준(예외)** | **`http://idr-fastapi:8000`** 등 **ga-server Docker API 컨테이너**를 공인 URL의 기본 업스트림으로 두는 것은 **팀 운영 표준이 아니다.** DR·오프라인 데모 등 **별도 합의·문서**가 있을 때만 예외로 둔다. |

**AI·자동화·문서 작성 시 금지**: 운영 표준을 말할 때 **`idr-fastapi` 이미지 재빌드·compose로 `demo/ide` 마운트·ga-server `lis_cursor`에 정적 심기**를 **먼저·기본 해결책**으로 제시하는 것. (MCP는 원칙적으로 **ga-nginx conf** 만.)

이 원칙과 충돌하는 스니펫·스크립트 기본값이 있으면 **§2.1·`infra/remote-proxy/*`** 를 이 §0에 맞출 것.

---

## 1. 방향이 맞는가? (한 줄)

**맞다.** 운영 의도는 다음과 같다.

- **`https://lis…/`** → IDR Analytics **강의 데모 UI** (브라우저 기본 진입).
- **`https://lis…/apps`** (및 Dify 콘솔·앱 경로) → **Dify** (Self-hosted Studio/앱).
- **`https://lis…/ide/docs/rules/`** (및 **`/ide/downloads/*.zip`**) → **교육생용 규칙 요약 HTML + ZIP 다운로드**.

즉 **서브도메인을 나누어 “규칙만 다른 사이트”를 두는 설계가 아니라**, **동일 호스트에서 경로(prefix)만 나눈다.**

---

## 2. 경로 → 업스트림 (엣지 nginx 관점)

리포의 예시 스니펫은 **`infra/remote-proxy/ga-server-append-lis.qk54r71z.conf.snippet`** 와 동일한 뜻을 가진다. 실제 `DEV_IP`·포트·`LIS_DEMO_ROOT` 는 배포 환경에 맞게 바뀔 수 있다.

| 브라우저 경로(접두) | 사용자에게 보이는 것 | 일반적인 업스트림 | 비고 |
|---------------------|----------------------|-------------------|------|
| **`GET /`** (정확히 루트) | 데모 `index.html` | **nginx `root`** (`LIS_DEMO_ROOT` 등) — 리포 `demo/` 동기화본 | FastAPI가 아닐 수 있음(스니펫 기준). |
| **`GET /api/v1/`** | JSON API | **FastAPI** `:8000` | |
| **`GET /health`**, **`/docs`**, **`/openapi.json`** | 헬스·Swagger·스펙 | **FastAPI** `:8000` | |
| **`GET /ide/`** (하위 전체) | 규칙 HTML·ZIP 등 | **FastAPI** `:8000` 의 `app.mount("/ide", StaticFiles(demo/ide))` | **`/api/v1/` 과 같은 프로세스**로 프록시하는 것이 정상. |
| **`GET /apps`**, **`/console`**, 그 외 `/` 아래 (루트 제외) | Dify UI | **Dify** (예: `:8080`) | `location /` 캐치올이 담당. **`location /ide/` 는 반드시 이 블록보다 위**에 둔다. |

**헷갈리기 쉬운 점**: 디스크 상으로는 `demo/index.html`(데모)과 `demo/ide/…`(규칙)이 **형제 디렉터리**이지만, **공인 URL에서는** 루트 `/`는 **정적 nginx**, `/ide/`는 **FastAPI 마운트**로 갈 수 있다. “데모만 배포했다 = `/ide`도 된다”가 **자동으로 성립하지 않는다.**

### 2.1 업스트림 FastAPI — 패턴 B(운영 표준) vs 패턴 A(예외·참고)

브라우저는 항상 **`https://lis…`** 만 본다. 차이는 **엣지 nginx가 `/api/v1/`·`/health`·`/docs`·`/openapi.json`·`/ide/` 를 어디로 `proxy_pass` 하느냐**뿐이다.

| 패턴 | 운영에서의 위치 | `proxy_pass` 대상(개념) | `demo/ide` |
|------|-----------------|---------------------------|------------|
| **B. 로컬 우회** | **§0 표준** | 로컬 uvicorn 이 ga-server에서 **닿는 주소**(터널·Tailscale 등; ga-nginx Docker 시 **호스트 게이트웨이**로 호스트의 터널 포트) | **로컬 리포** |
| **A. ga-server Docker API** | **예외 시만**(별도 합의) | `http://idr-fastapi:8000/…` | 컨테이너·이미지·볼륨 |

**「프록시 우회로 로컬을 바라보게」** = **패턴 B** = **§0 고정**. 패턴 B일 때 **ga-server에 API 이미지 재빌드·`demo/ide` 를 서버에 두는 것은 운영 표준 조치가 아니다.** 대신:

- **`/api/v1/` 과 `/ide/` 가 같은 upstream** 을 가리켜야 한다(한쪽만 `idr-fastapi`·한쪽만 로컬이면 안 됨).
- 로컬 PC에서 uvicorn 이 **켜져 있고**, 터널/네트워크가 **끊기지 않아야** 공인 `/ide` 가 살아 있다.

**반복되는 실수(§0 위반)**: 문서·스크립트에 패턴 A/B가 **동등하게** 적혀 있거나 **`idr-fastapi` 가 기본값**이면, AI·담당자가 **공인 운영 = ga-server 컨테이너**로 오해한다. 실제 표준은 **전 경로 동일 터널 끝점**이다. `/ide/` 만 **`idr-fastapi:8000`** 인 채로 두면 404·혼선이 난다.

---

## 3. `/ide/docs/rules/` 가 안 뜰 때 (올바른 수순)

1. **엣지(ga-nginx)**: `location /ide/` 존재 여부, `proxy_pass …/ide/`(끝 슬래시·접두 유지), Dify용 `location /` 보다 **위**인지 — **MCP 허용 범위는 여기까지(설정 읽기·명시 시 conf 수정)**. **§0 표준(패턴 B)** 이면 모든 FastAPI `proxy_pass` 가 **동일 터널 끝점**인지 확인한다.
2. **업스트림(§0 기준)**:
   - **먼저**: 로컬 리포 `demo/ide`·uvicorn·터널 가동.
   - **예외(패턴 A 합의 시에만)**: 컨테이너·이미지·볼륨.
3. 응답이 JSON `{"detail":"Not Found"}` 이면 **거의 항상 FastAPI**가 낸 것이다(프록시가 Dify로 잘못 보냈다면 Dify 쪽 HTML/다른 형태가 나올 수 있음).

---

## 4. 잘못된 방향(문서·작업에서 제거할 전제)

| 잘못된 전제 | 왜 틀리는가 |
|-------------|-------------|
| “`/ide`는 별도 도메인·별도 제품 배포가 원칙이다” | **아니다.** 단일 호스트·경로 분리가 원칙이다. |
| “루트 데모가 공인에 떴으니 `/ide`도 같은 방식으로 이미 해결됐다” | 루트는 **nginx 정적**, `/ide`는 **FastAPI**일 수 있어 **별도 조건**이 필요하다. |
| “nginx에 HTML 하나 더 두면 `/ide` 완료” | 규칙 페이지·ZIP·링크 일관성은 **`demo/ide` + FastAPI 마운트**가 정본이다. 엣지에 수동 미러는 재현성·버전 관리에 불리하다. |
| “MCP로 `idr-fastapi`에 파일 넣어 `/ide` 고친다” | **금지.** MCP는 **ga-nginx conf** 범위만. |
| “공인 404 → ga-server에서 `idr-fastapi` 이미지·compose·`demo/ide` 부터 손본다” | **§0 비표준.** 표준은 **로컬 우회 끝점·로컬 `demo/ide`·nginx `proxy_pass` 일치**다. |
| “문서에 A/B 나란히만 쓰고 운영 표준을 §0에 고정하지 않는다” | AI가 **패턴 A를 기본**으로 오해한다 → **§0 필독**. |

---

## 5. 참고 링크

- **단계별 실행 체크리스트(MCP·§0·터널)**: `docs/CURRENT_WORK_SESSION.md` — 「공인 `lis.*` — `/ide/docs/rules/` 교육생 AI 세팅 가이드 노출 (상세 계획)」
- 엣지 스니펫: `infra/remote-proxy/ga-server-location-ide.snippet.conf`, `ga-server-append-lis.qk54r71z.conf.snippet`
- MCP·분기: `docs/rules/project_context.md` §ga-server·공인 URL
- 스택·볼륨: `infra/deploy/public-edge/README.md`, `docker-compose.idr-stack.yml`
- 교육생 ZIP·랜딩: `docs/plans/student_rules_download_lis_plan.md`, `demo/ide/docs/rules/index.html`
- 강의 동선: `docs/plans/ppt_aux_instructor_build_guide.md`

---

## 6. 재구축·배포 체크리스트(리포 → 공인까지)

아래를 **위에서 아래 순서**로 맞추면 §2 표와 동일 동작이 재현된다.

| 단계 | 할 일 | 산출물·검증 |
|------|--------|-------------|
| 1 | 리포에서 교육생 ZIP 갱신(로컬) | `make package-student-rules` → `demo/ide/downloads/*.zip` |
| 2 (**§0 표준**) | 로컬 우회 일관 | 로컬 `demo/ide` + uvicorn; ga-nginx가 **모든 FastAPI 경로**를 **동일 터널 끝점**으로 `proxy_pass` |
| (예외) 패턴 A | 별도 합의 시에만 ga-server API 컨테이너 | 이미지·`demo/ide` 볼륨 등 — **§0 기본 절차 아님** |
| 3 | 로컬 한 포트 검증 | `uvicorn` 8010 + 선택 `nginx-local-demo.conf` 9080 → `curl -f …/ide/docs/rules/` · ZIP URL (`make prod-smoke-ide`) |
| 4 | ga-nginx `lis` 블록 | `location = /ide` → 301 `/ide/` , `location /ide/` → **API와 동일** `proxy_pass …/ide/` , **Dify용 `location /` 보다 위** |
| 5 | 루트 데모 정적 | `location = /` → `demo/index.html` (스니펫의 `LIS_DEMO_ROOT` 등) — `/ide` 와 혼동 금지 |
| 6 | 공인 스모크 | 브라우저: `/` 데모 · `/apps` Dify · `/ide/docs/rules/` HTML · ZIP 저장 |

원격 `lis` 블록 일괄 교체 예시는 `infra/remote-proxy/patch_lis_nginx_remote.py` 이다. **팀 운영(§0)** 에 맞게 `FASTAPI_UPSTREAM` 은 **호스트의 터널 포트**에 닿는 주소 — 보통 `docker exec ga-nginx ip route show default` 의 게이트웨이(예: docker0 **172.17.0.1**, `ga-api-platform` 등 사용자 브리지 **172.18.0.1**)에 `:8000`. **패턴 A 예외** 시에만 `http://idr-fastapi:8000` 로 바꾼 뒤 실행.
