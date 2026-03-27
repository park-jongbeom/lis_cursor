# infra/remote-proxy

**역할**: 공인 도메인(예: `https://lis.qk54r71z.freeddns.org/`)으로 들어오는 **HTTP(S) 엣지** 설정만. TLS 종료·`/` vs `/api` vs Dify 경로 분배.

**하지 않는 것**: IDR Postgres·Redis·FastAPI·Dify 컨테이너를 이 서버에 올리는 «백엔드 배포». 그 부분은 [`../deploy/local-prod/README.md`](../deploy/local-prod/README.md) 의 **로컬 운영형** 스택이 담당한다.

ga-nginx 등과 연동할 때만 이 디렉터리를 본다. 로컬 단독이면 `local-prod/nginx-local-demo.conf`(9080)로 충분하다.
