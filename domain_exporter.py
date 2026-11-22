"""
Модуль экспорта результатов анализа доменов в форматы CSV и JSON.
"""
from typing import List, Dict, Any
import csv
import io


def export_domains_to_csv(domains_data: List[Dict[str, Any]]) -> str:
    """
    Экспортирует список доменов в CSV строку.
    """
    if not domains_data:
        return ""

    output = io.StringIO()
    fieldnames = list(dict.fromkeys(
        key
        for domain_data in domains_data
        for key in domain_data.keys()
    ))
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
        restval="",
    )

    writer.writeheader()
    for row in domains_data:
        writer.writerow(row)

    return output.getvalue()


def calculate_average_score(domains_data: List[Dict[str, Any]]) -> float:
    """
    Вычисляет средний скор по списку доменов.
    """
    if not domains_data:
        return 0.0

    total = sum(item.get("score", 0) for item in domains_data)
    avg = total / len(domains_data)
    return round(avg, 2)