# 워크플로 심층 점검 — 보완 반영 로그

> 워크플로·계획서·아키텍처 문서에 대한 심층 점검 결과(10건)를 코드/문서에 반영한 요약이다.  
> 상세 논지는 내부 계획서(워크플로 심층 점검)를 참조한다.

## 반영 파일

| 주제 | 조치 |
|------|------|
| Gate A~E vs 구 3단계 불일치 | [`workflow_gates.md`](workflow_gates.md) 전면 개정, [`project_context.md`](project_context.md) 표 추가, [`.cursorrules`](../../.cursorrules) 요약 갱신 |
| CRUD가 Phase 5에만 있어 Phase 4 서비스가 막힘 | [`plan.md`](../plans/plan.md) **Phase 4-0** CRUD 추가, Phase 5에서 CRUD 중복 항목 제거, [`CURRENT_WORK_SESSION.md`](../CURRENT_WORK_SESSION.md) 4-0 체크리스트 |
| CPU-bound 동기 라이브러리 vs async | [`backend_architecture.md`](backend_architecture.md) §1 `run_in_executor` 패턴 |
| ARQ 폴링·결과 저장 미정의 | [`plan.md`](../plans/plan.md) Phase 5 상단 **ARQ 잡 결과·폴링 전략** 절 |
| `plan.md` 체크박스 미갱신 | Phase 0~3 `[x]`, 상단 **진행 현황** 표, Gate E에 `plan.md` 동기화 명시 |
| 에러 JSON 표준 미정의 | [`backend_architecture.md`](backend_architecture.md) §4 HTTP/API 에러 응답 절, 부록 A 행 추가 |
| `columns_json` ↔ `DatasetProfileResponse` | [`plan.md`](../plans/plan.md) §4-1 권장 JSON 구조, CURRENT ingestion 항목 |
| `conftest` Phase 7 vs Phase 2 중복 | [`plan.md`](../plans/plan.md) §7-1 `[x]` 및 경고 문구 |
| 포트 5432 vs 15432 | [`plan.md`](../plans/plan.md) 부록 B, 다이어그램 주석, [`backend_architecture.md`](backend_architecture.md) §6 예시 |
| `AgentQueryRequest` ↔ `RoutingRequest` | [`plan.md`](../plans/plan.md) Phase 5 `agent.py` 어댑터 문구 |

## 후속 권장

- Phase 5 구현 시 `HTTPException`/`exception_handler`를 위 에러 절과 실제 응답 샘플로 맞출 것.
- Gate E마다 `plan.md` 상단 표와 해당 Phase 체크박스를 함께 갱신할 것.

## 2026-03 보완 — 운영자 의도 워크플로 반영

Gate 정의를 다음 순서로 재정렬함: **구현 상세 계획(CURRENT)·승인 → 구현·완료 요약·승인 → 테스트 상세 계획·승인 → 검증 → WORK_HISTORY + `plan.md` + 다음 CURRENT**. (`workflow_gates.md`, `project_context.md`, `.cursorrules`, `CURRENT_WORK_SESSION.md` 템플릿)
