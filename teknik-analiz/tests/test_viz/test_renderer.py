"""`tlab/viz/renderer.py` için hedefli testler — Faz 7'de GERÇEK veriyle
render edilirken bulunan 3 hatanın regresyonları + iki temel duman testi +
2026-08-29 görsel-kalite düzeltmesinin (bkz. CLAUDE.md) 2 regresyonu (raw
pid sızıntısı, harmonik köşe etiketleri). Bu modül HESAP yapmadığı (yalnızca
IndicatorResult primitiflerini çizdiği) için repaint_test kapsamı dışıdır;
burada doğrulanan yalnızca "veri doğruysa çıktı figürü de doğru mu" sorusu."""

from __future__ import annotations

import re

import pandas as pd
import pytest

from tests.test_harmonics.fixtures import build_gartley_ohlcv
from tests.test_pairs.fixtures import build_cointegrated_pair
from tests.test_structure.fixtures import build_abcd_ohlcv
from tlab.core.types import Box, IndicatorResult, Level, Line, Marker, Polygon, Timeframe
from tlab.indicators.harmonics.scanner_indicator import HarmonicIndicator, HarmonicParams
from tlab.indicators.pairs.relative_momentum import RelativeMomentumPair, RelativeMomentumParams
from tlab.indicators.structure.price_structure import PriceStructure, PriceStructureParams
from tlab.indicators.structure.swing_fib_abcd import SwingFibABCD, SwingFibABCDParams
from tlab.testing.fixtures import make_trend
from tlab.viz.renderer import (
    _STAGGER_TRIGGER_PX,
    _cap_frozen_channels,
    _declutter_levels,
    _filter_confirmed_patterns,
    _harmonic_price_bounds,
    _latest_per_group,
    _resolve_window_end,
    _stagger_yshifts,
    _x,
    render,
    render_structure_report,
)
from tlab.viz.themes import DARK_TERMINAL, LIGHT_ANALYSIS, fill_color, line_color

_PAIR_PARAMS = RelativeMomentumParams(
    window=40, k=2.0, beta_method="one", beta_window=200, min_periods=200,
    y_symbol="YT", x_symbol="XT",
)


def _rgb(rgba: str) -> tuple[int, int, int]:
    m = re.match(r"rgba?\((\d+),(\d+),(\d+)", rgba)
    assert m is not None, rgba
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def test_generic_render_produces_candlestick_and_subpanels() -> None:
    df = make_trend(n=250, slope=0.1, noise=1.2)
    result = PriceStructure(PriceStructureParams())(df)
    result.symbol = "TEST"
    fig = render(result, df, theme="light")
    trace_types = {t.type for t in fig.data}
    assert "candlestick" in trace_types
    # series_layout iki alt panel istiyor (hacim, macd) -> en az 3 farklı yaxis
    yaxes = {getattr(t, "yaxis", "y") or "y" for t in fig.data}
    assert len(yaxes) >= 3


def test_volume_profile_bars_are_gapless() -> None:
    """Regresyon (2026-08-30, kullanıcı geri bildirimi — referans ekran
    görüntüsüyle kıyaslayınca bizimki 'çok cılız' görünüyordu): vp çubukları
    artık `width=bin_height` ile birbirine BİTİŞİK çizilir (varsayılan
    Plotly `bargap` boşluk bırakırdı), yoğun/dolu bir histogram görünümü
    için."""
    df = make_trend(n=250, slope=0.1, noise=1.2)
    result = PriceStructure(PriceStructureParams())(df)
    result.symbol = "TEST"
    fig = render(result, df, theme="light")
    vp_bar = next(t for t in fig.data if t.type == "bar" and t.name == "Hacim Profili")
    bins = result.series["vp_bins"].to_numpy()
    expected_height = float(bins[1] - bins[0])
    assert vp_bar.width == pytest.approx(expected_height)


def test_panel_frames_drawn_around_each_subplot() -> None:
    """Regresyon (2026-08-30): kullanıcı, referans ekran görüntüsündeki gibi
    her alt panelin (mum+vp, hacim, MACD) KENDİ çerçevesini istedi — eskiden
    yalnızca TÜM figürü saran tek bir dış çerçeve vardı. `_draw_panel_frames`
    her eksen çiftine (xaxis/yaxis, xaxis2/yaxis2, ...) bir dikdörtgen çizer."""
    df = make_trend(n=250, slope=0.1, noise=1.2)
    result = PriceStructure(PriceStructureParams())(df)
    result.symbol = "TEST"
    fig = render(result, df, theme="light")
    n_axis_pairs = len(list(fig.select_xaxes()))
    border_rects = [
        s for s in fig.layout.shapes
        if s.type == "rect" and s.xref == "paper" and s.yref == "paper"
    ]
    # 2026-08-30: `_draw_card_frame` (tüm figürü saran ayrı dış çerçeve)
    # kaldırıldı — referans ekran görüntülerinin hiçbirinde yoktu, yalnızca
    # panel çerçeveleri kaldı.
    assert len(border_rects) == n_axis_pairs


def test_pair_render_draws_holding_period_shading() -> None:
    """Regresyon: `add_vrect(row=...)`, o satıra ilk trace eklenmeden ÖNCE
    çağrılırsa Plotly (7.x) şekli SESSİZCE hiç eklemiyordu — tutulan-dönem
    gölgeleri (Görsel 1) bu yüzden hiç görünmüyordu."""
    df_y, df_x = build_cointegrated_pair()
    result = RelativeMomentumPair(_PAIR_PARAMS)(df_y, context={"x": df_x})
    result.symbol = "YT/XT"
    assert len(result.boxes) > 0  # fixture holding-box üretecek şekilde tasarlandı

    fig = render(result, theme="dark")
    assert len(fig.layout.shapes) >= len(result.boxes)


def test_line_extension_is_capped_not_unbounded() -> None:
    """Regresyon: kısa/dik bir bacağın (ör. harmonik X→B) eğimi ham hâliyle
    grafiğin en son barına kadar projekte edilince fiyat ekseni gerçek dışı
    büyüyordu. Uzatma artık bacağın KENDİ süresinin en fazla 3 katıyla
    sınırlı."""
    df = make_trend(n=200, slope=0.0, noise=0.1, start_price=100.0)
    t0, t1 = df.index[5], df.index[7]  # yalnızca 2 barlık, DİK bir bacak
    result = IndicatorResult(
        indicator="structure.fake_test", version="0.1.0", params_hash="h",
        symbol="TEST", timeframe=Timeframe.D1,
        lines=[
            Line(
                points=((t0, 100.0), (t1, 130.0)), label="dik_bacak",
                style="dashed", extend_right=True,
            )
        ],
    )
    fig = render(result, df, theme="light")
    ext_trace = next(t for t in fig.data if t.name == "dik_bacak_uzatma")
    # Sınırsız (ham eğim * kalan ~193 gün) projeksiyon >2900 verirdi;
    # sınırlı (en fazla 3x bacak süresi = 6 gün) projeksiyon ~190 civarı olmalı.
    assert max(ext_trace.y) < 300


def test_panel_titles_land_on_correct_axis_when_vp_panel_present() -> None:
    """Regresyon (2026-08-30, TCELL'de bulunan GERÇEK bir hata): Plotly eksen
    numaralandırması SATIR-ÖNCELİKLİ ve `specs`teki HER hücreye (None hariç)
    ayrı bir sayı verir — vp paneli varken 1. satır İKİ eksen tüketir (yaxis
    + yaxis2), bu yüzden 2. satırın ("hacim") KENDİ ekseni `yaxis2` DEĞİL,
    `yaxis3`'tür. Bu ayrım gözden kaçırılınca "Hacim" başlığı yanlışlıkla
    vp panelinin (row=1, col=2) üstüne çiziliyordu."""
    df = make_trend(n=200, slope=0.1, noise=1.2)
    ps_result = PriceStructure(PriceStructureParams())(df)
    ps_result.symbol = "TEST"
    sf_result = SwingFibABCD(SwingFibABCDParams())(df)
    sf_result.symbol = "TEST"
    fig = render_structure_report(ps_result, sf_result, df, theme="light")

    hacim_title = next(
        a for a in fig.layout.annotations if "Hacim" in str(a.text) and a.xref == "paper"
    )
    # vp paneli varken "hacim" satırının GERÇEK ekseni yaxis3'tür (yaxis +
    # yaxis2'nin ikisi de row=1'e ait) — domain'i yaxis2'den (vp paneli,
    # row=1, col=2) FARKLI olmalı.
    assert fig.layout.yaxis3.domain != fig.layout.yaxis2.domain
    assert hacim_title.y == pytest.approx(fig.layout.yaxis3.domain[1] - 0.008, abs=1e-6)


def test_generic_breakout_markers_declutter_per_category_not_globally() -> None:
    """Regresyon (2026-08-30, kullanıcı için galeri görselleri üretilirken
    bulundu): `trend.breakouts` (MultiBreakout) TÜM olaylarını AYNI
    kind="breakout" altında yayınlar; gerçek TCELL verisiyle 282 böyle
    marker TEK panelde üst üste binip grafiği tamamen okunmaz kılmıştı.
    Declutter artık `Marker.text`e gömülü kategoriye (break_type) göre HER
    kategoriden yalnızca en güncel örneği gösterir."""
    df = make_trend(n=100, slope=0.0, noise=0.5, start_price=100.0)
    times = df.index
    markers = [
        Marker(
            t=times[i], price=100.0,
            text=f"Kırılım: YUKARI | channel_break_up | Temas:{i} | Hacim ×1.0 | Q:50",
            kind="breakout",
        )
        for i in range(0, 40, 4)
    ] + [
        Marker(
            t=times[i], price=100.0,
            text=f"Kırılım: AŞAĞI | donchian_break_down | Temas:{i} | Hacim ×1.0 | Q:50",
            kind="breakout",
        )
        for i in range(1, 40, 4)
    ]
    result = IndicatorResult(
        indicator="trend.fake_test", version="0.1.0", params_hash="h",
        symbol="TEST", timeframe=Timeframe.D1, markers=markers,
    )
    fig = render(result, df, theme="light")
    # 2026-09-02: görünen metin artık `_short_generic_text` ile kısaltılıyor
    # ("▲ channel_break_up" gibi) — ham "Kırılım: ..." cümlesi artık yalnızca
    # `hovertext`'te. 10 "channel_break_up" + 10 "donchian_break_down" ->
    # declutter yalnızca 2 (kategori başına birer en güncel) bırakmalı.
    breakout_anns = [a for a in fig.layout.annotations if "channel_break_up" in str(a.hovertext)
                      or "donchian_break_down" in str(a.hovertext)]
    assert len(breakout_anns) == 2


def test_golden_zone_success_markers_declutter_to_most_recent() -> None:
    """Regresyon (2026-09-02, kullanıcı geri bildirimi — "hala karışık"):
    önceki tasarım kararı `structure.golden_zone`/`structure.supply_demand`
    marker'larının ("REAKSİYON"/"BAŞARILI"/"BAŞARISIZ"/"KIRILDI") AZ SAYIDA
    olacağını varsayıp declutter'dan MUAF tutuyordu — gerçek ALARK/ASELS
    verisiyle bu varsayım YANLIŞ çıktı (düzinelerce swing'in her biri kendi
    marker'ını üretip üst üste bindi). Artık bu kind'lar da
    `_DECLUTTER_GENERIC_KINDS`'a dahil — yalnızca EN GÜNCEL örnek kalır."""
    df = make_trend(n=100, slope=0.0, noise=0.5, start_price=100.0)
    times = df.index
    markers = [
        Marker(t=times[i], price=100.0, text="BAŞARILI", kind="golden_zone_success")
        for i in range(0, 40, 4)
    ]
    result = IndicatorResult(
        indicator="structure.fake_test", version="0.1.0", params_hash="h",
        symbol="TEST", timeframe=Timeframe.D1, markers=markers,
    )
    fig = render(result, df, theme="light")
    success_anns = [a for a in fig.layout.annotations if a.text == "BAŞARILI"]
    assert len(success_anns) == 1
    assert success_anns[0].x == _x(times[36])


def test_latest_per_group_returns_max_time_per_group() -> None:
    t1, t2, t3 = pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05"), pd.Timestamp("2024-01-10")
    box_a = Box(t0=t1, t1=t2, low=1.0, high=2.0, label="a", style="x")
    box_b = Box(t0=t3, t1=t2, low=1.0, high=2.0, label="b", style="x")
    box_c = Box(t0=t2, t1=t2, low=1.0, high=2.0, label="c", style="y")
    result = _latest_per_group([box_a, box_b, box_c], lambda b: b.style, lambda b: b.t0)
    assert result == {"x": box_b, "y": box_c}


def test_latest_per_group_picks_exactly_one_item_on_tied_time() -> None:
    """Regresyon (2026-09-02, gerçek ISCTR verisiyle bulundu): `trend.
    breakouts`'ta birçok trendline adayı `extend_right=True` ile AYNI son
    bara uzatıldığı için `points[-1][0]` (dolayısıyla eski sürümde `b.t0`
    ile karşılaştırılan DEĞER) çakışıyordu — eskiden ('değer eşitliği')
    ikisi de "en güncel" sayılıp İKİSİ de etiketleniyordu ("uptrend_break
    adayı" iki kez görünüyordu). Artık dönen ÖĞENİN KENDİSİ (kimlik) tek bir
    kazanan seçer."""
    t = pd.Timestamp("2024-01-10")
    box_a = Box(t0=t, t1=t, low=1.0, high=2.0, label="a", style="x")
    box_b = Box(t0=t, t1=t, low=1.0, high=2.1, label="b", style="x")  # label/high FARKLI: != box_a
    result = _latest_per_group([box_a, box_b], lambda b: b.style, lambda b: b.t0)
    assert len(result) == 1
    assert result["x"] is box_b  # liste sırasına göre SONUNCU (>=) kazanır, box_a DEĞİL


def test_declutter_levels_keeps_only_latest_start_per_style() -> None:
    """Kullanıcı geri bildirimi: gerçek çok-yıllık veride her ABC üçlüsünün
    fib merdiveni/D-hedefi üst üste binip grafiği okunmaz kılıyordu.
    `_declutter_levels`, aynı stildeki eski üçlüleri TAMAMEN eler."""
    df = build_abcd_ohlcv()
    result = SwingFibABCD(SwingFibABCDParams(left=2, right=2))(df)
    d_levels_full = [lv for lv in result.levels if lv.style == "bullish"]
    assert len({lv.start for lv in d_levels_full}) >= 2  # fixture 2 üçlü üretir

    reduced = _declutter_levels(result.levels, keep_recent=1)
    d_levels_reduced = [lv for lv in reduced if lv.style == "bullish"]
    assert len({lv.start for lv in d_levels_reduced}) == 1
    assert len(d_levels_reduced) < len(d_levels_full)


def test_stagger_yshifts_separates_mixed_direction_items_by_all_pairs() -> None:
    """Kullanıcı geri bildirimi: ASELS gerçek verisinde "Destek Bölgesi"
    (box, +base, yukarı büyür) / "VAL" (level, +base) / "Destek (Temas:N)"
    (line-uzatma, -base, aşağı büyür) üç etiketi aynı dar fiyat bandında
    (341.88-347.63) toplandığında hâlâ üst üste biniyordu — kök neden:
    `_stagger_yshifts` SALT `price`e göre sıralıyordu, ama `price` sırası
    yalnızca TÜM öğeler AYNI işaretli `base` taşıdığında ekran-konumu
    sırasıyla ÖRTÜŞÜR. Negatif base'li bir öğe (line), raw price'ı daha
    büyük olsa bile n=0 ekran konumu daha KÜÇÜK olabilir — bu durumda eski
    sıralama, bitişik-öncekiyle-kıyasla kontrolünü YANLIŞ komşu çiftine
    uyguluyor, gerçek çakışan çift hiç karşılaştırılmıyordu. Bu test SALT
    ilk/son değil TÜM ikili mesafeleri kontrol eder (bitişik kontrol
    yetersiz kalabileceği için)."""
    px_per_unit = 1.554  # ASELS örneğindeki GERÇEK render'ın kaba tahminiyle aynı mertebe
    val = Level(price=341.88, label="VAL", style="value_area")
    line = Line(points=((pd.Timestamp("2026-07-17"), 344.5),) * 2, label="x", style="support")
    box = Box(t0=pd.Timestamp("2026-07-22"), t1=pd.Timestamp("2026-07-22"),
              low=339.37, high=347.63, label="y", style="support_zone")
    items = [(val, 341.88, 10.0), (line, 344.5, -24.0), (box, 347.63, 10.0)]
    yshifts = _stagger_yshifts(items, px_per_unit=px_per_unit, step=14.0)

    effective = {it: price + yshifts[it] / px_per_unit for it, price, _b in items}
    values = list(effective.values())
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            assert abs(values[i] - values[j]) >= _STAGGER_TRIGGER_PX / px_per_unit - 1e-9


def test_stagger_yshifts_never_escapes_price_bounds() -> None:
    """Regresyon (2026-08-30, gerçek THYAO verisiyle bulundu): `structure.
    report` birleşik grafiğinde çok sayıda öğe (POC/VAH/VAL/D-hedefleri)
    aynı dar banda yığılınca paylaşılan `n` sayacı zaten yüksekken sıradaki
    öğe (VAH) fiyatça görünür eksenin ÜST sınırına yakındı — `_STAGGER_MAX_
    OFFSET_PX`'in SABİT piksel tavanı bunu önleyemedi (aynı piksel bütçesi,
    geniş fiyat aralıklı hisselerde çok daha fazla fiyat birimine karşılık
    geliyor); VAH masthead'in bile üstüne taşmıştı. `price_bounds` verilince
    hiçbir öğenin ekran konumu bu aralığın DIŞINA taşmamalı — TEK adımlık bir
    geri-sarım da YETERSİZDİ (paylaşılan `n` çok yüksekken bir adım geri
    gitmek hâlâ sınırın dışında kalabiliyordu), bu yüzden `n` sınırın İÇİNE
    dönene kadar (ya da 0'a) geri sarılıyor."""
    px_per_unit = 5.48  # THYAO örneğindeki gerçek render'ın kaba tahminiyle aynı mertebe
    bounds = (258.0, 360.0)
    # Önce 6 öğe AYNI fiyatta (paylaşılan `n`'i yüksek zorlar), SONRA sınıra
    # yakın VAH — gerçek THYAO sırasıyla aynı desen.
    pileup = [(f"item_{i}", 320.0, 10.0) for i in range(6)]
    vah = ("VAH", 355.5, 10.0)
    items = [*pileup, vah]

    yshifts = _stagger_yshifts(items, px_per_unit=px_per_unit, step=14.0, price_bounds=bounds)

    for item, price, _base in items:
        effective = price + yshifts[item] / px_per_unit
        assert bounds[0] - 1e-6 <= effective <= bounds[1] + 1e-6, (item, effective)


def test_cap_frozen_channels_keeps_only_most_recent_pairs() -> None:
    """Kullanıcı geri bildirimi: `trend.weekly_channel`'ın dar `n` penceresiyle
    çok-yıllık veride HER dokunuş/kırılım sinyali bir `channel_frozen` çift
    (alt+üst) üretiyordu — onlarca üst üste binen çizgi ("curcuna", TCELL
    örnek grafiğinde bulundu). `_latest_per_group` bu stili yalnızca ETİKET
    düzeyinde kısıtlar (şekiller yine hepsi çizilir) — bu yüzden ayrı, şekil
    düzeyinde bir kesim gerekti."""
    times = [pd.Timestamp(f"2024-01-{d:02d}") for d in (5, 10, 15, 20, 25)]
    frozen = [
        Line(points=((t, 90.0), (t, 110.0)), label=f"channel_frozen_lower_{i}",
             style="channel_frozen", extend_right=False)
        for i, t in enumerate(times)
    ] + [
        Line(points=((t, 95.0), (t, 115.0)), label=f"channel_frozen_upper_{i}",
             style="channel_frozen", extend_right=False)
        for i, t in enumerate(times)
    ]
    other = Line(points=((times[0], 100.0), (times[-1], 100.0)), label="x", style="channel")
    capped = _cap_frozen_channels([*frozen, other])

    assert other in capped
    kept_frozen = [ln for ln in capped if ln.style == "channel_frozen"]
    assert len(kept_frozen) == 4  # son 2 sinyal x (alt+üst)
    assert {ln.points[-1][0] for ln in kept_frozen} == set(times[-2:])


def test_render_declutter_reduces_annotation_count() -> None:
    df = build_abcd_ohlcv()
    result = SwingFibABCD(SwingFibABCDParams(left=2, right=2))(df)
    result.symbol = "TEST"
    fig_full = render(result, df, theme="light", declutter=False)
    fig_declutter = render(result, df, theme="light", declutter=True)
    assert len(fig_declutter.layout.annotations) < len(fig_full.layout.annotations)


def test_fill_and_line_colors_agree_on_direction() -> None:
    """Regresyon: `_FILL_STYLE_COLOR`'da bullish/bearish ters eşlenmişti —
    yeşil çizgili bir boğa üçgeni kırmızı dolgulu görünüyordu."""
    for style, expected_hex in (("bullish", DARK_TERMINAL.green), ("bearish", DARK_TERMINAL.red)):
        line_hex = line_color(DARK_TERMINAL, style)
        assert line_hex == expected_hex
        fill_rgb = _rgb(fill_color(DARK_TERMINAL, style, 0.5))
        expected_rgb = tuple(int(expected_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        assert fill_rgb == expected_rgb


def _render_gartley() -> tuple[IndicatorResult, pd.DataFrame]:
    df = build_gartley_ohlcv()
    params = HarmonicParams(left=2, right=2, confirmation_policy="close_reversal", reversal_bars=1)
    result = HarmonicIndicator("carney", params)(df)
    result.symbol = "TEST"
    return result, df


def test_resolve_window_end_caps_for_old_harmonic_candidate() -> None:
    """Regresyon (2026-08-30, ALARK'ta bulunan bir davranış): eskiden görünür
    pencerenin BİTİŞİ her zaman veri setinin GERÇEK son barıydı — bir aday
    çok eskiyse (o zamandan beri yeni bir aday doğmadıysa) grafiğin çoğu
    boş/düz mumdan oluşan bir görünüm alıyordu. `_resolve_window_end` artık
    adayın kendi ufkuna (`_HARMONIC_END_PAD_BARS` kadar ötesi) kısıtlar."""
    df = make_trend(n=500, slope=0.0, noise=0.5, start_price=100.0)
    result = IndicatorResult(
        indicator="harmonic.fake_test", version="0.1.0", params_hash="h",
        symbol="TEST", timeframe=Timeframe.D1,
        polygons=[
            Polygon(
                points=((df.index[10], 100.0), (df.index[15], 110.0), (df.index[20], 105.0)),
                label="p_xab", style="bullish",
            ),
            Polygon(
                points=((df.index[15], 110.0), (df.index[20], 105.0), (df.index[25], 108.0)),
                label="p_bcd", style="bullish",
            ),
        ],
    )
    end_idx = _resolve_window_end(result, df)
    assert 25 <= end_idx < len(df) - 1


def test_resolve_window_end_uses_last_bar_for_non_harmonic() -> None:
    df = make_trend(n=100, slope=0.1, noise=0.5)
    result = PriceStructure(PriceStructureParams())(df)
    assert _resolve_window_end(result, df) == len(df) - 1


def test_harmonic_price_bounds_includes_offscreen_polygon_points() -> None:
    """Regresyon (2026-08-30, ACSEL'de bulunan GERÇEK bir hata): D hedefi/PRZ
    görünür mum aralığının ÇOK dışında (ör. çok daha aşağıda) kalınca eskiden
    yalnızca mum yüksek/düşüklerini kullanan y-ekseni hesabı bunu hesaba
    katmıyordu — BCD üçgeni ekran dışına taşıp tuhaf bir şekilde kesiliyor,
    D etiketi de görünmez bir y-koordinatına yerleşip ALAKASIZ bir
    noktadaymış gibi görünüyordu."""
    df = make_trend(n=50, slope=0.0, noise=0.5, start_price=100.0)
    result = IndicatorResult(
        indicator="harmonic.fake_test", version="0.1.0", params_hash="h",
        symbol="TEST", timeframe=Timeframe.D1,
        polygons=[
            Polygon(
                points=((df.index[5], 100.0), (df.index[10], 100.0), (df.index[15], 30.0)),
                label="p_bcd", style="bullish",
            ),
        ],
    )
    bounds = _harmonic_price_bounds(result, df, 0, len(df) - 1)
    assert bounds is not None
    low, _high = bounds
    assert low < 30.0  # D hedefi (30) aralığa DAHİL edilmeli, kesilmemeli


def test_harmonic_confirmed_marker_uses_accent_not_generic_bullish() -> None:
    """Regresyon (2026-08-30, kullanıcı geri bildirimi): eskiden pending/
    active/confirmed HEPSİ aynı yeşili ("bullish") alıyordu — invalidated
    HARİÇ — bu yüzden 'sinyal gerçekten geldi mi (confirmed)' sorusunun
    cevabı görsel olarak AYIRT EDİLEMİYORDU. `_render_gartley` fixture'ı
    sonda "confirmed" durumuna ulaşır (bkz. test_harmonics_repaint.py);
    artık bu durum `accent` (marka rengi) alır, jenerik `bullish` yeşili
    DEĞİL."""
    result, df = _render_gartley()
    assert any(m.kind == "harmonic_confirmed" for m in result.markers)
    fig = render(result, df, theme="light")
    harmonic_anns = [a for a in fig.layout.annotations if a.arrowcolor is not None]
    assert any(a.arrowcolor == LIGHT_ANALYSIS.accent for a in harmonic_anns)
    assert not any(a.arrowcolor == LIGHT_ANALYSIS.green for a in harmonic_anns)


def test_prz_band_drawn_as_single_shaded_rect_not_two_lines() -> None:
    """Regresyon (2026-09-01, "Grafik Stil Vitrini" mockup'ıyla birebir
    eşitleme): eskiden PRZ alt/üst iki AYRI kesikli `Level` çizgisi + iki
    ayrı "PRZ Alt"/"PRZ Üst" etiketi olarak çiziliyordu. `_draw_prz_bands`
    artık `_prz_low`/`_prz_high` çiftini TEK bir yarı saydam dolgulu
    dikdörtgen + TEK "Hedef Bölge (PRZ): ..." etiketine indirger."""
    result, df = _render_gartley()
    assert any(lv.label.endswith("_prz_low") for lv in result.levels)
    fig = render(result, df, theme="light")
    prz_shapes = [
        s for s in fig.layout.shapes
        if s.type == "rect" and s.fillcolor is not None and "rgba" in str(s.fillcolor)
        and s.line.color == LIGHT_ANALYSIS.accent
    ]
    assert len(prz_shapes) == 1
    prz_anns = [a for a in fig.layout.annotations if "Hedef Bölge (PRZ)" in str(a.text)]
    assert len(prz_anns) == 1
    assert not any(str(a.text) in ("PRZ Alt", "PRZ Üst") for a in fig.layout.annotations)


def test_harmonic_confirmed_badge_is_solid_filled_not_outline() -> None:
    """Regresyon (2026-09-01, mockup'ın `badgeStyle`'ıyla birebir eşitleme):
    eskiden `confirmed` durumdaki D rozeti bile yalnızca %15 opaklıkta
    dolgu kullanıyordu (ince kenarlıklı, "outline" görünüm). Artık TAM opak
    dolgu (`bgcolor == theme.accent`, `rgba(...)` DEĞİL) + beyaz metin alır
    (light/kagit_raporu temalarında — dark_terminal'da koyu metin, ayrı bir
    kural)."""
    result, df = _render_gartley()
    fig = render(result, df, theme="light")
    d_badges = [
        a for a in fig.layout.annotations
        if a.arrowcolor == LIGHT_ANALYSIS.accent and str(a.text).startswith("<b>D:")
    ]
    assert len(d_badges) == 1
    assert d_badges[0].bgcolor == LIGHT_ANALYSIS.accent
    assert d_badges[0].font.color == "#ffffff"


def test_no_raw_internal_id_in_rendered_annotation_text() -> None:
    """Regresyon (2026-08-29 görsel-kalite düzeltmesi, bkz. CLAUDE.md):
    `_draw_lines`/`_draw_levels` eskiden `Line.label`/`Level.label`'ı
    OLDUĞU GİBİ `text=` olarak basıyordu — harmonik tarayıcıda bu, uzun bir
    dahili kompozit kimlik (`f"{school}_{pattern}_{x_idx}_{a_idx}_{b_idx}_
    {c_idx}_prz_low"` gibi) demekti ve canlı grafikte çıplak "pesavento_g..."
    metni olarak görünüyordu. `_display_text()` artık ya bilinen bir son ek
    üzerinden (`_prz_low`→"PRZ Alt" vb.) ya da `style`'dan kısa bir Türkçe
    metin türetiyor; hiçbir grafik-üzerindeki (Level/Line/Marker kaynaklı)
    annotation metni ekol/pattern/pattern_id parçalarını (`carney`,
    `gartley`, `pattern_id`'nin alt çizgili indeks yığını gibi) HAM olarak
    içermemeli. `xref="paper"` olan masthead annotation'ları (2026-08-29
    tasarım geçişi, bkz. CLAUDE.md — `_draw_header`'ın alt başlığı MEŞRU
    olarak "Sistem: Carney" gibi okunur bir cümle içerir) bu denetimin
    KAPSAMI DIŞINDA — onlar ham bir dahili kimlik değil, kasıtlı Türkçe
    rapor metni."""
    result, df = _render_gartley()
    fig = render(result, df, theme="light")
    raw_id_fragments = ("carney", "pesavento", "gartley", "pattern_id")
    for ann in fig.layout.annotations:
        if ann.xref == "paper" and ann.yref == "paper":
            continue  # masthead/dipnot — bkz. docstring
        text_lower = str(ann.text).lower()
        for fragment in raw_id_fragments:
            assert fragment not in text_lower, f"ham kimlik sızıntısı: {ann.text!r}"
        # Ham kimlikler alt çizgi ağırlıklı, boşluksuz uzun dizeler biçiminde
        # olur (ör. "carney_gartley_5_10_15_20_prz_low") — kısa/okunur
        # etiketler ("PRZ Alt", "X-B", "Direnç (Temas:6)") bu deseni taşımaz.
        assert not (" " not in str(ann.text) and str(ann.text).count("_") >= 2), ann.text


def test_harmonic_vertices_labeled_for_recent_candidate() -> None:
    """Regresyon (2026-08-29): eskiden yalnızca son "D: fiyat [DURUM]"
    etiketi vardı — XAB/BCD üçgenlerinin gerçek pivotları (X, A, B, C) hiç
    işaretlenmiyordu. `_draw_harmonic_vertices` artık en güncel adayların
    her köşesine küçük bir nokta + harf etiketi ekliyor (D hariç — o zaten
    `_draw_markers`'ın "D: ..." kutusunda var, burada TEKRAR edilmiyor)."""
    result, df = _render_gartley()
    fig = render(result, df, theme="light")
    vertex_texts = [ann.text for ann in fig.layout.annotations if ann.text in ("X", "A", "B", "C")]
    assert {"X", "A", "B", "C"} <= set(vertex_texts)
    # D noktası burada tekrar EKLENMEMELİ (yalnızca "D: fiyat [...]" formunda,
    # tek başına "D" harfi olarak DEĞİL).
    assert "D" not in vertex_texts


def test_render_structure_report_combines_both_indicators() -> None:
    """`structure.report` (2026-08-30) — `structure.price_structure` +
    `structure.swing_fib_abcd`'i TEK figürde birleştirir (mum + vp paneli +
    hacim/MACD/RSI alt panelleri). **2026-08-30 ikinci düzeltme**: kullanıcı
    grafiğin İÇİNDEKİ "Özet Raporu" metin sütununu istemedi — anlatı artık
    görselin DIŞINDA, ayrı bir LLM metni olarak üretiliyor (bkz. `tlab/viz/
    quant_report.py`); bu yüzden bu test artık yalnızca GÖRSEL birleşimi
    (mum + swing etiketleri + RSI paneli) doğrular, rapor metnini DEĞİL."""
    df = make_trend(n=250, slope=0.1, noise=1.2)
    ps_result = PriceStructure(PriceStructureParams())(df)
    ps_result.symbol = "TEST"
    sf_result = SwingFibABCD(SwingFibABCDParams())(df)
    sf_result.symbol = "TEST"

    fig = render_structure_report(ps_result, sf_result, df, theme="light")

    trace_types = {t.type for t in fig.data}
    assert "candlestick" in trace_types
    # swing_fib_abcd'in HH/HL/LH/LL marker'ları birleşik figürde de görünmeli.
    structure_labels = {
        ann.text for ann in fig.layout.annotations if ann.text in ("HH", "HL", "LH", "LL")
    }
    assert structure_labels  # en az bir swing etiketi
    # RSI paneli (`series_layout`'a `render_structure_report`'tan ÖNCE,
    # `PriceStructure.compute()`'a eklendi) üçüncü alt panel olarak var.
    assert "rsi" in ps_result.series_layout


def test_filter_confirmed_patterns_drops_invalidated_keeps_confirmed() -> None:
    """Faz 8B (`patterns.*`) — kullanıcı geri bildirimi: "geçersiz olan
    denemeler gösterilmemeli, sadece tam olarak obo/tobo olan noktalar
    gösterilmeli". İki pattern_id: biri confirmed (tutulmalı, Line/Level/
    vertex/outcome marker'ıyla birlikte), biri invalidated (TAMAMEN
    budanmalı — Line/Level/vertex/outcome marker'ı dahil)."""
    ts = pd.Timestamp("2024-01-10", tz="Europe/Istanbul")
    result = IndicatorResult(
        indicator="patterns.head_shoulders", version="0.1.0", params_hash="x",
        symbol="TEST", timeframe=Timeframe.D1,
        lines=[
            Line(
                points=((ts, 100.0), (ts, 101.0)), label="tobo_ok_neckline",
                style="pattern_boundary",
            ),
            Line(
                points=((ts, 90.0), (ts, 91.0)), label="tobo_bad_neckline",
                style="pattern_boundary",
            ),
        ],
        levels=[
            Level(price=110.0, label="tobo_ok_target", style="pattern_target"),
            Level(price=80.0, label="tobo_bad_target", style="pattern_target"),
        ],
        markers=[
            Marker(t=ts, price=100.0, text="SAĞ OMUZ", kind="pattern_vertex:tobo_ok"),
            Marker(t=ts, price=90.0, text="SAĞ OMUZ", kind="pattern_vertex:tobo_bad"),
            Marker(t=ts, price=102.0, text="TOBO [ONAY]", kind="pattern_confirmed:tobo_ok"),
            Marker(t=ts, price=79.0, text="TOBO [GEÇERSİZ]", kind="pattern_invalidated"),
        ],
        last_state={
            "tobo_ok": {"state": "confirmed"},
            "tobo_bad": {"state": "invalidated"},
        },
    )
    filtered = _filter_confirmed_patterns(result)
    assert [ln.label for ln in filtered.lines] == ["tobo_ok_neckline"]
    assert [lv.label for lv in filtered.levels] == ["tobo_ok_target"]
    assert {m.kind for m in filtered.markers} == {"pattern_vertex:tobo_ok", "pattern_confirmed:tobo_ok"}


def test_filter_confirmed_patterns_matches_either_direction_for_wedge_style_ids() -> None:
    """`wedge.py`/`broadening.py`'de Line etiketi YÖNSÜZ bir `pattern_key`
    kullanır ama `last_state` anahtarı yön soneki taşır (`{pattern_key}_long`/
    `_short`) — bir yön onaylanmışsa (sym_triangle her iki yönü de dener)
    paylaşılan çizgi şekli GÖSTERİLMELİ, diğer (short) yön yine de
    last_state'te ayrı kalsa bile."""
    ts = pd.Timestamp("2024-01-10", tz="Europe/Istanbul")
    result = IndicatorResult(
        indicator="patterns.wedge", version="0.1.0", params_hash="x",
        symbol="TEST", timeframe=Timeframe.D1,
        lines=[
            Line(
                points=((ts, 100.0), (ts, 101.0)), label="wedge_5_10_15_20_upper",
                style="pattern_boundary",
            ),
        ],
        last_state={
            "wedge_5_10_15_20_long": {"state": "confirmed"},
            "wedge_5_10_15_20_short": {"state": "invalidated"},
        },
    )
    filtered = _filter_confirmed_patterns(result)
    assert len(filtered.lines) == 1


def test_filter_confirmed_patterns_target_level_stays_direction_specific() -> None:
    """2026-09-03 GERÇEK bulgu (ODAS `patterns.triangle` render'ı): yön
    soneki kırpılmış `pattern_key` eşleşmesi paylaşılan Line/Polygon için
    doğru olsa da, `_target` Level'i YÖNE ÖZGÜdür (`{pattern_key}_{direction}
    _target`) — geçersiz (short) yönün hedef fiyatı, kırpılmış base'e göre
    yanlışlıkla geçerli (long) yönle eşleşip başıboş bir "Hedef" çizgisi
    olarak sızmamalı."""
    result = IndicatorResult(
        indicator="patterns.triangle", version="0.1.0", params_hash="x",
        symbol="TEST", timeframe=Timeframe.D1,
        levels=[
            Level(price=110.0, label="triangle_5_10_15_20_long_target", style="pattern_target"),
            Level(price=80.0, label="triangle_5_10_15_20_short_target", style="pattern_target"),
        ],
        last_state={
            "triangle_5_10_15_20_long": {"shape": "sym_triangle", "state": "confirmed"},
            "triangle_5_10_15_20_short": {"shape": "sym_triangle", "state": "invalidated"},
        },
    )
    filtered = _filter_confirmed_patterns(result)
    assert [lv.label for lv in filtered.levels] == ["triangle_5_10_15_20_long_target"]
