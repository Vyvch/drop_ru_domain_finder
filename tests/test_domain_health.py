import pytest
from domain_health import assess_domain_risk, batch_assess_domains

def test_safe_domain():
    res = assess_domain_risk("example.ru")
    assert res["risk_level"] == "LOW"
    assert res["is_safe"] is True
    assert res["detected_keywords"] == []

def test_suspicious_domain():
    res = assess_domain_risk("secure-bank-login123.ru")
    assert res["risk_level"] == "HIGH"
    assert "login" in res["detected_keywords"]
    assert res["is_safe"] is False

def test_batch_assess():
    domains = ["mysite.ru", "bank-secure.ru"]
    results = batch_assess_domains(domains)
    assert len(results) == 2
    assert results[0]["domain"] == "mysite.ru"
