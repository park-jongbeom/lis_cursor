# Google Slides Apps Script 작성 가이드 (내용 자동 입력용)

> 목적: 디자인은 수동으로 처리하고, **슬라이드의 내용(제목/불릿/발표노트)** 만 Google Apps Script로 자동 입력한다.
>
> 작성 근거(실제 프로젝트 문서):
> - `docs/plans/plan.md`
> - `docs/CURRENT_WORK_SESSION.md`
> - `docs/rules/project_context.md`
> - `docs/rules/workflow_gates.md`
> - `docs/rules/error_analysis.md`
> - `demo/DEMO_SCRIPT.md`
> - `demo/README.md`
> - `ref_files/컨설팅계획서_김희원_IDR시스템즈_전문가_양식.md`

---

## 1) 사용 방식

- Google 프레젠테이션에서 `확장 프로그램 > Apps Script`를 열어 아래 코드를 붙여넣는다.
- 먼저 `프레젠테이션`이 비어있는지(슬라이드가 0장에 가까운지) 확인한다.
- Apps Script에서 **전체 생성 함수 `createDeck()`만 실행**한다.
  - 이 함수는 `DECK` 배열에 정의된 순서대로 **전 슬라이드를 일괄 추가**한다.
- 만약 이미 슬라이드가 있다면, 자동 생성은 “추가” 방식이라 중복될 수 있으니
  - 빈 템플릿에서 시작하거나
  - 필요 시 수동으로 초기 슬라이드를 지운 뒤 실행한다.

---

## 2) Apps Script 코드

```javascript
/**
 * IDR 3/28 발표용 슬라이드 내용 자동 생성 스크립트
 * - 디자인/테마는 건드리지 않음
 * - 제목/불릿/발표자 노트만 입력
 */

const DECK = [
  // ===== AI 먼저 (도입) =====
  {
    id: "A01",
    track: "AI_INTRO",
    title: "AI 개발 운영체계가 필요한 이유",
    bullets: [
      "AI 산출물은 속도를 올리지만 아키텍처/타입/성능/보안까지 자동 만족하진 못함",
      "그래서 문서(계약) + Gate(상태 머신) + 테스트(증적)를 결합",
      "변경 영향 범위를 줄이고 리뷰/운영 부담을 감소",
      "결론: AI 활용이 아니라 AI를 통제 가능한 공정으로 만드는 것이 핵심",
    ],
    notes:
      "이 프로젝트는 AI를 많이 쓰는 사례가 아니라, AI 변경이 안전하게 반영되도록 공정을 설계한 사례로 소개한다.",
  },
  {
    id: "A02",
    track: "AI_INTRO",
    title: "규칙 계층 구조",
    bullets: [
      "레벨1: 전역 작업 규칙(.cursorrules) = 세션/승인 문화",
      "레벨2: 도메인 아키텍처 규칙(docs/rules/*) = 레이어/async/compact/dify 포맷 계약",
      "레벨3: 품질·운영 규칙(.gitignore/커밋·보안) = 실수 재발 방지",
    ],
    notes:
      "규칙을 계층화해서 전략-구현-운영 책임을 분리해야 AI 변경도 예측 가능해진다고 설명한다.",
  },
  {
    id: "A03",
    track: "AI_INTRO",
    title: "세션 시작 문서 참조 루틴",
    bullets: [
      "plan.md: Phase/WBS 위치(무엇을 언제 끝낼지 계약) 확인",
      "CURRENT_WORK_SESSION.md: Gate/승인 범위 고정(상태 머신 입력)",
      "error_analysis.md: 과거 실패 모드 재확인",
      "종료: WORK_HISTORY로 증적 이전(E2E 품질)",
    ],
    notes:
      "시작/종료가 문서화되어 결정이 재현 가능해지고 핸드오프 품질이 올라간다고 강조한다.",
  },
  {
    id: "A04",
    track: "AI_INTRO",
    title: "Gate A~E 승인 경계",
    bullets: [
      "A 승인: 설계/착수까지만(구현 시작만 허용)",
      "B: 구현 완료 후 강제 중지(사용자 검토 창)",
      "C: 테스트 계획 승인 후 실행(실행 권한 분리)",
      "D/E: 검증 결과 기록 후 다음 세션 계약 전환",
    ],
    notes:
      "승인 범위 과대해석을 상태 머신으로 차단해서 사고를 줄인다고 설명한다.",
  },
  {
    id: "A05",
    track: "AI_INTRO",
    title: "스킬 적용 방식",
    bullets: [
      "프로젝트 스킬: idr-session-workflow = 프로세스 오케스트레이터",
      "구현 전/중/후 체크로 레이어 침범/계약 위반 방지",
      "코드 생성보다 절차 준수와 문서 정합성에 집중",
      "결과: AI-assisted 개발에서도 CI 수준 재현성 확보",
    ],
    notes:
      "스킬은 코드 생성기가 아니라 변경의 생산 공정을 표준화하는 장치라고 설명한다.",
  },

  // ===== 샘플 중심 (본론) =====
  {
    id: "S01",
    track: "SAMPLE_CORE",
    title: "IDR Analytics 3/28 데모 실습",
    bullets: [
      "4주차 오전(이론 연결) + 5~6주차 오후(실습/코드)",
      "보조강사 파트: 데이터분석 시연 중심",
      "공인 URL 기준: https://lis.qk54r71z.freeddns.org/",
    ],
    notes:
      "강사님 흐름(이론→분석→점심→코드 샘플→종범 자료)과 정확히 맞춰 진행한다고 소개한다.",
  },
  {
    id: "S02",
    track: "SAMPLE_CORE",
    title: "오늘 목표",
    bullets: [
      "SCM: 수요예측",
      "CRM: 이탈/클러스터",
      "BI: 지역/시기 트렌드",
      "화면 → API → LLM 요약 연결 이해",
    ],
    notes:
      "결과 자체보다 결과가 만들어지는 데이터 흐름을 보여주는 것이 핵심 목표라고 말한다.",
  },
  {
    id: "S03",
    track: "SAMPLE_CORE",
    title: "2-Tier 아키텍처",
    bullets: [
      "Tier1: FastAPI + Pandas (수치 계산)",
      "Tier2: Dify + LLM (해석/요약)",
      "복잡도 기준으로 라우팅",
    ],
    notes: "숫자는 백엔드, 설명은 LLM이라는 역할 분리를 반복 강조한다.",
  },
  {
    id: "S04",
    track: "SAMPLE_CORE",
    title: "기술 스택과 알고리즘",
    bullets: [
      "FastAPI, Pandas, PostgreSQL, Redis/ARQ, Dify",
      "SCM: Prophet/ARIMA",
      "CRM: RFM/K-Means",
      "BI: GroupBy/Pivot/YoY",
    ],
    notes:
      "점심 후 코드 샘플 설명에서 알고리즘 키워드를 다시 연결하겠다고 예고한다.",
  },
  {
    id: "S05",
    track: "SAMPLE_CORE",
    title: "문서 주도 개발 + Gate 운영",
    bullets: [
      "plan / CURRENT / rules 문서로 개발 기준 고정",
      "Gate A~E로 구현/검증 타이밍 분리",
      "AI 코딩 결과도 문서-테스트로 통제",
    ],
    notes:
      "강사 이론의 개발 프로세스가 실제 프로젝트에서 어떻게 구현되는지 보여주는 장이다.",
  },
  {
    id: "S06",
    track: "SAMPLE_CORE",
    title: "Swagger/API 구조 확인",
    bullets: [
      "Swagger: https://lis.qk54r71z.freeddns.org/docs",
      "OpenAPI: https://lis.qk54r71z.freeddns.org/openapi.json",
      "SCM/CRM/BI/Agent 엔드포인트 구조 확인",
    ],
    notes: "공인 URL 환경에서도 API 구조를 실제로 확인 가능하다는 점을 짚는다.",
  },
  {
    id: "S07",
    track: "SAMPLE_CORE",
    title: "compact=true 설계 이유",
    bullets: [
      "LLM 컨텍스트 절약",
      "핵심 지표만 전달해 응답 품질 개선",
      "Dify HTTP Request 노드 파싱 안정성 확보",
    ],
    notes:
      "Dify 연동에서 길고 복잡한 원본 대신 compact 응답을 쓰는 이유를 설명한다.",
  },
  {
    id: "S08",
    track: "SAMPLE_CORE",
    title: "데모 전체 동선",
    bullets: [
      "데모 접속",
      "CSV 업로드 + dataset_id 확인",
      "SCM/CRM/BI 탭 분석 실행",
      "Dify AI 요약으로 해석 연결",
    ],
    notes:
      "청중 대기시간을 줄이기 위해 사전 업로드/리허설 체크를 한다는 운영 포인트를 말한다.",
  },
  {
    id: "S09",
    track: "SAMPLE_CORE",
    title: "SCM 수요예측",
    bullets: [
      "입력: SCM 샘플 CSV",
      "출력: 예측 라인 차트",
      "활용: 재고/수요 타이밍 의사결정",
    ],
    notes: "Prophet 중심, 필요 시 ARIMA fallback이 동작한다는 점을 짧게 언급한다.",
  },
  {
    id: "S10",
    track: "SAMPLE_CORE",
    title: "CRM 이탈/클러스터",
    bullets: [
      "이탈 위험 Top-N",
      "요약 텍스트 + 세그먼트 관점",
      "RFM + K-Means 기반 분석",
    ],
    notes: "영업 우선순위 설정으로 바로 연결되는 실무 가치를 강조한다.",
  },
  {
    id: "S11",
    track: "SAMPLE_CORE",
    title: "BI 지역/시기 트렌드",
    bullets: [
      "지역×기간 히트맵",
      "YoY 비교",
      "GroupBy/Pivot 집계 기반",
    ],
    notes: "지역/시기별 질환 트렌드 기반의 기획 인사이트로 이어진다고 설명한다.",
  },
  {
    id: "S12",
    track: "SAMPLE_CORE",
    title: "Dify 워크플로 구조",
    bullets: [
      "Start → HTTP(CRM/BI) → Aggregator → LLM → Answer",
      "Dify는 계산이 아니라 오케스트레이션 담당",
      "FastAPI 결과를 한국어 인사이트로 변환",
    ],
    notes: "Dify와 FastAPI의 역할 분리를 다시 확인하는 장이다.",
  },
  {
    id: "S13",
    track: "SAMPLE_CORE",
    title: "코드 샘플 브릿지",
    bullets: [
      "Endpoint → Service → compact response → Dify 연동",
      "핵심 라인 중심 설명",
      "구현 세부 전체보다 흐름 우선",
    ],
    notes: "점심 후 코드 샘플 설명으로 자연스럽게 전환하는 브릿지 장이다.",
  },
  {
    id: "S14",
    track: "SAMPLE_CORE",
    title: "Tier1 vs Tier2 재정리",
    bullets: [
      "Tier1: 계산/성능",
      "Tier2: 해석/요약",
      "역할 분리가 운영 안정성의 핵심",
    ],
    notes: "운영/확장 관점에서 분리 아키텍처의 장점을 정리한다.",
  },
  {
    id: "S15",
    track: "SAMPLE_CORE",
    title: "리허설 체크리스트",
    bullets: [
      "공인 URL 접속 확인",
      "/docs 또는 /openapi.json 확인",
      "SCM/CRM/BI 최소 1경로 성공",
      "Tier2 요약 1회 확인",
    ],
    notes: "강의 전 점검의 목적은 기능 개발이 아니라 시연 경로 안정화라고 설명한다.",
  },
  {
    id: "S16",
    track: "SAMPLE_CORE",
    title: "문제 발생 시 우회 시나리오",
    bullets: [
      "401: 토큰/사용자 확인",
      "CORS: 출처 설정 확인",
      "pending: 워커/백엔드 상태 확인",
      "BI 404: period 값 불일치 확인",
    ],
    notes: "당일에는 원인 분석보다 빠른 복구 루틴이 우선이라는 운영 원칙을 말한다.",
  },
  {
    id: "S17",
    track: "SAMPLE_CORE",
    title: "KPI 관점 중간 마무리",
    bullets: [
      "신규 기능 제안: SCM/CRM/BI 3개 축",
      "분석 백엔드 + 데모 웹 + AI 요약 연결",
      "강사 흐름(이론→분석→코드→ML 설명)과 정렬",
    ],
    notes: "본론 파트 종료 시 KPI 관점에서 의미를 다시 묶어준다.",
  },

  // ===== AI 정리 (마무리) =====
  {
    id: "R01",
    track: "AI_WRAPUP",
    title: "오류 분석 루프",
    bullets: [
      "error_analysis: 포스트모템 데이터로 실패를 구조화해 축적",
      "오류 유형/상황/근본 원인/재발 방지 규칙으로 기록",
      "다음 세션 체크리스트로 재투입해서 반복 실패 방지",
    ],
    notes: "실패를 숨기지 않고 공정 개선 입력으로 바꾸는 포스트모템 문화를 강조한다.",
  },
  {
    id: "R02",
    track: "AI_WRAPUP",
    title: "품질 게이트 체계",
    bullets: [
      "정적: ruff(포맷/린트), mypy(strict)",
      "실행: pytest(unit/integration)로 증적 남김",
      "커밋: pre-commit으로 로컬에서 실패를 앞당김",
      "운영 규칙: staged/unstaged 혼재 커밋 금지(롤백 비용 방지)",
    ],
    notes: "AI 산출물도 도구로 통과/실패가 판정되므로, 사람 감각 대신 팀 일관성이 유지된다는 점을 정리한다.",
  },
  {
    id: "R03",
    track: "AI_WRAPUP",
    title: "보안/비밀 관리 원칙",
    bullets: [
      ".env* 전면 ignore로 시크릿 유출 방지",
      "템플릿은 점 없는 파일명(env.example/env.prod.example)으로 분리",
      "토큰/키 커밋 금지(운영 보안 원칙 동일 적용)",
      "푸시 보호/시크릿 스캔 오탐 대응 원칙 문서화",
    ],
    notes: "데모라도 운영과 동일한 보안 위생을 유지했다는 점을 강조한다.",
  },
  {
    id: "R04",
    track: "AI_WRAPUP",
    title: "현업 복제 템플릿",
    bullets: [
      "규칙 문서 세트(context/architecture/workflow/error)",
      "세션 문서(CURRENT/WORK_HISTORY)로 범위와 증적 고정",
      "Gate 승인 문화(상태 머신)로 실행 권한 분리",
      "품질 자동화(ruff/mypy/pytest/pre-commit)로 객관 판정",
    ],
    notes: "모델이 바뀌어도 공정은 유지되므로, 운영체계를 복제한다는 메시지로 마무리한다.",
  },
];

/**
 * 스크린샷을 직접 넣을 슬라이드 힌트
 * - 사용자가 실제 화면 캡처 후, 해당 자리(placeholder)에 이미지 수동 삽입
 */
const IMAGE_HINTS = {
  S06: "Swagger 화면: /docs 또는 /openapi.json 접근 확인 장면",
  S08: "데모 메인 화면: 업로드/탭(SCM, CRM, BI) 영역이 보이게",
  S09: "SCM 결과 화면: 예측 라인 차트가 보이게",
  S10: "CRM 결과 화면: 이탈 Top-N/요약 영역이 보이게",
  S11: "BI 결과 화면: 히트맵 + YoY 영역이 보이게",
  S12: "Dify Studio 워크플로: Start→HTTP→Aggregator→LLM 노드 보이게",
  A02: "규칙 문서 트리: docs/rules 및 .cursorrules가 보이게",
  A03: "문서 참조 흐름: plan/CURRENT/error_analysis 위치가 보이게",
  R01: "error_analysis 문서 일부(오류 유형/원인/재발방지) 보이게",
};

function _getPresentation() {
  return SlidesApp.getActivePresentation();
}

function _createSlide(spec) {
  const pres = _getPresentation();
  const slide = pres.appendSlide(SlidesApp.PredefinedLayout.TITLE_AND_BODY);
  const pageElements = slide.getPageElements();

  // 1) 가능하면 PlaceholderType로 title/body를 찾는다.
  //    (일부 환경에서는 getPlaceholder()가 없어서 호출하면 TypeError 발생)
  let titleShape = null;
  let bodyShape = null;

  pageElements.forEach((el) => {
    if (el.getPageElementType() !== SlidesApp.PageElementType.SHAPE) return;
    const shape = el.asShape();

    if (typeof shape.getPlaceholder === "function") {
      const ph = shape.getPlaceholder();
      if (ph && typeof ph.getType === "function") {
        const type = ph.getType();
        if (type === SlidesApp.PlaceholderType.TITLE) titleShape = shape;
        if (type === SlidesApp.PlaceholderType.BODY) bodyShape = shape;
      }
    }
  });

  // 2) Placeholder API가 없으면(혹은 탐색 실패하면) TITLE_AND_BODY 레이아웃의
  //    “앞쪽 두 개 텍스트 Shape”를 title/body로 간주한다.
  if (!titleShape || !bodyShape) {
    const shapes = slide.getShapes ? slide.getShapes() : pageElements.filter((e) => e.getPageElementType() === SlidesApp.PageElementType.SHAPE).map((e) => e.asShape());
    const textShapes = shapes.filter((s) => {
      try {
        // Text가 없는 shape은 제외
        const t = s.getText && s.getText();
        return !!t;
      } catch (e) {
        return false;
      }
    });

    if (!titleShape && textShapes.length >= 1) titleShape = textShapes[0];
    if (!bodyShape && textShapes.length >= 2) bodyShape = textShapes[1];
  }

  if (titleShape && typeof titleShape.getText === "function") {
    titleShape.getText().setText(spec.title);
  }

  if (bodyShape && typeof bodyShape.getText === "function") {
    const bodyText = spec.bullets.map((b) => `• ${b}`).join("\n");
    bodyShape.getText().setText(bodyText);
  }

  // 하단 메타(발표 운영용)
  const meta = `${spec.id} | ${spec.track} | source: project docs`;
  slide.insertTextBox(meta, 20, 365, 500, 20).getText().getTextStyle().setFontSize(9);

  // 이미지 삽입 자리 안내(수동 스크린샷 삽입용)
  if (IMAGE_HINTS[spec.id]) {
    const imagePlaceholder = `[이미지 삽입 위치]\n${IMAGE_HINTS[spec.id]}`;
    slide
      .insertTextBox(imagePlaceholder, 360, 95, 330, 140)
      .getText()
      .getTextStyle()
      .setFontSize(10);
  }

  // 발표자 노트
  try {
    const notesShape = slide.getNotesPage().getSpeakerNotesShape();
    if (notesShape && typeof notesShape.getText === "function") {
      notesShape.getText().setText(spec.notes);
    }
  } catch (e) {
    // Notes page API가 없는 경우 무시
  }
}

/**
 * 전체 슬라이드 일괄 생성
 */
function createDeck() {
  DECK.forEach((s) => _createSlide(s));
}

/**
 * 호환을 위한 별칭(필요 시)
 */
function createAll() {
  createDeck();
}
```

---

## 3) 실행 순서(강의 흐름 기준)

- `createDeck()`만 실행하면 `DECK` 배열 순서대로 자동으로 적용된다.

예시(일괄 생성):

1. `createDeck()` 실행

---

## 4) 운영 메모

- 문구 수정은 `DECK` 데이터만 바꾸면 된다(코드 수정 최소화).
- 디자인은 Slides 테마/수동 편집으로 처리한다(요청사항 반영).
- 발표 흐름 변경 시 `track`은 유지하고 `DECK` 항목 순서만 조정하면 된다.
- 이미지가 필요한 슬라이드는 코드가 `[이미지 삽입 위치]` 텍스트박스를 자동으로 넣는다.
- 발표 준비 시 해당 위치에 직접 스크린샷(수동 캡처)을 삽입하고, 안내 텍스트박스는 삭제하면 된다.
