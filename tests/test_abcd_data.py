"""src/fetchers/abcd_data.py testleri.

Kural 11: gercek ag istegi ATILMAZ -- `abcd_data._yf_history` (bu modulun
yfinance'e dokundugu TEK nokta) monkeypatch ile sahte yfinance ciktisi
doner. Onbellek testleri de gercek proje veri klasorune YAZMAZ --
`abcd_data._CACHE_DIR` her testte `tmp_path` altina yonlendirilir.
"""

from __future__ import annotations

import pandas as pd

from src.fetchers import abcd_data


def _fake_yf_frame(times: list, opens: list, highs: list, lows: list, closes: list, volumes: list) -> pd.DataFrame:
    """yfinance.Ticker(...).history()'nin dondurdugu sekle benzer bir
    DataFrame uretir: tz-aware DatetimeIndex + Open/High/Low/Close/Volume."""
    index = pd.DatetimeIndex(times, name="Datetime")
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=index,
    )


def test_fetch_ohlcv_abcd_bist_sembolune_is_eki_ekler(monkeypatch, tmp_path):
    monkeypatch.setattr(abcd_data, "_CACHE_DIR", tmp_path)
    captured = {}

    def _fake_history(yf_symbol, interval, period):
        captured["yf_symbol"] = yf_symbol
        captured["interval"] = interval
        times = pd.date_range("2026-08-10", periods=3, freq="1D", tz=abcd_data.TZ_ISTANBUL)
        return _fake_yf_frame(times, [10, 11, 12], [11, 12, 13], [9, 10, 11], [10.5, 11.5, 12.5], [1000, 1100, 1200])

    monkeypatch.setattr(abcd_data, "_yf_history", _fake_history)

    result = abcd_data.fetch_ohlcv_abcd("THYAO", "1D")

    assert captured["yf_symbol"] == "THYAO.IS"
    assert captured["interval"] == "1d"
    assert list(result.columns) == abcd_data.OHLCV_COLUMNS
    assert len(result) == 3


def test_fetch_usdtry_is_eki_EKLEMEZ(monkeypatch, tmp_path):
    """USDTRY=X sembolune -- BIST hisselerinin aksine -- .IS eki eklenmemeli."""
    monkeypatch.setattr(abcd_data, "_CACHE_DIR", tmp_path)
    captured = {}

    def _fake_history(yf_symbol, interval, period):
        captured["yf_symbol"] = yf_symbol
        times = pd.date_range("2026-08-10", periods=2, freq="1D", tz=abcd_data.TZ_ISTANBUL)
        return _fake_yf_frame(times, [32.0, 32.1], [32.2, 32.3], [31.9, 32.0], [32.1, 32.2], [0, 0])

    monkeypatch.setattr(abcd_data, "_yf_history", _fake_history)

    result = abcd_data.fetch_usdtry("1D")

    assert captured["yf_symbol"] == "USDTRY=X"
    assert list(result.columns) == abcd_data.USDTRY_COLUMNS
    assert len(result) == 2


def test_resample_to_hours_origin_09_00_istanbul_a_sabitlenir():
    """abcd-project'in canli TradingView dogrulamasi: BIST 4H barlari
    09:00/13:00/17:00'da acilir. yfinance'in 09:30'dan baslayan 1H
    barlari resample edildiginde, ilk kovanin etiketi 09:00 olmalidir
    (10:00 DEGIL), boylece gunun sonraki her 4H bari TradingView ile
    tam eslesir (bkz. modul ust notu)."""
    tz = abcd_data.TZ_ISTANBUL
    times = pd.to_datetime(
        [
            "2026-08-10 09:30",
            "2026-08-10 10:30",
            "2026-08-10 11:30",
            "2026-08-10 12:30",
            "2026-08-10 13:30",
            "2026-08-10 14:30",
        ]
    ).tz_localize(tz)
    df = pd.DataFrame(
        {
            "time": times,
            "open": [10, 11, 12, 13, 14, 15],
            "high": [11, 12, 13, 14, 15, 16],
            "low": [9, 10, 11, 12, 13, 14],
            "close": [10.5, 11.5, 12.5, 13.5, 14.5, 15.5],
            "volume": [100, 100, 100, 100, 100, 100],
        }
    )

    result = abcd_data._resample_to_hours(df, hours=4)

    assert result.iloc[0]["time"].hour == 9
    assert result.iloc[0]["time"].minute == 0
    assert result.iloc[1]["time"].hour == 13
    # Ilk kovan [09:00, 13:00) -> ilk 4 bar (09:30..12:30): open=ilk barin open'i (10), close=son barin close'u (13.5)
    assert result.iloc[0]["open"] == 10
    assert result.iloc[0]["close"] == 13.5


def test_fetch_ohlcv_abcd_parquet_onbellek_dogru_path_te_olusur(monkeypatch, tmp_path):
    monkeypatch.setattr(abcd_data, "_CACHE_DIR", tmp_path)

    def _fake_history(yf_symbol, interval, period):
        times = pd.date_range("2026-08-10", periods=5, freq="1D", tz=abcd_data.TZ_ISTANBUL)
        return _fake_yf_frame(
            times, [10, 11, 12, 13, 14], [11, 12, 13, 14, 15], [9, 10, 11, 12, 13],
            [10.5, 11.5, 12.5, 13.5, 14.5], [100, 100, 100, 100, 100],
        )

    monkeypatch.setattr(abcd_data, "_yf_history", _fake_history)

    abcd_data.fetch_ohlcv_abcd("THYAO", "1D", n_bars=5)

    expected_path = tmp_path / "THYAO_1D.parquet"
    assert expected_path.exists()
    cached = pd.read_parquet(expected_path)
    assert len(cached) == 5
    assert list(cached.columns) == abcd_data.OHLCV_COLUMNS


def test_fetch_usdtry_onbellek_usdtry_onekiyle_olusur(monkeypatch, tmp_path):
    monkeypatch.setattr(abcd_data, "_CACHE_DIR", tmp_path)

    def _fake_history(yf_symbol, interval, period):
        times = pd.date_range("2026-08-10", periods=2, freq="1D", tz=abcd_data.TZ_ISTANBUL)
        return _fake_yf_frame(times, [32.0, 32.1], [32.2, 32.3], [31.9, 32.0], [32.1, 32.2], [0, 0])

    monkeypatch.setattr(abcd_data, "_yf_history", _fake_history)

    abcd_data.fetch_usdtry("1D")

    assert (tmp_path / "USDTRY_1D.parquet").exists()


def test_fetch_ohlcv_abcd_ag_hatasinda_bos_dataframe_doner_firlatmaz(monkeypatch, tmp_path):
    monkeypatch.setattr(abcd_data, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(abcd_data._time, "sleep", lambda *_: None)  # retry backoff'unu bekletme

    def _raise(yf_symbol, interval, period):
        raise ConnectionError("ag hatasi (test)")

    monkeypatch.setattr(abcd_data, "_yf_history", _raise)

    result = abcd_data.fetch_ohlcv_abcd("THYAO", "1D")

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert list(result.columns) == abcd_data.OHLCV_COLUMNS


def test_fetch_usdtry_ag_hatasinda_bos_dataframe_doner_firlatmaz(monkeypatch, tmp_path):
    monkeypatch.setattr(abcd_data, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(abcd_data._time, "sleep", lambda *_: None)

    def _raise(yf_symbol, interval, period):
        raise ConnectionError("ag hatasi (test)")

    monkeypatch.setattr(abcd_data, "_yf_history", _raise)

    result = abcd_data.fetch_usdtry("240")

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert list(result.columns) == abcd_data.USDTRY_COLUMNS


def test_fetch_ohlcv_abcd_bos_yfinance_yaniti_bos_dataframe_doner(monkeypatch, tmp_path):
    monkeypatch.setattr(abcd_data, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(abcd_data, "_yf_history", lambda yf_symbol, interval, period: pd.DataFrame())

    result = abcd_data.fetch_ohlcv_abcd("YOKHISSE", "1D")

    assert result.empty
    assert list(result.columns) == abcd_data.OHLCV_COLUMNS


def test_fetch_ohlcv_abcd_desteklenmeyen_zaman_dilimi_bos_dataframe_doner(tmp_path, monkeypatch):
    monkeypatch.setattr(abcd_data, "_CACHE_DIR", tmp_path)

    result = abcd_data.fetch_ohlcv_abcd("THYAO", "5m")

    assert result.empty
    assert list(result.columns) == abcd_data.OHLCV_COLUMNS
