"""scripts/abcd_research.py testleri.

Gercek ag/DB cagrisi YOK -- `abcd_research.run_grid` monkeypatch ile sahte
DataFrame donduren bir taklitle degistirilir (test_abcd_backtest.py'nin
`_patch_data_layer` ilkesiyle AYNI, ama burada dogrudan `run_grid`'in
KENDISI taklit edilir -- script `run_grid`'in ic mantigini degil, KENDI
orkestrasyonunu (LONG/SHORT ayrimi, rapor formatlama, "en verimli 5" secimi)
test etmelidir).

`--symbols` her testte ACIKCA verilir -- `get_bist_universe()` (gercek DB)
hicbir testte cagrilmaz.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

import scripts.abcd_research as abcd_research
from src.analysis.abcd_pattern import Params

_COLUMNS = [
    "tf", "currency", "params", "n_trades", "win_rate", "profit_factor", "expectancy_r", "avg_r",
    "avg_max_drawdown_pct", "exposure_pct", "trustworthy", "guven_etiketi", "currency_note", "grid_warning",
]


def _row(tf, currency, n_trades, trustworthy, profit_factor=1.5, expectancy_r=0.3, win_rate=55.0, dd=-5.0, currency_note=""):
    guven = "GUVENILIR" if trustworthy else f"GUVENSIZ (n={n_trades})"
    return {
        "tf": tf, "currency": currency, "params": "L5_atr1.0_eps0.05", "n_trades": n_trades,
        "win_rate": win_rate, "profit_factor": profit_factor, "expectancy_r": expectancy_r, "avg_r": expectancy_r,
        "avg_max_drawdown_pct": dd, "exposure_pct": 10.0, "trustworthy": trustworthy, "guven_etiketi": guven,
        "currency_note": currency_note, "grid_warning": "2 hucre karsilastirildi (...)",
    }


def _fake_summary(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=_COLUMNS)
    df.attrs["grid_warning"] = rows[0]["grid_warning"] if rows else "(hucre yok)"
    return df


# ── _parse_list / _fmt_num ─────────────────────────────────────────────────


def test_parse_list_virgullu_stringi_ayirir_bosluklari_temizler():
    assert abcd_research._parse_list(" THYAO, ASELS ,TUPRS") == ["THYAO", "ASELS", "TUPRS"]


def test_parse_list_bos_string_bos_liste():
    assert abcd_research._parse_list("") == []


def test_fmt_num_nan_na_doner():
    assert abcd_research._fmt_num(float("nan")) == "N/A"


def test_fmt_num_pozitif_sonsuz():
    assert abcd_research._fmt_num(float("inf")) == "sonsuz"


def test_fmt_num_negatif_sonsuz():
    assert abcd_research._fmt_num(float("-inf")) == "-sonsuz"


def test_fmt_num_normal_deger_formatlanir():
    assert abcd_research._fmt_num(1.23456, "{:.2f}") == "1.23"


# ── _build_report: GUVENSIZ hucreler SILINMEZ, "en verimli 5" trustworthy filtreli ─


def test_build_report_guvensiz_hucre_tablodan_silinmez():
    combined = pd.concat(
        [
            _fake_summary([_row("1D", "TRY", 12, False)]).assign(yon="LONG"),
            _fake_summary([_row("1D", "TRY", 150, True)]).assign(yon="SHORT"),
        ],
        ignore_index=True,
    )
    report = abcd_research._build_report(
        combined, "LONG uyari", "SHORT uyari", ["THYAO"], ["1D"], ["TRY"], 2.0, 30, 100, out_csv_path="dummy.csv"
    )
    assert "GUVENSIZ (n=12)" in report
    assert "GUVENILIR" in report


def test_build_report_en_verimli_5_sadece_trustworthy_secer():
    # Guvensiz hucre YUKSEK profit_factor'a ragmen "en verimli" listesine giremez.
    guvensiz_yuksek_pf = _row("240", "TRY", 15, False, profit_factor=99.0, expectancy_r=5.0)
    guvenilir_dusuk_pf = _row("1D", "TRY", 120, True, profit_factor=1.2, expectancy_r=0.1)
    combined = pd.concat(
        [
            _fake_summary([guvensiz_yuksek_pf]).assign(yon="LONG"),
            _fake_summary([guvenilir_dusuk_pf]).assign(yon="SHORT"),
        ],
        ignore_index=True,
    )
    report = abcd_research._build_report(
        combined, "LONG uyari", "SHORT uyari", ["THYAO"], ["1D", "240"], ["TRY"], 2.0, 30, 100, out_csv_path="dummy.csv"
    )
    top5_section = report.split("En Verimli 5 Kosul")[1].split("## TRY Grafigi")[0]
    assert "99.00" not in top5_section  # guvensiz hucrenin profit_factor'u en-iyi listesinde YOK
    assert "1.20" in top5_section  # tek trustworthy hucre listede VAR


def test_build_report_hicbir_trustworthy_yoksa_acik_mesaj_verir():
    combined = _fake_summary([_row("1D", "TRY", 10, False)]).assign(yon="LONG")
    report = abcd_research._build_report(
        combined, "LONG uyari", "SHORT uyari", ["THYAO"], ["1D"], ["TRY"], 2.0, 30, 100, out_csv_path="dummy.csv"
    )
    assert "esigini gecmedi" in report or "YAPILAMAZ" in report


def test_build_report_usd_bolumu_currency_note_tekrarlar():
    combined = pd.concat(
        [
            _fake_summary([_row("1D", "TRY", 40, False)]).assign(yon="LONG"),
            _fake_summary([_row("1D", "USD", 40, False, currency_note="BAGIMSIZ tespit -- doviz-ayarli DEGIL")]).assign(yon="LONG"),
        ],
        ignore_index=True,
    )
    report = abcd_research._build_report(
        combined, "LONG uyari", "SHORT uyari", ["THYAO"], ["1D"], ["TRY", "USD"], 2.0, 30, 100, out_csv_path="dummy.csv"
    )
    usd_section = report.split("## USD Grafigi")[1]
    assert "BAGIMSIZ tespit" in usd_section


def test_build_report_bos_hucre_de_gosterilir_mesajla():
    combined = _fake_summary([_row("1D", "TRY", 40, False)]).assign(yon="LONG")
    report = abcd_research._build_report(
        combined, "LONG uyari", "SHORT uyari", ["THYAO"], ["1D", "240"], ["TRY"], 2.0, 30, 100, out_csv_path="dummy.csv"
    )
    # 240/SHORT/TRY hicbir satirda yok -- rapor bunu sessizce atlamamali, "uretilmedi" notu vermeli
    assert "uretilmedi" in report


# ── main(): uctan uca, run_grid taklit edilir, gercek ag/DB YOK ────────────


@pytest.fixture
def _patch_run_grid(monkeypatch):
    """`run_grid`'i cagrilan `detector_params`'a gore FARKLI sonuc donduren
    bir taklitle degistirir -- boylece script'in LONG/SHORT icin GERCEKTEN
    AYRI cagri yaptigini (ve yon bilgisini KAYBETMEDIGINI) dogrulayabiliriz."""
    calls = []

    def _fake_run_grid(symbols, tfs, backtest_params, denominators, years, min_trades_show, min_trades_trustworthy, detector_params):
        dp = detector_params[0]
        calls.append(dp)
        n = 150 if dp.enable_long else 8  # LONG guvenilir, SHORT guvensiz -- ayirt edici
        rows = []
        for tf in tfs:
            for denom in denominators:
                rows.append(_row(tf, denom, n, trustworthy=(n >= min_trades_trustworthy)))
        return _fake_summary(rows)

    monkeypatch.setattr(abcd_research, "run_grid", _fake_run_grid)
    return calls


def test_main_long_short_icin_ayri_run_grid_cagrisi_yapar(tmp_path, _patch_run_grid, capsys):
    out_md = tmp_path / "rapor.md"
    out_csv = tmp_path / "ham.csv"

    rc = _run_main_argv(
        [
            "--symbols", "THYAO,ASELS",
            "--tfs", "1D",
            "--currencies", "TRY",
            "--out", str(out_md),
            "--out-csv", str(out_csv),
        ]
    )

    assert rc == 0
    assert len(_patch_run_grid) == 2  # LONG + SHORT -- iki AYRI cagri
    assert _patch_run_grid[0].enable_long and not _patch_run_grid[0].enable_short
    assert not _patch_run_grid[1].enable_long and _patch_run_grid[1].enable_short

    assert out_md.exists()
    assert out_csv.exists()

    report_text = out_md.read_text(encoding="utf-8")
    assert "LONG" in report_text and "SHORT" in report_text
    assert "GUVENSIZ (n=8)" in report_text  # SHORT hucresi -- SILINMEDI

    csv_df = pd.read_csv(out_csv)
    assert set(csv_df["yon"]) == {"LONG", "SHORT"}
    assert len(csv_df) == 2  # 1 tf x 1 currency x 2 yon


def _run_main_argv(argv: list[str]) -> int:
    return abcd_research.main(argv)


def test_main_limit_symbols_uygulanir(tmp_path, _patch_run_grid):
    out_md = tmp_path / "rapor.md"
    out_csv = tmp_path / "ham.csv"

    rc = _run_main_argv(
        [
            "--symbols", "THYAO,ASELS,TUPRS,KCHOL",
            "--limit-symbols", "2",
            "--tfs", "1D",
            "--currencies", "TRY",
            "--out", str(out_md),
            "--out-csv", str(out_csv),
        ]
    )
    assert rc == 0
    assert out_md.exists()


def test_main_bos_sembol_listesi_hata_donduru(tmp_path, capsys):
    rc = _run_main_argv(
        [
            "--symbols", " , ,",
            "--out", str(tmp_path / "r.md"),
            "--out-csv", str(tmp_path / "c.csv"),
        ]
    )
    assert rc == 1
