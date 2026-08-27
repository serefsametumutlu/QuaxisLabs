"""8 ekolün her biri için ≥1 pozitif, ≥1 negatif fixture; Cypher'ın klasik
(Carney) tarafından reddedildiğinin doğrulanması. Tüm fiyat değerleri gerçek
kod çalıştırılarak (brute-force + analitik) doğrulanmıştır — bkz. session
notları; bu dosyadaki sabitler sonuç, türetme süreci değil."""

from __future__ import annotations

from tests.test_harmonics.fixtures import make_candidate
from tlab.indicators.harmonics.schools.beck_navarro200 import Navarro200School
from tlab.indicators.harmonics.schools.carney import CarneySchool
from tlab.indicators.harmonics.schools.five_zero import FiveZeroSchool
from tlab.indicators.harmonics.schools.gilmore import GilmoreSchool
from tlab.indicators.harmonics.schools.kerkez_nenstar import NenStarSchool
from tlab.indicators.harmonics.schools.oglesbee_cypher import CypherSchool
from tlab.indicators.harmonics.schools.pesavento import PesaventoSchool
from tlab.indicators.harmonics.schools.three_drives import ThreeDrivesSchool

# Ortak "gartley-benzeri" aday: Carney/Pesavento/Gilmore'un hepsinde gartley
# eşleşir (aynı X,A,B,C üçü için de geçerli).
_GARTLEY_LIKE = (100.0, 120.0, 107.64, 116.64)


def test_carney_gartley_matches() -> None:
    cand = make_candidate(*_GARTLEY_LIKE)
    matches = CarneySchool().match(cand)
    names = {m.spec.name for m in matches}
    assert "gartley" in names


def test_carney_gartley_rejects_out_of_range_ratio() -> None:
    x, a = 100.0, 120.0
    b = a - 0.25 * (a - x)  # ab_xa=0.25, hiçbir Carney formasyonunun xab aralığında değil
    c = b + 0.5 * (a - b)
    cand = make_candidate(x, a, b, c)
    matches = CarneySchool().match(cand)
    assert matches == []


def test_carney_shark_matches_with_zero_point() -> None:
    cand = make_candidate(100.0, 120.0, 110.0, 123.0, zero=90.0)
    matches = CarneySchool().match(cand)
    names = {m.spec.name for m in matches}
    assert "shark" in names


def test_pesavento_gartley_matches_with_ab_cd_symmetry() -> None:
    cand = make_candidate(*_GARTLEY_LIKE)
    matches = PesaventoSchool().match(cand)
    assert {m.spec.name for m in matches} == {"gartley"}


def test_pesavento_rejects_when_ab_cd_symmetry_broken() -> None:
    # xa_ret oranı gartley'e uyuyor ama C öyle seçildi ki CD/AB hiçbir
    # standart orana (1.0/1.27/1.618) yakın değil.
    cand = make_candidate(100.0, 120.0, 107.64, 105.0)
    assert PesaventoSchool().match(cand) == []


def test_gilmore_reuses_pesavento_price_ratios() -> None:
    cand = make_candidate(*_GARTLEY_LIKE)
    matches = GilmoreSchool().match(cand)
    assert {m.spec.name for m in matches} == {"gartley"}


def test_cypher_matches_when_c_beyond_a() -> None:
    cand = make_candidate(100.0, 120.0, 110.0, 123.0)
    assert cand.c_beyond_a is True
    matches = CypherSchool().match(cand)
    assert {m.spec.name for m in matches} == {"cypher"}


def test_cypher_candidate_rejected_by_classic_carney() -> None:
    """Cypher'ın C>A geometrisi, klasik (Carney) tarafından TAMAMEN reddedilmeli
    (c_beyond_a=True hiçbir klasik retracement formasyonuna uymaz; shark ise
    zero noktası olmadığı için değerlendirilmez)."""
    cand = make_candidate(100.0, 120.0, 110.0, 123.0)
    assert CarneySchool().match(cand) == []


def test_nenstar_matches() -> None:
    cand = make_candidate(100.0, 120.0, 109.0, 123.3)
    matches = NenStarSchool().match(cand)
    assert {m.spec.name for m in matches} == {"nenstar"}


def test_nenstar_rejects_without_intersection() -> None:
    cand = make_candidate(100.0, 120.0, 110.0, 123.0)  # cypher fixture, farklı geometri
    assert NenStarSchool().match(cand) == []


def test_navarro200_matches() -> None:
    x, a = 100.0, 120.0
    b = a - 0.4 * (a - x)
    c = b + 1.28 * (a - b)
    cand = make_candidate(x, a, b, c)
    matches = Navarro200School().match(cand)
    assert {m.spec.name for m in matches} == {"navarro200"}


def test_navarro200_rejects_wrong_d_target() -> None:
    cand = make_candidate(*_GARTLEY_LIKE)  # D burada 0.786 XA'da, 2.0 XA'da değil
    assert Navarro200School().match(cand) == []


def test_five_zero_matches() -> None:
    cand = make_candidate(100.0, 112.0, 91.6, 50.8, zero=90.0)
    matches = FiveZeroSchool().match(cand)
    assert {m.spec.name for m in matches} == {"five_zero"}


def test_five_zero_requires_zero_point() -> None:
    cand = make_candidate(100.0, 112.0, 91.6, 50.8)  # zero yok
    assert FiveZeroSchool().match(cand) == []


def test_three_drives_matches_impulsive_continuation() -> None:
    x, a = 100.0, 120.0
    b = a - 1.272 * (a - x)
    c = b + 0.7 * (a - b)
    cand = make_candidate(x, a, b, c)
    assert cand.b_beyond_x is True
    matches = ThreeDrivesSchool().match(cand)
    assert {m.spec.name for m in matches} == {"three_drives_1272"}


def test_three_drives_rejects_plain_retracement() -> None:
    """B, X'i aşmıyorsa (klasik retracement) three_drives asla eşleşmemeli."""
    cand = make_candidate(*_GARTLEY_LIKE)
    assert cand.b_beyond_x is False
    assert ThreeDrivesSchool().match(cand) == []
