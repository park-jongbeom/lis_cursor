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

> 이후 AI 오판이 발생하면 위 형식으로 이어서 추가하세요.
