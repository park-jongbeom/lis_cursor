# 교육생 규칙 패키지 — 공인 URL(`lis.*`) 배포·다운로드·적용 계획

> **작성 목적**: 공인 URL 배포의 목표를 **강사 화면 시연**이 아니라, **교육생이 직접 URL로 진입해 교육용 규칙 묶음을 내려받고 자신의 Cursor/저장소에 적용**할 수 있게 하는 것으로 정의한다.  
> **관련**: `demo/ide/docs/rules/index.html`(요약 뷰), `docs/rules/*`(원문), `infra/remote-proxy/*`·`infra/deploy/public-edge/*`(엣지·스택), `docs/plans/ppt_aux_instructor_build_guide.md`(강의 동선)  
> **공인 URL 전제(필독)**: `https://lis…/` 데모·`/apps` Dify·`/ide/…` 규칙 가이드는 **동일 호스트·경로 분리**다. **FastAPI(`/ide` 포함) 운영 표준은 해당 문서 §0 — 오직 로컬 우회.** 정본 전체는 **`docs/plans/lis_public_url_path_map.md`**.

---

## 1. 목표·성공 기준

| 구분 | 내용 |
|------|------|
| **교육생 관점** | 브라우저에서 `https://lis.qk54r71z.freeddns.org/ide/...` 로 진입 → **규칙 패키지(파일 묶음) 다운로드** → 압축 해제 후 README 절차대로 **자신의 프로젝트/홈에 복사**해 Cursor 규칙·문서를 켤 수 있다. |
| **강사·운영 관점** | 강의 회차마다 **동일 URL 체계**로 안내 가능하고, 버전(날짜·태그)을 패키지에 명시해 **재현 가능**하다. |
| **성공 기준** | (1) 다운로드 링크가 공인 URL에서 **인증 없이** 또는 정책에 맞는 범위에서 동작한다. (2) 패키지 내 `README_교육생.md`(가칭)만 따라도 최소 적용이 완료된다. (3) 엣지 nginx는 **`ga-nginx` conf 범위**만 담당하고, **파일 내용은 FastAPI 정적 또는 별도 호스팅**으로 제공한다(MCP 범위는 `project_context.md` 참고). |

---

## 2. 현재 상태와 갭

| 항목 | 리포·구현 | 남는 갭(운영) |
|------|-----------|----------------|
| URL 방향 | **`/ide/…`는 데모(`/`)·Dify(`/apps`)와 별도 제품이 아니라 동일 호스트에서 FastAPI로 프록시** — `lis_public_url_path_map.md` | 엣지에 `location /ide/` 누락·순서 오류 시 공인에서만 실패 |
| 진입·다운로드 | `/ide/docs/rules/` HTML + `make package-student-rules` → `/ide/downloads/*.zip` | 공인에서 200 확인·강의 회차마다 ZIP 재배포 |
| 콘텐츠 | 패키지 스크립트·`README_교육생.md`·랜딩 CTA | 강사 합의로 패키지 파일 목록 조정 시 스크립트 갱신 |
| 공인 응답 | 코드·이미지에 `demo/ide` 포함 가능 | 업스트림에 **`demo/ide` 실물 없음**이면 JSON 404 — 볼륨·이미지·동기화 |
| 법·보안 | 템플릿만 포함·실비밀 제외 원칙 | 패키지 재생성 시 수동 스캔 |

---

## 3. 교육생 사용자 여정(목표 UX)

1. 강사가 공유한 링크로 접속: 예) `https://lis.qk54r71z.freeddns.org/ide/` 또는 랜딩 페이지.
2. **「교육생용 규칙 패키지 다운로드」** 버튼 또는 직접 링크: 예) `/ide/downloads/idr-cursor-rules-student.zip` (경로는 구현 시 확정).
3. ZIP 저장 → 압축 해제.
4. 패키지 루트의 **설치 README**에 따라:
   - `.cursor/rules/` 에 복사할 파일 목록
   - 선택: `.cursorrules` **발췌본** 또는 팀용 축약본
   - **금지**: 실제 API 키·`.env` 샘플에 비밀 값 금지(템플릿만)
5. Cursor 재시작 또는 규칙 새로고침 후, 강의 실습 저장소에서 동작 확인.

---

## 4. 패키지(산출물) 구성안

**원칙**: 전체 `lis_cursor`를 주지 않고, **교육에 필요한 최소 규칙 레이어**만 포함한다. (용량·보안·혼동 방지)

| 포함 후보 | 설명 | 비고 |
|-----------|------|------|
| `README_교육생.md` | 복사 경로, Cursor 버전 가정, 강의 당일 체크리스트 | 필수 |
| `.cursor/rules/*.mdc` **교육용 부분집합** | 예: `git-commit-korean.mdc`, 세션 워크플로 요약본 | 원문 전체 vs 강의 축약본 결정 필요 |
| `.cursor/skills/.../SKILL.md` **요약 또는 링크** | 전문은 URL로 안내, 로컬에는 1~2페이지 요약 | 용량 조절 |
| `docs/rules/` **선택 MD** | `workflow_gates.md` 발췌, `project_context.md` 발췌 등 | 버전·날짜 헤더 |
| `index.html` (동일 콘텐츠 링크) | 브라우저로 읽기 + ZIP 하단에 동일 안내 | 선택 |

**제외(기본)**:

- `.env`, `infra/dify` 실비밀, `ref_files/` 내부 전용 문서
- 팀 고유 SDD 전문(필요 시 링크만)

**버전 표기**: ZIP 내부 `VERSION.txt` 또는 README 상단에 `규칙 패키지 rYYYYMMDD` 형태.

---

## 5. URL·서빙 설계

| 방식 | 장점 | 단점 |
|------|------|------|
| **A. `StaticFiles` 하위에 zip 정적 배치** | 구현 단순, CDN 없이 동작 | ZIP 갱신 시 **이미지/볼륨 재배포** 필요 |
| **B. FastAPI `FileResponse` 전용 라우트** | 다운로드 헤더·로깅·향후 인증 확장 용이 | 코드 변경·테스트 필요 |
| **C. 객체 스토리지 + 리다이렉트** | 대용량·트래픽 분리 | 인프라 추가 |

**1차 권장**: **A 또는 B** — 교육 규모에서 A로 시작해, 다운로드 수·통제 요구가 생기면 B로 이전.

**경로 예시**(확정 전):

- 랜딩: `/ide/` 또는 `/ide/docs/rules/` (기존 HTML에 다운로드 섹션 추가)
- 아카이브: `/ide/downloads/idr-cursor-rules-student.zip`

---

## 6. 구현 작업 분해(WBS)

1. **콘텐츠**: 교육용 파일 부분집합 확정 + `README_교육생.md` 초안 작성.
2. **빌드**: 리포에 `scripts/package_student_rules.sh`(가칭) 또는 `make package-student-rules` 로 ZIP 생성(생성물은 `demo/ide/downloads/` 등에 두어 StaticFiles로 서빙).
3. **UI**: `index.html`에 다운로드 링크·SHA256(선택)·버전 문구 추가.
4. **앱**: `main.py` 마운트 루트에 `downloads/` 포함 여부 확인; 필요 시 B안 라우트 추가.
5. **배포**: `Dockerfile` `COPY demo/ide/`에 downloads 포함, **public-edge compose** 호스트 동기화·볼륨 정책과 정합(`infra/deploy/public-edge/README.md`).
6. **검증**: 공인 URL에서 GET zip **200**, 브라우저 저장, 압축 해제 구조 검사.
7. **문서**: 본 계획서 갱신 + `ppt_aux_instructor_build_guide.md`에 「다운로드 목적」 한 단락 링크.

**워크플로**: 실제 구현 시 `docs/rules/workflow_gates.md` · `CURRENT_WORK_SESSION.md` 절차 준수.

---

## 7. 배포·운영 체크리스트(담당자)

- [ ] 엣지 `ga-nginx`: `/ide/` 가 FastAPI 업스트림과 일치하는지(설정만 MCP 허용 범위).
- [ ] 업스트림: `/app/demo/ide` 에 `index.html` + `downloads/*.zip` 존재.
- [ ] 강의 전: 공인 URL로 ZIP 다운로드 **실측**.
- [ ] 강의 후: 패키지 버전 갱신 시 ZIP 재생성·재배포 반복.

---

## 8. 리스크·완화

| 리스크 | 완화 |
|--------|------|
| 공개 ZIP에 민감 문자열 유입 | 패키지 스크립트에서 grep/검증 또는 수동 리뷰 체크리스트 |
| 교육생 OS·Cursor 버전 차이 | README에 「지원 버전」·문제 시 강사 문의 |
| URL만으로는 적용 실패 | README에 스크린샷 또는 `tree` 예시 |
| 404 재발 | 업스트림 이미지·볼륨을 규칙과 함께 **한 세트**로 문서화 |

---

## 9. 다음 액션(요약)

**리포 구현 상태(참고)**

1. 산출물: `README_교육생.md`(템플릿), `.cursor/rules`·스킬·`cursorrules.example`, `docs/rules/` 5종 — `scripts/package_student_rules.sh`가 묶음.  
2. 빌드: `make package-student-rules` → `demo/ide/downloads/idr-cursor-rules-student.zip` + `.sha256`.  
3. UI: `demo/ide/docs/rules/index.html` §다운로드 CTA.  
4. **공인 E2E**·강의 채널 URL 고정 — 배포 담당자 검증(업스트림에 `demo/ide` 포함).

---

## 10. 참고 링크(저장소 내부)

- `docs/plans/lis_public_url_path_map.md` — 공인 `lis.*` 에서 `/`·`/apps`·`/ide/` 정본
- `scripts/package_student_rules.sh` · `make package-student-rules`
- `demo/ide/downloads/` (ZIP·SHA256)
- `demo/ide/docs/rules/index.html`
- `docs/rules/project_context.md` (ga-server MCP 범위)
- `infra/remote-proxy/README.md`
- `infra/deploy/public-edge/README.md`
- `docs/plans/ppt_aux_instructor_build_guide.md`
