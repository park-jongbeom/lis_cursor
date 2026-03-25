# Dify 연동 규칙 — FastAPI ↔ Local Self-hosted Dify

> **핵심 원칙**: Dify는 데이터를 직접 처리하지 않는다.
> 복잡한 수치 계산은 반드시 FastAPI에 위임하고, 정제된 JSON만 받아서 LLM에 전달한다.
> Spring Boot 비유: Dify = Camunda (BPM 워크플로 엔진) + LLM 호출 내장

---

## 1. 역할 분리 원칙

| 계층 | 담당 | 처리 내용 |
|------|------|----------|
| **데이터 처리 계층** | FastAPI + Pandas | CSV 파싱, 결측치 처리, Prophet/K-Means 실행, JSON 직렬화 |
| **AI 오케스트레이션 계층** | Self-hosted Dify | HTTP Request → LLM Node 체인, 멀티스텝 프롬프팅, 워크플로 시각화 |
| **LLM 실행 계층** | Claude API / Ollama | 자연어 이해, 인사이트 생성, 한국어 요약 |

---

## 2. REST API 응답 JSON 포맷 표준

### 원칙: Dify LLM Node의 컨텍스트 창을 낭비하지 않는다

Dify에서 FastAPI를 호출할 때 응답 크기가 크면 LLM 컨텍스트 창이 낭비된다.
따라서 **모든 분석 엔드포인트는 `compact=true` 쿼리 파라미터를 지원해야 한다.**

```python
# 모든 분석 엔드포인트 공통 패턴
# app/api/v1/endpoints/crm.py

@router.get("/crm/churn-risk")
async def get_churn_risk(
    dataset_id: UUID,
    top_n: int = 20,
    compact: bool = False,       # Dify HTTP Request Node → ?compact=true 로 호출
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = await crm_service.compute_churn_risk(dataset_id, db)

    if compact:
        # Dify용: 핵심 필드만 반환 — LLM 컨텍스트 절약
        return {
            "high_risk_count": len(result.high_risk),
            "top_customers": [
                {"code": c.code, "name": c.name, "risk_score": c.score}
                for c in result.high_risk[:top_n]
            ],
            "summary": result.summary_stats,
        }

    return result  # 일반 클라이언트용: 전체 응답
```

### compact=true 응답 설계 기준

| 항목 | 기준 |
|------|------|
| 최대 리스트 항목 수 | 기본 20개 (`top_n` 파라미터로 조정 가능) |
| 포함 필드 | 식별자(code/id), 핵심 지표 1~3개, 요약 텍스트 1개 |
| 제외 필드 | 타임스탬프, 메타데이터, 중간 계산 결과, 원본 배열 전체 |
| 응답 크기 목표 | 4KB 이하 (LLM 컨텍스트 1,000 토큰 이내) |

### 도메인별 compact 응답 형식

**SCM (수요 예측):**
```json
{
  "forecast_period_days": 30,
  "high_demand_items": [
    {"test_code": "BRCA1", "predicted_qty": 142, "trend": "increasing"}
  ],
  "restock_alerts": 3,
  "summary": "BRCA1 수요 14% 증가 예상. 3개 품목 재고 보충 필요."
}
```

**CRM (고객 분석):**
```json
{
  "high_risk_count": 12,
  "top_customers": [
    {"code": "C001", "name": "서울대병원", "risk_score": 0.87}
  ],
  "cluster_count": 4,
  "summary": "12개 거래처 이탈 위험. 서울 권역 집중 관리 필요."
}
```

**BI (트렌드 분석):**
```json
{
  "period": "2026-01",
  "top_regions": ["서울", "부산", "대구"],
  "trending_tests": ["BRCA1", "HPV"],
  "heatmap_highlights": [
    {"region": "서울", "test": "BRCA1", "growth_rate": 0.23}
  ],
  "summary": "서울 BRCA1 검사 23% 증가. 계절성 패턴 확인됨."
}
```

---

## 3. Dify HTTP Request Node 연동 가이드

### Dify에서 FastAPI 엔드포인트를 호출하는 방법

```yaml
# Dify Workflow 노드 구성 예시 (Dify Web UI에서 설정)

노드 타입: HTTP Request
메서드: POST
URL: http://fastapi-app:8000/api/v1/crm/cluster
  # Docker 네트워크 내부: fastapi-app은 docker-compose.yml의 서비스명
  # 외부에서 테스트: http://localhost:8000/api/v1/crm/cluster

Headers:
  Content-Type: application/json
  Authorization: Bearer {{sys.user_id}}  # 또는 고정 API 키

Query Params:
  compact: "true"    # 반드시 문자열 "true"로 전달

Body (JSON):
  {
    "dataset_id": "{{dataset_id}}",
    "cluster_count": 4,
    "include_rfm": true
  }

출력 변수명: crm_result
```

### Dify 워크플로 전체 흐름 (CRM 이탈 분석 예시)

```
① Start Node
   - 입력 변수: user_query (string), dataset_id (string)

② HTTP Request Node  →  FastAPI /crm/cluster
   - compact=true
   - 출력: crm_result

③ HTTP Request Node  →  FastAPI /bi/regional-heatmap
   - compact=true, period=현재월
   - 출력: bi_result

④ Variable Aggregator Node
   - 입력: crm_result + bi_result
   - 출력: combined_data

⑤ LLM Node (Claude Sonnet 또는 Ollama)
   System: "당신은 의료 검사 영업 분석 전문가입니다. 주어진 데이터를 분석하여 한국어로 인사이트를 제공하세요."
   User:   "데이터: {{combined_data}}\n질문: {{user_query}}"
   - 출력: llm_answer

⑥ Answer Node
   - 응답: "{{llm_answer}}"
```

---

## 4. FastAPI → Dify 프록시 패턴 (방식 A)

자연어 쿼리를 FastAPI `/agent/query` 엔드포인트로 받아 Dify Workflow API로 프록시하는 방식.

```python
# app/services/ai/agent_service.py

class AgentService:
    """Dify Workflow API 프록시 서비스. Spring: @Component LLMGateway"""

    def __init__(self) -> None:
        self._dify_base_url = settings.DIFY_API_BASE_URL  # http://localhost/v1
        self._dify_api_key = settings.DIFY_API_KEY         # app-xxxx...

    async def analyze(self, query: str, dataset_id: str) -> AgentResult:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._dify_base_url}/workflows/run",
                headers={"Authorization": f"Bearer {self._dify_api_key}"},
                json={
                    "inputs": {
                        "user_query": query,
                        "dataset_id": dataset_id,
                    },
                    "response_mode": "blocking",
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            return AgentResult(
                answer=data["data"]["outputs"]["answer"],
                workflow_run_id=data["workflow_run_id"],
            )
```

> **방식 B (강의 권장)**: 프론트엔드 또는 Dify Chat UI에서 FastAPI를 직접 HTTP Request Node로 호출.
> 코드 작성 없이 Dify 시각적 워크플로만으로 완성 가능. 방식 A보다 학습 목적에 적합.

---

## 5. 인프라 구성 (Docker 네트워크 공유)

### 포트 구성 (충돌 방지)

| 서비스 | 포트 | 파일 |
|--------|------|------|
| FastAPI (idr_analytics) | 8000 | `docker-compose.yml` |
| Dify Web UI + API Gateway | 80 | `docker-compose.dify.yml` |
| PostgreSQL (idr 전용) | 5432 | `docker-compose.yml` |
| PostgreSQL (Dify 전용) | **5433** | `docker-compose.dify.yml` (충돌 방지) |
| Redis (공유 가능) | 6379 | `docker-compose.yml` |
| Ollama (온프레미스 LLM) | 11434 | 호스트 직접 실행 |

### 네트워크 공유 — `idr-net` 브리지

```yaml
# docker-compose.yml (FastAPI 스택)
networks:
  idr-net:
    name: idr-net
    driver: bridge

# docker-compose.dify.yml (Dify 스택)
networks:
  idr-net:
    external: true  # FastAPI 스택과 같은 네트워크 공유
```

> 네트워크 공유 이유: Dify의 HTTP Request Node에서 `http://fastapi-app:8000`으로 직접 접근하기 위함.
> 포트 포워딩(localhost:8000) 대신 Docker 내부 DNS로 통신.

### 환경 변수 (.env.example 필수 항목)

```dotenv
# Dify 연동 설정 (방식 A — FastAPI 프록시 시)
DIFY_API_BASE_URL=http://localhost/v1
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DIFY_WORKFLOW_ID=your-workflow-id-here
```

---

## 6. Dify 연동 시 FastAPI 응답 설계 체크리스트

코드를 작성하기 전 아래 항목을 확인한다:

- [ ] 엔드포인트에 `compact: bool = False` 파라미터가 있는가
- [ ] `compact=True` 응답이 4KB 이하인가
- [ ] `compact=True` 응답의 최상위 키 이름이 명확한가 (Dify Variable Aggregator에서 `{{crm_result.key}}`로 참조)
- [ ] 응답 JSON에 한국어 요약 문자열 필드(`summary`)가 있는가
- [ ] Dify HTTP Request Node에서 파싱할 배열의 길이가 `top_n`으로 제한되는가
- [ ] 에러 응답 시 Dify가 처리할 수 있는 명확한 JSON 에러 메시지를 반환하는가
