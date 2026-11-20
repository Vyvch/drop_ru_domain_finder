from analyzer import calculate_domain_score

def test_calculate_domain_score_short():
    res = calculate_domain_score("auto.ru")
    assert res["score"] >= 80
    assert res["is_premium"] is True

def test_calculate_domain_score_digits():
    res = calculate_domain_score("shop-12345.ru")
    assert res["score"] < 60
    assert res["is_premium"] is False
