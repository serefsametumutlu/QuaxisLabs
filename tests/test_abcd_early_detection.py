"""src/analysis/abcd_early_detection.py testleri.

`_zigzag_df` deseni `tests/test_abcd_pattern.py`den BIREBIR alinir (anchor
barlarda kesin yerel ekstremum kuran, aralarinda dogrusal interpolasyonlu
sentetik OHLC) -- ayni disiplin: sadece anchor barlari pivot adayi olur, iki
anchor arasindaki dogrusal segmentin ic kismi ASLA pivot uretmez, bu yuzden
"D henuz onaylanmadi" pencerelerini elle, kapali-form olarak kurgulamak
mumkun olur. Gercek ag/dosya I/O YOK.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src.analysis.abcd_early_detection import (
    BUCKET_LABELS,
    BucketObservation,
    build_bucket_table,
    cd_progress_at,
    compare_to_null,
    compute_t_max,
    estimate_log_return_std,
    find_abc_candidates,
    format_bucket_sentence,
    generate_gbm_series,
)
from src.analysis.abcd_early_detection import analyze_series
from src.analysis.abcd_pattern import Params, Signal

EPS = 0.05


def _zigzag_df(anchors: list[tuple[int, float]], eps: float = EPS) -> pd.DataFrame:
    xs = [a[0] for a in anchors]
    ys = [a[1] for a in anchors]
    n = xs[-1] + 1
    t = np.arange(n)
    mid = np.interp(t, xs, ys)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC"),
            "open": mid,
            "high": mid + eps,
            "low": mid - eps,
            "close": mid,
            "volume": np.full(n, 1000.0),
        }
    )


PARAMS_L2 = Params(pivot_lookback=2)


# ── find_abc_candidates ──────────────────────────────────────────────────


def test_find_abc_candidates_tek_uclu_D_gelmeden_once():
    # A(high)@2=100 B(low)@7=80 C(high)@12=90 -- henuz D yok (df 12'de biter).
    df = _zigzag_df([(0, 95), (2, 100), (7, 80), (12, 90), (14, 88)])
    candidates = find_abc_candidates(df, PARAMS_L2)

    assert len(candidates) == 1
    c = candidates[0]
    assert (c.a_bar, c.b_bar, c.c_bar) == (2, 7, 12)
    # Pivot degerleri high/low dizisinden gelir (mid +/- EPS), close/mid DEGIL
    # -- `abcd_pattern.detect()`nin Signal.a_price/b_price/c_price ile AYNI ilke.
    assert c.a_price == pytest.approx(100, abs=EPS)
    assert c.b_price == pytest.approx(80, abs=EPS)
    assert c.c_price == pytest.approx(90, abs=EPS)
    assert c.c_confirm == 12 + PARAMS_L2.pivot_lookback == 14
    assert c.is_long is True  # C bir tepe -> D'nin dip olmasi beklenir


def test_find_abc_candidates_D_gelince_ikinci_aday_da_belirir():
    # A(high)@2=100 B(low)@7=80 C(high)@12=90 D(low)@17=70 -- artik
    # (A,B,C) VE (B,C,D) olmak uzere 2 ardisik ABC uclusu var.
    df = _zigzag_df([(0, 95), (2, 100), (7, 80), (12, 90), (17, 70), (19, 75)])
    candidates = find_abc_candidates(df, PARAMS_L2)

    assert len(candidates) == 2
    first, second = candidates
    assert (first.a_bar, first.b_bar, first.c_bar) == (2, 7, 12)
    assert (second.a_bar, second.b_bar, second.c_bar) == (7, 12, 17)
    assert second.is_long is False  # C=D(low) -> beklenen D bir tepe


# ── cd_progress_at ────────────────────────────────────────────────────────


def test_cd_progress_at_long_dogru_yon():
    # is_long=True: C'nin ALTINA inmek gecerli yon.
    assert cd_progress_at(80.0, 90.0, is_long=True, ab_range=20.0) == pytest.approx(0.5)


def test_cd_progress_at_long_yanlis_yon_sifir_doner():
    # C'nin altina INMEDEN (hala ustunde) ilerleme 0 olmali -- uydurulmaz.
    assert cd_progress_at(95.0, 90.0, is_long=True, ab_range=20.0) == 0.0


def test_cd_progress_at_short_dogru_yon():
    # is_long=False: C'nin USTUNE cikmak gecerli yon.
    assert cd_progress_at(100.0, 90.0, is_long=False, ab_range=20.0) == pytest.approx(0.5)


def test_cd_progress_at_dejenere_ab_araligi_sifir_doner():
    assert cd_progress_at(50.0, 90.0, is_long=True, ab_range=0.0) == 0.0


# ── analyze_series: uc-cikisli etiketleme ────────────────────────────────


def _success_df() -> pd.DataFrame:
    # A(high)@2=100 B(low)@7=80 C(high)@12=90 D(low)@17=70 -- ratio testi
    # GECER (cd_r=|70-90|/20=1.0, bc_r=|90-80|/20=0.5, strict 100>90>80 ve
    # 70<80) -- test_abcd_pattern.py::_bullish_df ile AYNI seviyeler.
    return _zigzag_df([(0, 95), (2, 100), (7, 80), (12, 90), (17, 70), (19, 75)])


def test_analyze_series_basari_D_gecerli_pivotla_tamamlanir():
    # df 4 pivot icerir (A,B,C,D) -> find_abc_candidates 2 aday uretir:
    # (A,B,C) VE (B,C,D) -- ilgilendigimiz (A,B,C) c_bar=12 ile secilir.
    # Ikinci aday (B,C,D), c_confirm=17+2=19=n-1 oldugundan (df bar 19'da
    # biter) HIC ileri bar tarayamaz -> 0 gozlem uretir, dolayisiyla
    # `observations` toplami SADECE ilk adaydan gelir.
    df = _success_df()
    labels, observations = analyze_series(df, PARAMS_L2, t_max=10)
    assert len(labels) == 2
    lab = next(l for l in labels if l.candidate.c_bar == 12)

    assert lab.label == 1
    assert lab.reason == "success"
    # c_confirm=12+2=14, D onay bari=17+2=19 -> t_event=19-14=5
    assert lab.t_event == 5

    # c_confirm+1 (15) ile D onay bari (19) arasi 5 bar taranir, HEPSI
    # basari etiketiyle (label=1) kova gozlemine donusur.
    assert len(observations) == 5
    assert all(o.outcome == 1 for o in observations)


def test_analyze_series_timeout_kucuk_t_max_ile_belirsiz_kalir():
    # AYNI basari senaryosu ama t_max=2 -- tarama D'ye (bar 19) ULASMADAN
    # (c_confirm+1..c_confirm+2 = 15..16) biter -> ne basari ne ret.
    df = _success_df()
    labels, _obs = analyze_series(df, PARAMS_L2, t_max=2)
    assert len(labels) == 2
    lab = next(l for l in labels if l.candidate.c_bar == 12)

    assert lab.label is None
    assert lab.reason == "timeout"
    assert lab.t_event is None


def test_analyze_series_asiri_uzama_pivot_gelmeden_iptal_eder():
    # A(high)@2=100 B(low)@7=80 C(high)@12=90 -- sonra bar 25'e kadar
    # KESINTISIZ dogrusal dusus (hicbir ic nokta yerel minimum degil, D
    # pivotu hic ONAYLANMAZ). Esik: cd_max_ext(1.272)+fib_tolerance(0.05)
    # = 1.322 -> fiyat 90 - 1.322*20 = 63.56 altina indiginde tetiklenir.
    # mid(t) = 90 - (50/13)*(t-12); bar19'da mid = 90 - (50/13)*7 ~= 63.08
    # (63.56'nin altinda, ilk kez), bar18'de ~66.92 (henuz ustunde).
    df = _zigzag_df([(0, 95), (2, 100), (7, 80), (12, 90), (25, 40)])
    labels, observations = analyze_series(df, PARAMS_L2, t_max=10)

    assert len(labels) == 1
    lab = labels[0]
    assert lab.label == 0
    assert lab.reason == "overextension"
    assert lab.t_event == 19 - 14  # == 5
    assert all(o.outcome == 0 for o in observations)


def test_analyze_series_reshuffle_oran_testi_fail_olursa():
    # A(high)@2=100 B(low)@7=80 C(high)@12=90 D(low)@17=85 -- D, B'nin (80)
    # ALTINA inmiyor (85>80) VE cd_r=|85-90|/20=0.25 (1.0'dan cok uzak) ->
    # _is_valid_abcd FAIL. Sonraki (22,92) anchor'i sadece bar17'nin kesin
    # bir yerel minimum olmasini saglamak icin (zigzag kurali).
    df = _zigzag_df([(0, 95), (2, 100), (7, 80), (12, 90), (17, 85), (22, 92)])
    labels, _observations = analyze_series(df, PARAMS_L2, t_max=10)

    # df 4 pivot icerir (A,B,C,D=85) -> 2 aday: (A,B,C) c_bar=12 (ilgilendigimiz)
    # VE (B,C,D) c_bar=17 (ayri bir senaryo, burada test edilmiyor).
    assert len(labels) == 2
    lab = next(l for l in labels if l.candidate.c_bar == 12)
    assert lab.label == 0
    assert lab.reason == "reshuffled"
    assert lab.t_event == 19 - 14  # == 5 (D onay bari = 17+2)


def test_analyze_series_bos_seride_bos_liste_doner():
    df = _zigzag_df([(0, 100), (5, 95)])
    labels, observations = analyze_series(df, PARAMS_L2, t_max=10)
    assert labels == []
    assert observations == []


# ── compute_t_max ────────────────────────────────────────────────────────


def _fake_signal(c_bar: int, d_bar: int) -> Signal:
    return Signal(
        direction=1, a_bar=0, b_bar=0, c_bar=c_bar, d_bar=d_bar,
        a_price=0.0, b_price=0.0, c_price=0.0, d_price=0.0,
        signal_bar=d_bar, signal_time=pd.Timestamp("2024-01-01", tz="UTC"),
        entry_ref=0.0, fill_ref=0.0, tp1=0.0, tp2=0.0, sl=0.0,
        bc_ratio=0.0, cd_ratio=0.0,
    )


def test_compute_t_max_bos_sinyal_listesinde_taban_doner():
    assert compute_t_max([], floor=20) == 20
    assert compute_t_max([], floor=7) == 7


def test_compute_t_max_persentil_taban_ustundeyse_persentil_kullanilir():
    signals = [_fake_signal(0, d) for d in range(1, 101)]  # sureler 1..100
    expected = max(int(round(np.percentile(range(1, 101), 95))), 20)
    assert compute_t_max(signals, percentile=95.0, floor=20) == expected
    assert expected > 20  # bu senaryoda persentil tabani asar (kontrol amacli)


def test_compute_t_max_persentil_tabanin_altindaysa_taban_kazanir():
    signals = [_fake_signal(0, d) for d in (1, 2, 3)]
    assert compute_t_max(signals, percentile=95.0, floor=20) == 20


# ── build_bucket_table (Wilson %95 GA) ────────────────────────────────────


def _obs(is_long: bool, bucket_index: int, n_success: int, n_fail: int, n_timeout: int = 0) -> list[BucketObservation]:
    out = [BucketObservation(is_long, bucket_index, 1) for _ in range(n_success)]
    out += [BucketObservation(is_long, bucket_index, 0) for _ in range(n_fail)]
    out += [BucketObservation(is_long, bucket_index, None) for _ in range(n_timeout)]
    return out


def test_build_bucket_table_guvenilir_hucre_wilson_araligi_statsmodels_ile_esles():
    from statsmodels.stats.proportion import proportion_confint

    observations = _obs(True, 0, n_success=25, n_fail=15)  # n=40 >= 30
    table = build_bucket_table(observations)

    row = table[(table["direction"] == "LONG") & (table["bucket_index"] == 0)].iloc[0]
    assert row["n_basari"] == 25
    assert row["n_toplam"] == 40
    assert row["oran"] == pytest.approx(0.625)
    assert row["guven_etiketi"] == "GUVENILIR"

    expected_low, expected_high = proportion_confint(25, 40, alpha=0.05, method="wilson")
    assert row["wilson_ci_low"] == pytest.approx(expected_low)
    assert row["wilson_ci_high"] == pytest.approx(expected_high)


def test_build_bucket_table_kucuk_n_guvensiz_etiketlenir_gizlenmez():
    observations = _obs(True, 1, n_success=3, n_fail=3, n_timeout=4)
    table = build_bucket_table(observations)

    row = table[(table["direction"] == "LONG") & (table["bucket_index"] == 1)].iloc[0]
    assert row["n_toplam"] == 6  # timeout'lar n_toplam'a DAHIL DEGIL
    assert row["n_timeout"] == 4
    assert row["guven_etiketi"] == "GUVENSIZ (n=6)"


def test_build_bucket_table_bos_hucre_nan_oran_ve_guvensiz_n0():
    observations = _obs(True, 0, n_success=5, n_fail=5)  # sadece bir hucre dolu
    table = build_bucket_table(observations)

    row = table[(table["direction"] == "SHORT") & (table["bucket_index"] == 0)].iloc[0]
    assert row["n_toplam"] == 0
    assert math.isnan(row["oran"])
    assert row["guven_etiketi"] == "GUVENSIZ (n=0)"

    # Tum 6 kova x 2 yon = 12 satir HER ZAMAN uretilir (hicbiri sessizce atlanmaz).
    assert len(table) == 2 * len(BUCKET_LABELS)


# ── null-hipotez (GBM) karsilastirmasi ────────────────────────────────────


def test_compare_to_null_buyuk_farkli_oranlar_anlamli_cikar():
    real_obs = _obs(True, 0, n_success=80, n_fail=20)  # %80, n=100
    null_obs = _obs(True, 0, n_success=50, n_fail=50)  # %50, n=100
    real_table = build_bucket_table(real_obs)
    null_table = build_bucket_table(null_obs)

    result = compare_to_null(real_table, null_table, min_n=30)
    row = result[(result["direction"] == "LONG") & (result["bucket_index"] == 0)].iloc[0]
    assert row["null_karsilastirma"] == "anlamli farkli"
    assert row["p_value"] < row["effective_alpha"]


def test_compare_to_null_yetersiz_n_test_edilemedi_etiketlenir():
    real_obs = _obs(True, 0, n_success=8, n_fail=2)  # n=10 < min_n
    null_obs = _obs(True, 0, n_success=5, n_fail=5)
    real_table = build_bucket_table(real_obs)
    null_table = build_bucket_table(null_obs)

    result = compare_to_null(real_table, null_table, min_n=30)
    row = result[(result["direction"] == "LONG") & (result["bucket_index"] == 0)].iloc[0]
    assert row["null_karsilastirma"] == "test edilemedi (n<30)"
    assert math.isnan(row["p_value"])


def test_compare_to_null_benzer_oranlar_nulldan_ayirt_edilemez():
    real_obs = _obs(True, 0, n_success=52, n_fail=48)  # n=100, %52
    null_obs = _obs(True, 0, n_success=50, n_fail=50)  # n=100, %50
    real_table = build_bucket_table(real_obs)
    null_table = build_bucket_table(null_obs)

    result = compare_to_null(real_table, null_table, min_n=30)
    row = result[(result["direction"] == "LONG") & (result["bucket_index"] == 0)].iloc[0]
    assert row["null_karsilastirma"] == "nulldan ayirt edilemiyor"


# ── GBM sentetik seri + volatilite tahmini ────────────────────────────────


def test_estimate_log_return_std_sabit_buyume_oraninda_sifira_yakin():
    # Her barda TAM %1 buyuyen bir seri -- log-getiri SABIT, std ~ 0.
    close = 100.0 * (1.01 ** np.arange(50))
    std = estimate_log_return_std(close)
    assert std == pytest.approx(0.0, abs=1e-9)


def test_estimate_log_return_std_yetersiz_veri_sifir_doner():
    assert estimate_log_return_std(np.array([100.0])) == 0.0
    assert estimate_log_return_std(np.array([])) == 0.0


def test_generate_gbm_series_deterministik_ve_pozitif():
    df1 = generate_gbm_series(n_bars=100, log_return_std=0.02, seed=42)
    df2 = generate_gbm_series(n_bars=100, log_return_std=0.02, seed=42)
    pd.testing.assert_frame_equal(df1, df2)

    assert len(df1) == 100
    assert (df1["low"] > 0).all()
    assert (df1["high"] >= df1["low"]).all()

    df3 = generate_gbm_series(n_bars=100, log_return_std=0.02, seed=7)
    assert not df1["close"].equals(df3["close"])  # farkli seed -> farkli seri


def test_generate_gbm_series_bos_n_bars():
    df = generate_gbm_series(n_bars=0, log_return_std=0.02, seed=1)
    assert df.empty


# ── rapor dili (ZORUNLU format, "olasilik" YASAK) ─────────────────────────


def test_format_bucket_sentence_olasilik_kelimesi_kullanilmaz():
    observations = _obs(True, 0, n_success=25, n_fail=15)
    table = build_bucket_table(observations)
    row = table[(table["direction"] == "LONG") & (table["bucket_index"] == 0)].iloc[0]
    row["null_karsilastirma"] = "anlamli farkli"

    sentence = format_bucket_sentence(row)
    assert "olasilik" not in sentence.lower()
    assert "olasılık" not in sentence.lower()
    assert "25/40" in sentence
    assert "GUVENILIR" in sentence


def test_format_bucket_sentence_bos_hucre_na_gosterir():
    observations = _obs(True, 0, n_success=1, n_fail=0)
    table = build_bucket_table(observations)
    row = table[(table["direction"] == "SHORT") & (table["bucket_index"] == 0)].iloc[0]

    sentence = format_bucket_sentence(row)
    assert "N/A" in sentence
