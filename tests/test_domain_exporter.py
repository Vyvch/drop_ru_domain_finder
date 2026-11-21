import pytest
from domain_exporter import export_domains_to_csv, calculate_average_score

def test_export_csv():
    data = [{"domain": "test.ru", "score": 85}, {"domain": "site.ru", "score": 65}]
    csv_str = export_domains_to_csv(data)
    assert "test.ru" in csv_str
    assert "score" in csv_str

def test_average_score():
    data = [{"domain": "a.ru", "score": 90}, {"domain": "b.ru", "score": 50}]
    assert calculate_average_score(data) == 70.0
