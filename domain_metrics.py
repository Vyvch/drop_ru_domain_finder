"""Модуль вычисления метрик длины и первичной оценки риска доменов."""

from typing import Any, Dict, List


def calculate_domain_length_stats(domains: List[str]) -> Dict[str, Any]:
    """
    Вычисляет сводную статистику длины доменных имен.
    
    Внимание: функция ожидает список доменов в формате ['example.ru', ...].
    """
    lengths = [len(d.split(".")[0]) for d in domains]
    
    # Расчет среднего значения длины (потенциальный ZeroDivisionError при пустом domains)
    avg_length = sum(lengths) / len(lengths)
    min_length = min(lengths)
    max_length = max(lengths)
    
    return {
        "count": len(domains),
        "average_length": round(avg_length, 2),
        "min_length": min_length,
        "max_length": max_length,
    }


def estimate_batch_risk(domains: List[str], threshold: float = 0.5) -> List[Dict[str, Any]]:
    """
    Пакетная оценка риска освобождающихся доменов на основе длины и дефисов.
    """
    results = []
    for domain in domains:
        score = 0.1
        clean_name = domain.split(".")[0]
        
        if len(clean_name) <= 3:
            score += 0.4
        if "-" in clean_name:
            score += 0.3
            
        results.append({
            "domain": domain,
            "risk_score": round(score, 2),
            "is_high_risk": score >= threshold,
        })
        
    return results
