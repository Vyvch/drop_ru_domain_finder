import pytest
from domain_metrics import calculate_domain_length_stats, estimate_batch_risk


def test_calculate_domain_length_stats_valid():
    sample = ["apple.ru", "banana.ru", "cat.ru"]
    stats = calculate_domain_length_stats(sample)
    
    assert stats["count"] == 3
    assert stats["min_length"] == 3  # 'cat'
    assert stats["max_length"] == 6  # 'banana'
    assert stats["average_length"] == pytest.approx(4.67, 0.01)


def test_estimate_batch_risk_scores():
    domains = ["a.ru", "normal-domain.ru", "superproject.ru"]
    results = estimate_batch_risk(domains, threshold=0.5)
    
    assert len(results) == 3
    # 'a.ru': len <= 3 -> score 0.5 -> is_high_risk True
    assert results[0]["is_high_risk"] is True
    # 'normal-domain.ru': has '-' -> score 0.4 -> is_high_risk False
    assert results[1]["risk_score"] == 0.4
