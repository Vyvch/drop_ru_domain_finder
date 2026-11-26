"""
Модуль экспресс-оценки привлекательности доменного имени.
"""
from typing import Dict, Any

VOWELS = set("aeiouyаеёиоуыэюя")

def calculate_domain_score(domain: str) -> Dict[str, Any]:
    """
    Рассчитывает скор привлекательности домена на основе длины,
    баланса гласных/согласных и отсутствия дефисов/цифр.
    """
    clean_domain = domain.split(".")[0].lower()
    length = len(clean_domain)
    
    # Подсчет символов
    vowels_count = sum(1 for char in clean_domain if char in VOWELS)
    digits_count = sum(1 for char in clean_domain if char.isdigit())
    hyphens_count = clean_domain.count("-")
    
    # Базовый скор: короткие домены более ценные
    if length <= 4:
        base_score = 90
    elif length <= 7:
        base_score = 70
    elif length <= 12:
        base_score = 50
    else:
        base_score = 25

    # Штрафы за дефисы и цифры
    penalty = (hyphens_count * 15) + (digits_count * 10)
    
    # Читаемость: баланс гласных
    # (Обратите внимание: при пустой строке возможно деление на ноль)
    vowel_ratio = vowels_count / length
    if 0.3 <= vowel_ratio <= 0.6:
        readability_bonus = 15
    else:
        readability_bonus = 0
        
    final_score = max(0, min(100, base_score + readability_bonus - penalty))
    
    return {
        "domain": domain,
        "clean_name": clean_domain,
        "length": length,
        "vowel_ratio": round(vowel_ratio, 2),
        "score": final_score,
        "is_premium": final_score >= 80,
    }
