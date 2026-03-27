# 현재 작업 세션 — Session 20

> **초점**: Phase 9 **잔여** — 강의 리허설·Dify·`DEMO_SCRIPT`·공인 Tier2(`DIFY_*`) 등 (Session 19에서 **`/ide/docs/rules/`** 탭·회귀·Gate E 완료)
> **전체 계획**: [`docs/plans/plan.md`](plans/plan.md) §Phase 9
> **워크플로**: [`docs/rules/workflow_gates.md`](rules/workflow_gates.md)

> **직전 세션(Session 19)**: [`docs/history/WORK_HISTORY.md`](history/WORK_HISTORY.md) 「Session 19 — `/ide/docs/rules/` 탭 UI…」. Session 18 이전 대용량 `CURRENT` 본문은 **Git 이력**의 이전 커밋을 참고.

---

## 진행 상태

**현재 단계**: **Gate A 대기** — 아래 「Phase 9 잔여」에서 범위를 정한 뒤, **`CURRENT`에 구현·검증 상세 계획**을 쓰고 **사용자 승인** 후에만 코드·테스트 착수.

---

## 세션 워크플로 상태 (Session 20)

| 게이트 | 완료 | 비고 |
|--------|:----:|------|
| A. 구현 상세 계획 | ⬜ | 승인 전 코드 변경 금지 |
| B. 구현 완료 | ⬜ | |
| C. 테스트 상세 계획 | ⬜ | |
| D. 테스트 검증 | ⬜ | |
| E. 이력·plan·CURRENT | ⬜ | |

---

## 직전 완료 요약 (Session 19 — 참고만)

| 항목 | 내용 |
|------|------|
| **구현** | `demo/ide/docs/rules/index.html` — Cursor / VS Code+Claude Code **탭**, 해시 `#cursor`·`#vscode-claude`, Mermaid 지연 렌더 |
| **검증** | `make test` **156 passed**; `TestClient` `GET /ide/docs/rules/` **200**; 공인 `verify_lis_public_smoke.py` **OK**(환경 전제) |
| **문서** | `plan.md` Session 19·Phase 9 표; `WORK_HISTORY` 항목 |

---

## Phase 9 잔여 — 작업 후보 (`plan.md`와 동일 취지)

> **다음 태스크를 시작할 때** 본 절 또는 사용자 지시를 바탕으로 **Gate A**에 범위·파일·DoD를 구체화한다.

| 구분 | 내용 |
|------|------|
| **P9-1** | Dify Studio **Publish**·Bearer·샘플 사전 업로드·LLM 1회 리허설 — [`plan.md`](plans/plan.md) §P9-1 |
| **데모** | `demo/index.html` 브라우저 동선 C-1.2~·차트·ARQ — [`demo/DEMO_SCRIPT.md`](../demo/DEMO_SCRIPT.md)·[`demo/README.md`](../demo/README.md) |
| **스크립트** | `DEMO_SCRIPT.md` 체크리스트 강의 전 `- [x]` 반영 |
| **Tier2·공인** | `verify_lis_public_smoke.py --with-agent`·`DIFY_*`·`verify_dify_upstream.py` — Session 18 기록과 동일 분기 |
| **교육 URL** | 공인 **`/ide/docs/rules/`** 탭·ZIP — [`lis_public_url_path_map.md`](plans/lis_public_url_path_map.md) §0·터널 |

---

## 참고 링크

| 문서 | 용도 |
|------|------|
| [`plans/ppt_aux_instructor_build_guide.md`](plans/ppt_aux_instructor_build_guide.md) | 강의 동선·다운로드 안내 |
| [`plans/student_rules_download_lis_plan.md`](plans/student_rules_download_lis_plan.md) | 교육생 ZIP |
| [`plans/ide_docs_rules_tabs_cursor_vscode_claude_plan.md`](plans/ide_docs_rules_tabs_cursor_vscode_claude_plan.md) | 탭 UI 배경 WBS |

---

**개정**: 2026-03-28 — Session 19 **Gate E** 완료, Session 20 본문으로 전환.
