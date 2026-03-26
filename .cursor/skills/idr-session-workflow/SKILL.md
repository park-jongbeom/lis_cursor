---
name: idr-session-workflow
description: >-
  Enforces the IDR lis_cursor session workflow (Gate A–E), mandatory document
  read order, and CURRENT/plan.md hygiene. Use at session start, before coding or
  running tests, when editing docs/CURRENT_WORK_SESSION.md, docs/plans/plan.md,
  or docs/rules in this repository.
---

# IDR 세션 워크플로 (에이전트용 요약)

**전체 규정(단일 원본)**: `docs/rules/workflow_gates.md` — 상충 시 그 문서가 우선한다.

## 세션 시작 시 읽기 순서

1. `docs/plans/plan.md` — Phase·WBS 위치
2. `docs/CURRENT_WORK_SESSION.md` — 현재 Gate, 구현/테스트 계획
3. `docs/rules/error_analysis.md` — 알려진 AI 오판
4. 구현·리뷰 시: `docs/rules/project_context.md`, `docs/rules/backend_architecture.md`, `ref_files/IDR_Data_Analysis_SDD.md` (필요 범위)

## Gate A ~ E (한 줄)

| Gate | 할 일 | 승인 전 금지 |
|------|--------|----------------|
| **A** | `CURRENT`에 구현 상세 계획 | 코드 변경 |
| **B** | 구현 후 구현 완료 요약·`[x]` | Gate C/D 테스트 착수 |
| **C** | `CURRENT`에 테스트 계획(상세) | 테스트 작성·실행 |
| **D** | 실행·검증 결과 기록 | (실패 시 재실행 후 기록) |
| **E** | `WORK_HISTORY.md`, `plan.md` 갱신, `CURRENT` 다음 세션용 교체 | E 생략 |

## AI 금지 (요약)

- A 승인 없이 구현 시작.
- B 승인 없이 테스트 계획(C) 또는 실행(D).
- C 승인 없이 테스트 코드·실행.
- D 기록 없이 이력만 갱신하거나 `CURRENT`를 다음 세션으로 통째 교체.
- E에서 `plan.md` 체크·진행 표 누락.

## `CURRENT_WORK_SESSION.md` 권장 섹션 순서

메타·워크플로 표 → 구현 상세 계획(A) → 구현 완료 요약(B) → 테스트 계획(C) → 검증 결과(D). 상세 템플릿은 `workflow_gates.md` §표준 섹션.

## 품질·커밋 (pre-commit 충돌 방지)

- 커밋 전: `make format && make lint && make typecheck` 통과 후 변경분 **전부** `git add` (unstaged 남기지 않기 — stash 롤백으로 훅 수정이 폐기될 수 있음).
- 상세: `docs/rules/error_analysis.md` (pre-commit·E501·mypy 재발 항목).

## 코드·아키텍처 힌트 (자주 씀)

- Dify는 수치 계산 안 함 — FastAPI/Pandas에서 계산.
- `endpoints/*.py`에 `from __future__ import annotations` 금지 (422 이슈).
- 분석 API에 `compact=true` 지원.
- 엔드포인트·서비스 메서드는 async 일관성.

## 관련 경로

- 이력: `docs/history/WORK_HISTORY.md`
- Git 커밋 한국어: `.cursor/rules/git-commit-korean.mdc`, `.vscode/settings.json` (Copilot 보조)
