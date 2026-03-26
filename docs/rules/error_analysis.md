# AI 오류 분석 기록 — IDR 시스템 데이터 분석 AI 백엔드

> **목적**: AI가 잘못 판단하여 오류를 유발한 사례를 기록하고, 동일한 실수가 반복되지 않도록 재발 방지 규칙을 명시한다.
> **사용법**: 세션 시작 시 이 문서를 읽어라. AI 오판이 확인되면 즉시 아래 형식으로 추가한다.

---

## 기록 형식

```
## [YYYY-MM-DD] <오류 제목>

**오류 유형**: (타입 에러 / 로직 오류 / 설계 오판 / 환경 설정 오류 / 기타)
**발생 상황**: 어떤 작업을 하다가 발생했는가
**근본 원인**: 왜 AI가 잘못 판단했는가
**재발 방지 규칙**: 다음 번에 이 상황에서 반드시 해야 할 것 / 하지 말아야 할 것
**관련 파일**: 해당 오류와 연관된 파일 경로
```

---

## 기록된 오류

### [2026-03-26] 구현 직후 세션 문서 전환 및 테스트 게이트 생략

**오류 유형**: 프로세스 위반 / 워크플로 누락 (기타)

**발생 상황**: Session 01(Phase 0~1 스캐폴딩) 코드 구현이 끝난 뒤, `docs/CURRENT_WORK_SESSION.md`를 사용자 검토·테스트 계획·테스트 검증 없이 곧바로 Session 02(Phase 2) 내용으로 교체하고 `WORK_HISTORY.md`만 갱신함.

**근본 원인**: `.cursorrules`와 `project_context.md`에 "계획 → 승인 → 구현 → 승인 → 테스트" 원칙은 있었으나, **구현 완료를 `CURRENT_WORK_SESSION.md`에 남기는 단계**와 **사용자 확인 후 테스트 계획·실행**을 문서·게이트로 강제하는 규정이 없어 AI가 한 턴에 마감 처리함.

**재발 방지 규칙**:
1. 구현 종료 직후 **`CURRENT_WORK_SESSION.md`에 「구현 완료 요약」**을 쓰고 상태를 **사용자 확인 대기**로 둔다. 사용자 명시 승인 전에는 테스트 계획으로 넘어가지 않는다.
2. 테스트는 **계획을 문서에 기록**한 뒤 승인받고, 실행 결과를 **「테스트 검증 결과」**에 남긴다.
3. 위 순서는 **`docs/rules/workflow_gates.md`** 및 갱신된 `.cursorrules` / `project_context.md` 작업 프로토콜(Gate A~E)을 따른다.

**관련 파일**: `docs/rules/workflow_gates.md`, `.cursorrules`, `docs/rules/project_context.md`, `docs/CURRENT_WORK_SESSION.md`

---

### [2026-03-26] "작업 계획 작성" 요청 시 Cursor CreatePlan 도구 오용

**오류 유형**: 프로세스 위반 / 도구 오용 (기타)

**발생 상황**: 사용자가 플랜 모드에서 "다음 작업 계획을 작성해라"고 했을 때, `docs/CURRENT_WORK_SESSION.md`에 상세 구현 계획을 기록하지 않고 Cursor의 CreatePlan 도구를 사용해 별도 `.plan.md` 파일을 생성함.

**근본 원인**: "작업 계획"이라는 말을 Cursor 플랜 모드의 내장 CreatePlan 기능으로 해석함. 이 프로젝트에서는 `CURRENT_WORK_SESSION.md`가 유일한 작업 계획 기록 장소임을 인식하지 못하고 범용 도구를 사용함.

**재발 방지 규칙**:
1. 플랜 모드에서 "작업 계획 작성" 또는 유사한 요청이 오면 → **`docs/CURRENT_WORK_SESSION.md`** 의 해당 섹션(구현 체크리스트, 완료 기준, 상세 스펙)을 채운다.
2. Cursor CreatePlan 도구(`CreatePlan`)는 이 프로젝트에서 **사용하지 않는다**.
3. 작업 계획의 기록 위치: `CURRENT_WORK_SESSION.md` (상세 스펙) → `WORK_HISTORY.md` (완료 이력).

**관련 파일**: `docs/CURRENT_WORK_SESSION.md`, `docs/rules/workflow_gates.md`, `.cursorrules`

---

### [2026-03-26] pre-commit: 테스트 한 줄 초과(E501) 및 BIService `prev` 삼항 연산 mypy 오류

**오류 유형**: 정적 분석 / 품질 게이트 (ruff E501, mypy `operator`)

**발생 상황**: Git 커밋 시 `pre-commit`이 `ruff`, `ruff-format`, `mypy`에서 실패. `test_crud_base.py`·`test_scm_service.py`에서 한 줄이 120자 초과(E501). `bi_service.py`의 `regional_trend`에서 `growth = ... if prev is None ... else (cur - prev) / prev` 형태로 인해 mypy가 `else` 가지에서도 `prev`에 `None` 가능성을 남겨 `float`와 `None` 간 `-`, `/` 연산 오류를 냄.

**근본 원인**: (1) 테스트에서 `create(..., {"key": ...})` 호출을 한 줄에 나열. (2) 삼항 연산자만으로는 일부 mypy 설정에서 `prev`의 좁히기(narrowing)가 불충분함. (3) unstaged 파일이 있을 때 pre-commit이 stash 후 훅이 파일을 고치면 롤백되어 사용자가 “고쳤는데도 실패”처럼 보일 수 있음.

**재발 방지 규칙**:
1. **ruff line-length 120**: 긴 함수 호출·dict 리터럴은 여러 줄로 나누거나 `poetry run ruff format`으로 맞춘 뒤 커밋한다. 커밋 전 `poetry run ruff check idr_analytics`로 확인.
2. **mypy + Optional 누적 변수**: `prev`처럼 `None`으로 시작해 루프에서 갱신하는 값은 `prev: float | None = None`으로 표기하고, `yoy_comparison`과 같이 **`if prev is None or prev == 0: ... else: (cur - prev) / prev`** 형태의 명시 분기를 쓴다. 성장률 계산은 삼항 한 줄에 `None` 가능 변수와 산술을 섞지 않는다.
3. **pre-commit stash 충돌**: 커밋 전에 스테이징과 맞추려면 `git add -A` 후 커밋하거나, unstaged 변경을 정리해 훅 자동 수정과 stash 복원이 충돌하지 않게 한다.

**관련 파일**: `idr_analytics/tests/unit/test_crud_base.py`, `idr_analytics/tests/unit/test_scm_service.py`, `idr_analytics/app/services/analytics/bi_service.py`, `.pre-commit-config.yaml`

---

### [2026-03-26] (재발) 동일 Git 로그(E501·bi_service 33행 mypy) — stash 롤백·미스테이징

**오류 유형**: 정적 분석 / pre-commit 동작 (환경·워크플로)

**발생 상황**: 이전에 기록한 것과 **동일한** `vscode.git.Git` 로그가 다시 나옴: `test_crud_base.py:78`·`test_scm_service.py:78`이 **한 줄짜리** 긴 코드로 보이고, `bi_service.py:33`에서 삼항 연산 기반 `(cur - prev) / prev` mypy 오류. 그러나 저장소의 올바른 수정본은 이미 **여러 줄 dict / DataFrame**, `bi_service`는 **`prev: float | None` + if/else** 형태이다.

**근본 원인**: (1) 커밋 시 **Unstaged files detected** → pre-commit이 unstaged를 stash한 뒤 훅이 스테이징된 스냅샷만 고침. (2) **Stashed changes conflicted with hook auto-fixes... Rolling back fixes** → 훅이 적용한 ruff-format·ruff --fix 결과가 **폐기**되고, 워킹 트리는 긴 줄·구버전 코드로 남음. (3) 수정이 **커밋/스테이징에 포함되지 않은** 채 IDE만 갱신된 것으로 착각하기 쉬움.

**재발 방지 규칙** (커밋 전 **순서 고정**):
1. 터미널에서 `make format && make lint && make typecheck` (또는 동일하게 `poetry run ruff format idr_analytics/`, `ruff check`, `mypy idr_analytics/app`)를 실행해 **로컬에서 먼저** 통과시킨다.
2. 그다음 **`git add -u`** 또는 **`git add -A`** 로 이번 변경 파일을 **전부 스테이징**한다. 일부만 stage하고 나머지를 unstaged로 둔 채 커밋하지 않는다.
3. 로그에 **한 줄짜리** `create(db, {"name": ...})`가 보이면 워킹 트리가 구버전이거나 롤백된 것이므로, 1~2를 반드시 다시 수행한다.
4. `bi_service.regional_trend`에는 **삼항 연산으로 `(cur - prev) / prev`를 쓰지 않는다** (mypy `operator` 재발 방지).

**관련 파일**: `Makefile` (`format` 타깃), `idr_analytics/tests/unit/test_crud_base.py`, `idr_analytics/tests/unit/test_scm_service.py`, `idr_analytics/app/services/analytics/bi_service.py`, `.pre-commit-config.yaml`

---

> 이후 AI 오판이 발생하면 위 형식으로 이어서 추가하세요.
