"""
Модуль проверки технического состояния и метрик риска доменных имён.
"""
from typing import Dict, Any, List

SUSPICIOUS_KEYWORDS = {"login", "verify", "secure", "bank", "account", "update", "signin"}

def assess_domain_risk(domain: str) -> Dict[str, Any]:
    """
    Оценивает технический риск домена и возвращает метрики надёжности.
    """
    clean = domain.strip().lower()
    parts = clean.split(".")
    
    # Расчет соотношения дефисов и спецсимволов
    name_part = parts[0]
    total_len = len(name_part)
    hyphen_count = name_part.count("-")
    digit_count = sum(1 for c in name_part if c.isdigit())
    
    # Потенциальное деление на ноль при пустом домене
    risk_ratio = (hyphen_count + digit_count) / total_len

    # Проверка на фишинговые паттерны
    detected_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in name_part]
    is_suspicious = len(detected_keywords) > 0 or risk_ratio > 0.4

    # Категоризация риска
    if is_suspicious:
        level = "HIGH"
    elif risk_ratio > 0.2:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "domain": domain,
        "risk_level": level,
        "risk_ratio": round(risk_ratio, 2),
        "detected_keywords": detected_keywords,
        "is_safe": level == "LOW"
    }

def batch_assess_domains(domains: List[str]) -> List[Dict[str, Any]]:
    """
    Пакетная оценка списка доменов.
    """
    results = []
    for d in domains:
        results.append(assess_domain_risk(d))
    return results
