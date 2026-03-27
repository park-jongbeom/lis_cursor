# `/ide/docs/rules/` — 탭 UI(Cursor · VS Code+Claude Code) 및 Cursor 콘텐츠 정합 계획

> **목적**: 공인 `https://lis…/ide/docs/rules/` 교육용 HTML을 **도구별 탭**으로 나누어, 기존 **Cursor** 안내를 최신 저장소 문서와 맞추고, **VS Code + Claude Code** 수강생을 위한 동등한 진입 경로를 둔다.  
> **관련 정본**: [`lis_public_url_path_map.md`](lis_public_url_path_map.md)(경로·운영 원칙), [`student_rules_download_lis_plan.md`](student_rules_download_lis_plan.md)(ZIP·다운로드), [`demo/ide/docs/rules/index.html`](../../demo/ide/docs/rules/index.html)(구현물)  
> **워크플로**: 실제 구현·테스트 착수 시 [`docs/rules/workflow_gates.md`](../rules/workflow_gates.md) · `docs/CURRENT_WORK_SESSION.md` 절차 준수.

---

## 1. 현재 상태

| 항목 | 내용 |
|------|------|
| **URL** | 동일 호스트 `/ide/docs/rules/` — FastAPI `StaticFiles`로 `demo/ide` 서빙 ([`lis_public_url_path_map.md`](lis_public_url_path_map.md) §2) |
| **페이지** | 단일 스크롤 HTML, 히어로·목차·섹션 구조, Mermaid 2개 |
| **톤** | 히어로·레이어 표·일부 문구가 **Cursor 전용** (예: “Cursor AI”, `.cursorrules` 중심) |
| **ZIP** | `idr-cursor-rules-student.zip` — [`scripts/package_student_rules.sh`](../../scripts/package_student_rules.sh), [`README_교육생.md`](../../demo/ide/student_package_template/README_교육생.md)도 Cursor 전제 |

**갭**: VS Code에서 **Claude Code**(또는 유사 확장/CLI)를 쓰는 수강생은 **경로·개념 매핑**이 다르다. 페이지가 Cursor만 가리키면 “다른 도구 = 규칙 없음”으로 오해될 수 있다.

---

## 2. 목표 UX

1. **탭 2개(최소)**  
   - **Cursor** — 현재 페이지 본문을 이 탭으로 옮기고, 아래 §4 절차로 **정본 문서와 정합** 갱신.  
   - **VS Code + Claude Code** — 동일한 **IDR 규칙 체계(Gate·L4·품질)** 를 설명하되, **파일 위치·용어**를 해당 도구에 맞게 매핑(§5).

2. **공통 영역(탭 위 또는 탭 밖)**  
   - **다운로드(ZIP)·SHA256·404/§0 안내** — 도구 공통이므로 탭 **위**에 두어 한 번만 노출(현재 `#download` 섹션과 동일 취지).  
   - 히어로 제목은 예: “AI 변경 통제 개발 환경 — 규칙 가이드” 유지, 부제에 **두 도구 모두** 언급.

3. **접근성·내비**  
   - 탭은 `role="tablist"` / `role="tab"` / `role="tabpanel"` 및 키보드(화살표·Home/End) 패턴 권장.  
   - 우측 **목차**는 **활성 탭 패널 내부 앵커**만 따라가도록 하거나, 탭 전환 시 “이 탭 목차”로 갱신.  
   - **URL 해시**(선택): `#cursor` / `#vscode-claude` 로 직링크 가능하면 강의 URL 공유에 유리.

4. **Mermaid**  
   - 탭 전환 시 숨겨진 패널에 그려진 다이어그램이 깨지지 않게: **탭 표시 후** `mermaid.run()` 재호출 또는 탭별로 한 번만 초기화하는 패턴을 구현 단계에서 결정.

---

## 3. Cursor 탭 — “정합 갱신” 절차(구현 전 체크리스트)

HTML은 저장소 **원문의 교육용 압축본**이므로, 작업 시 아래를 **순서대로 열어 diff 관점으로 스캔**하고 HTML에 반영한다. (전문 붙여넣기가 아니라 **요약·표·금지 사항** 수준 유지.)

| 순서 | 정본 파일 | Cursor 탭에서 확인할 요지 |
|------|-----------|---------------------------|
| 1 | [`.cursorrules`](../../.cursorrules) | 필독 문서 목록, Dify/compact/async, `endpoints/*.py` `from __future__` 금지, Gate B 직후 멈춤, MCP·§0 한 줄 |
| 2 | [`.cursor/rules/git-commit-korean.mdc`](../../.cursor/rules/git-commit-korean.mdc) | 한국어 Conventional Commits (L2) |
| 3 | [`.cursor/skills/idr-session-workflow/SKILL.md`](../../.cursor/skills/idr-session-workflow/SKILL.md) | Gate A~E 요약, Gate B 직후 멈춤, `CURRENT` 단일 기록 |
| 4 | [`docs/rules/workflow_gates.md`](../rules/workflow_gates.md) | 승인 범위 해석, AI 금지 사항, `docs/plans/` 세션 전용 신설 금지 |
| 5 | [`docs/rules/project_context.md`](../rules/project_context.md) | 디렉터리·Gate·ga-server MCP 범위·`.env*` 정책 |
| 6 | [`docs/rules/backend_architecture.md`](../rules/backend_architecture.md) | 2-Tier, async, Depends/`TYPE_CHECKING`·422 |
| 7 | [`docs/rules/dify_integration.md`](../rules/dify_integration.md) | `compact=true`, 역할 분리, 동기 JSON 권장 |
| 8 | [`docs/rules/error_analysis.md`](../rules/error_analysis.md) | **최근 항목** 위주로 §7 카드 갱신(날짜·유형 반영) |
| 9 | (참고) [`docs/rules/lis_dify_public_troubleshooting.md`](../rules/lis_dify_public_troubleshooting.md) | 공인 디버깅은 본 페이지 **핵심이 아님** — ZIP 404 안내 문구와 중복만 정리 |

**문구 정리 예시**

- `workflow_gates.md` 상단은 “Cursor AI 및 모든 기여자”이므로, HTML 공통 섹션에서는 **“Cursor 및 기타 AI 코딩 에이전트”** 처럼 중립화할지, Cursor 탭에만 “Cursor”를 유지할지 **탭 분리 시** Cursor 탭에만 제품명을 쓰는 편이 일관적이다.
- `production_checklist.md` 등 **운영 전용** 문서는 교육 페이지 **본문에 새 절을 추가하지 않는 것**을 기본으로 하되, `project_context`·`plan.md`에서 이미 링크되는 내용과 **모순이 없게**만 본다.

---

## 4. VS Code + Claude Code 탭 — 콘텐츠 설계

**원칙**: IDR의 **규칙 내용(Gate·문서 계층·백엔드·Dify)** 은 Cursor와 **동일**. 달라지는 것은 **도구별 “계약 파일” 위치와 이름**뿐이다.

| IDR 개념 | Cursor (기존) | VS Code + Claude Code (안내용) |
|----------|---------------|----------------------------------|
| 최상위 계약 | `.cursorrules` | 프로젝트 루트 **`AGENTS.md`** 및/또는 **`.claude` 설정·프로젝트 지침**(Claude Code 문서에 맞는 최신 권장 파일명 사용; 구현 시 공식 문서 1회 확인) |
| 규칙 조각 | `.cursor/rules/*.mdc` | **`.claude/rules/`** 또는 VS Code용 **프로젝트 규칙 파일**(팀 표준 확정 필요) |
| 워크플로 모듈 | `.cursor/skills/.../SKILL.md` | **`.claude/skills/.../SKILL.md`** 또는 Claude Code가 로드하는 skills 경로(사용자/프로젝트 범위 구분 안내) |
| L4 원문 | `docs/rules/*.md` | **동일** — 저장소에 두고 읽음; ZIP에도 동일 포함 가능 |
| L5 | `pyproject.toml`, pre-commit, `.vscode/settings.json` | **동일** — VS Code는 `.vscode/settings.json`이 오히려 일치 |

**탭에 넣을 섹션(제안)**

1. 짧은 개요: “규칙 **내용**은 Cursor 탭과 같고, **적용 위치**만 다르다.”
2. 위 매핑 표 + “강의에서는 팀이 배포한 템플릿 경로를 따른다” 한 줄.
3. Gate A~E·Gate B 멈춤 — **동일 텍스트 재사용**(중복이 길면 Cursor 탭으로 링크 + 한 단락 요약).
4. 백엔드·Dify·체크리스트 — **공통**이면 “두 탭 동일”이므로 **한 탭에만 두고 다른 탭에서는 링크**할지, **양쪽에 짧게 반복**할지 구현 시 선택(유지보수는 단일 `main` 공통 블록 + JS 복제보다, HTML에 `template` 또는 빌드 스텝 없이면 **한쪽 탭에 상세·한쪽은 요약+앵커** 권장).

**주의**: Claude Code 제품의 **정확한 디렉터리 규칙**은 버전에 따라 변할 수 있어, HTML에 **“공식 문서 링크 1줄 + 팀 템플릿 따름”** 을 넣고, 저장소에는 **선택적**으로 `demo/ide/student_package_template/README_VSCode_Claude.md`(가칭)를 두어 ZIP 확장 시 함께 묶을 수 있게 계획한다.

---

## 5. ZIP·패키지 확장(선택 과제)

| 옵션 | 설명 |
|------|------|
| **A. 단일 ZIP** | `README_교육생.md`에 “Cursor / VS Code+Claude Code” 절을 추가하고, Claude용 샘플 `AGENTS.md` 발췌를 `examples/`에 넣는다. |
| **B. ZIP 분리** | `idr-vscode-claude-rules-student.zip` 추가 + `package_student_rules.sh` 인자화 또는 두 타깃 빌드. 다운로드 HTML에 버튼 2개. |
| **C. 문서만** | 당분간 HTML 탭만 추가하고 ZIP은 Cursor 패키지 유지; VS Code 수강생은 HTML 매핑만 따름. |

**권장 순서**: **C → A → B** (강의 피드백 후 패키지 증가).

---

## 6. 구현 WBS(요약)

| ID | 작업 | 산출 |
|----|------|------|
| W1 | 정본 스캔(§3) 및 Cursor 탭 카피·문구 수정 | 갱신된 Cursor 패널 HTML |
| W2 | 탭 UI + a11y + (선택) 해시 라우팅 | `index.html` CSS/JS |
| W3 | VS Code+Claude Code 패널 작성(§4) | 두 번째 `tabpanel` |
| W4 | 목차·스크롤 스파이 로직을 탭과 호환되게 수정 | `.nav` 동작 |
| W5 | Mermaid 탭 호환 | 초기화/재실행 |
| W6 | (선택) README·ZIP·`make package-student-rules` | 스크립트·템플릿 |
| W7 | 문서 링크 정리 | 본 계획서·[`student_rules_download_lis_plan.md`](student_rules_download_lis_plan.md) “UI” 행·[`ppt_aux_instructor_build_guide.md`](ppt_aux_instructor_build_guide.md) 한 줄(강의에서 탭 안내) |

---

## 7. 검증·DoD

- 로컬: `GET /ide/docs/rules/` **200**, 탭 전환·목차·(있으면) `#` 해시 진입.  
- `scripts/verify_lis_public_smoke.py` — 기존 경로 **200** 유지.  
- 공인: [`lis_public_url_path_map.md`](lis_public_url_path_map.md) §0 전제(터널·업스트림)하에 HTML 확인.  
- **DoD**: Cursor 탭이 §3 정본과 **충돌 없이** 읽히고, VS Code+Claude Code 탭에 **최소 매핑 표 + Gate 요약 + L4/L5 안내**가 있다.

---

## 8. 참고(저장소 내부)

- [`demo/ide/docs/rules/index.html`](../../demo/ide/docs/rules/index.html)  
- [`scripts/package_student_rules.sh`](../../scripts/package_student_rules.sh)  
- [`docs/CURRENT_WORK_SESSION.md`](../CURRENT_WORK_SESSION.md) — 공인 `/ide/docs/rules/` 상세 계획·검증 이력  
- [`docs/rules/workflow_gates.md`](../rules/workflow_gates.md) — Gate 단일 원본
