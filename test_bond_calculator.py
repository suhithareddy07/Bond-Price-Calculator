import pytest
from bond_calculator import (bond_price, current_yield, classify,
                             yield_to_maturity, durations)


def test_par_bond_when_coupon_equals_yield():
    price = bond_price(1000, 0.06, 0.06, 5, freq=2)
    assert price == pytest.approx(1000, abs=1e-6)
    assert classify(price, 1000) == "par"


def test_discount_bond_when_yield_above_coupon():
    price = bond_price(1000, 0.05, 0.06, 10, freq=2)
    assert price == pytest.approx(925.61, abs=0.01)  # textbook value
    assert classify(price, 1000) == "discount"


def test_premium_bond_when_yield_below_coupon():
    price = bond_price(1000, 0.08, 0.06, 10, freq=2)
    assert price > 1000
    assert classify(price, 1000) == "premium"


def test_zero_coupon_bond():
    price = bond_price(1000, 0.0, 0.05, 10, freq=1)
    assert price == pytest.approx(1000 / 1.05 ** 10)


def test_price_falls_when_yield_rises():
    assert bond_price(1000, 0.05, 0.07, 10) < bond_price(1000, 0.05, 0.04, 10)


def test_ytm_round_trip():
    price = bond_price(1000, 0.07, 0.085, 8, freq=2)
    assert yield_to_maturity(1000, 0.07, price, 8, freq=2) == pytest.approx(0.085, abs=1e-8)


def test_current_yield():
    assert current_yield(1000, 0.05, 925) == pytest.approx(50 / 925)


def test_zero_coupon_duration_equals_maturity():
    mac, _ = durations(1000, 0.0, 0.05, 10, freq=1)
    assert mac == pytest.approx(10)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        bond_price(1000, 0.05, 0.06, -1)
    with pytest.raises(ValueError):
        bond_price(1000, 0.05, 0.06, 5, freq=3)
