"""ComplexityScorer 단위 테스트.

외부 의존성 없음 — DB·Mock 불필요.
임계값(AI_ESCALATION_THRESHOLD)은 conftest.py에서 70으로 고정.
"""

import pytest
from app.core.routing import ComplexityScorer, QueryType, Route, RoutingRequest


@pytest.mark.parametrize(
    "query_type, row_count, cross_table, expected_score, expected_route",
    [
        # 단순 집계: base=10, 페널티/보너스 없음 → Tier 1
        (QueryType.AGGREGATION, 0, False, 10, Route.PANDAS),
        # 자연어: base=80 → 즉시 Tier 2
        (QueryType.NATURAL_LANGUAGE, 0, False, 80, Route.AI),
        # 이상치 설명: base=75 → Tier 2
        (QueryType.ANOMALY_EXPLAIN, 0, False, 75, Route.AI),
        # 예측+대용량(1M)+교차테이블: 30+20+15=65 → Tier 1 (65 < 70)
        (QueryType.FORECAST, 1_000_000, True, 65, Route.PANDAS),
        # 클러스터+교차테이블: 35+15=50 → Tier 1
        (QueryType.CLUSTER, 0, True, 50, Route.PANDAS),
        # 클러스터+대용량+교차테이블: 35+20+15=70 → Tier 2 (경계값 = threshold)
        (QueryType.CLUSTER, 1_000_000, True, 70, Route.AI),
    ],
)
def test_complexity_scorer(
    query_type: QueryType,
    row_count: int,
    cross_table: bool,
    expected_score: int,
    expected_route: Route,
) -> None:
    request = RoutingRequest(query_type=query_type, row_count=row_count, cross_table=cross_table)
    result = ComplexityScorer.score(request)
    assert result.score == expected_score
    assert result.route == expected_route


def test_size_penalty_medium_rows() -> None:
    """50만 행 이상 100만 미만 → size_penalty=10."""
    request = RoutingRequest(query_type=QueryType.TREND, row_count=500_000)
    result = ComplexityScorer.score(request)
    assert result.score == 25 + 10  # TREND(25) + penalty(10)
    assert result.route == Route.PANDAS


def test_size_penalty_large_rows() -> None:
    """100만 행 이상 → size_penalty=20."""
    request = RoutingRequest(query_type=QueryType.TREND, row_count=1_000_000)
    result = ComplexityScorer.score(request)
    assert result.score == 25 + 20  # TREND(25) + penalty(20)
    assert result.route == Route.PANDAS


def test_cross_table_bonus() -> None:
    """cross_table=True → +15 보너스."""
    without = ComplexityScorer.score(RoutingRequest(query_type=QueryType.AGGREGATION, cross_table=False))
    with_cross = ComplexityScorer.score(RoutingRequest(query_type=QueryType.AGGREGATION, cross_table=True))
    assert with_cross.score - without.score == 15
