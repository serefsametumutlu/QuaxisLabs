"""tlab Tarama Panosu — Streamlit uygulaması.

Çalıştırma: `tlab dashboard` (kısayol) ya da doğrudan
`streamlit run tlab/dashboard.py`.

Bu dosya HESAP YAPMAZ — `tlab/scanner/` (tarama + SQLite `ResultsStore`)
ve `tlab/viz/live.py::render_live` (grafik) üzerine ince bir sunum
katmanıdır. Amaç: "her gün kapanışta tara, hangi hisselerde hangi
stratejiden sinyal geldiğini tek ekranda gör, tıkla-grafiği-gör" akışı —
CLI (`tlab eod`/`tlab signals`/`tlab report`) hâlâ geçerli ve bu sayfanın
ALTINDA kullandığı aynı altyapı; bu sayfa yalnızca ona kolay erişim katar.

Tasarım kararları:
- `signals` tablosu HER durumu (pending/confirmed/retest_hold/completed/
  invalidated/expired) ayrı bir satır olarak tutar (non-repaint geçmiş) —
  bu ekran, her (sembol, tf, indikatör, pattern_id) zinciri için yalnızca
  EN GÜNCEL (`detected_at` en büyük) satırı gösterir: "şu an nerede"
  sorusuna cevap, "tüm geçmiş" değil (o CLI'daki `tlab signals`'ta).
- Varsayılan filtre yalnızca confirmed/completed (gerçekten "sinyal
  geldi" sayılan) durumları gösterir — "Tüm durumları göster" ile
  pending/invalidated/expired da açılabilir (hata ayıklama/merak amaçlı).
- SQLite bağlantısı HER script koşusunda TAZE açılıp kapanır
  (`st.cache_resource` KULLANILMAZ) — Streamlit'in çoklu-oturum/thread
  modeli sqlite3 bağlantılarını thread'ler arası paylaştırmayı
  YASAKLAR; açma/kapama maliyeti bu ölçekte (yerel SQLite, tek kullanıcı)
  ihmal edilebilir.
- "Son kaç gün" penceresi (varsayılan 5) ZORUNLU bir gerçeklik kontrolü:
  `trend.breakouts` gibi yüksek frekanslı indikatörler yıllar boyunca
  BİRİKMİŞ yüzlerce/binlerce zincir üretir (ör. 80 sembollük küçük bir
  taramada bile TÜM zamanların confirmed/completed sayısı onbinleri
  bulabiliyor — gerçek veriyle ilk denemede bulunan bir kullanılabilirlik
  sorunu) — pencere olmadan "Aktif Sinyal" metriği ve tablo anlamsız
  kalabalıklaşıyordu. Pencere, run'ın KENDİ en güncel `bar_time`'ına göre
  hesaplanır (bugünün tarihine değil — geçmiş bir run'ı incelerken de
  doğru çalışır).

2026-09-01 eklentileri ("Grafik Stil Vitrini" mockup'ının gerçek koda
aktarımı, Faz 1):
- **Tema seçici** (sidebar) — 3 tasarım dili (`Theme` — bkz. `viz/
  themes.py`): Klasik Beyaz Rapor (`light`), Terminal Koyu (`dark`),
  Kağıt Rapor (`paper`, opsiyonel üçüncü seçenek). Sayfadaki HER
  `render_live` çağrısına geçirilir — önceden hiçbiri geçmiyordu, her
  zaman modun kendi varsayılanını (pair->dark, diğerleri->light)
  kullanıyordu.
- **Ayrı ayrı tarama** — "Bugünü Tara" artık İKİ moda ayrıldı: Tam Tarama
  (mevcut davranış, `CATALOG`'daki HER gösterge) ve `config/scans.yaml`
  preset'lerinden biriyle SINIRLI bir tarama (`run_eod(...,
  indicator_names=preset_indicators)`) — kullanıcı yalnızca ilgilendiği
  formasyon türünü (ör. "Boynu kırarak onaylanan TOBO/OBO") tarayabilir,
  tüm evren × tüm gösterge kombinasyonunu beklemek zorunda kalmadan.
  `_load_scan_preset` CLI'nın (`tlab/cli.py`) KENDİ fonksiyonu — burada
  yeniden yazılmadı, doğrudan içe aktarılıp paylaşılıyor.
- **Taramalar listesi** artık bir tablo (`st.dataframe`) — tarih, piyasa,
  sembol sayısı, gösterge sayısı (Tam mı preset mi olduğunu ayırt eder),
  durum; satır seçimi o run'ı aktif hâle getirir (eski çıplak `selectbox`
  yerine).
- **"Grafiğini Seç"** bölümü artık sinyal listesinden BAĞIMSIZ, her zaman
  görünür bir birincil akış (eski "Hızlı bakış" expander'ı kaldırıldı) —
  bir sinyal satırı seçilirse sembol/gösterge/tf ORADAN ön-doldurulur,
  ama her zaman elle değiştirilebilir; gösterge seçimi kategoriye göre
  gruplanmış görünür (mockup'taki Fiyat Formasyonları/Pair Trading/Evren-
  Momentum/Trend dört grubuyla aynı).
- Grafiğin altında **okuma rehberi** (`labels_tr.py::signal_reading`) —
  Nereye Bak / Ne Ölçer / Değerler Ne Demek / AL Sinyali — dört bölüm,
  Plotly figürüne GÖMÜLMEZ (2026-08-30'daki AI rapor kararıyla AYNI ilke).
- `structure.report` seçiliyken bir "🤖 Yapay Zeka Raporu Oluştur" butonu
  belirir (`quant_report.generate_quant_report` — bu fazda yalnızca bu
  gösterge için, kalan 14 gösterge türüne genişletmek ayrı bir iştir,
  bkz. proje planı)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from tlab.cli import _load_scan_preset
from tlab.indicators.bootstrap import CATALOG
from tlab.scanner.eod import run_eod
from tlab.scanner.results import DiffReport, ResultsStore, RunRecord
from tlab.viz.labels_tr import INDICATOR_CATEGORY_TR, signal_reading, tr_direction, tr_state
from tlab.viz.live import STRUCTURE_REPORT_NAME, compute_structure_report
from tlab.viz.live import render_live as _render_live
from tlab.viz.quant_report import generate_quant_report

_ACTIONABLE_STATES = ("confirmed", "completed")

_DISPLAY_COLS = [
    "Sembol", "Kategori", "İndikatör", "Zaman Dilimi", "Yön", "Durum", "Olay", "Sinyal Zamanı",
]

_THEME_OPTIONS: dict[str, str] = {
    "Klasik Beyaz Rapor": "light",
    "Terminal Koyu": "dark",
    "Kağıt Rapor": "paper",
}

_READING_LABELS: tuple[tuple[str, str], ...] = (
    ("watch", "🔎 Nereye Bak"), ("measures", "📐 Ne Ölçer"),
    ("values", "📊 Değerler Ne Demek"), ("signal", "📈 AL Sinyali Ne Zaman Oluşur"),
)


def _category_of(indicator: str) -> str:
    spec = CATALOG.get(indicator)
    category = spec.category if spec is not None else indicator.split(".", 1)[0]
    return INDICATOR_CATEGORY_TR.get(category, category)


def _rows_to_frame(rows: list[dict]) -> pd.DataFrame:
    """Ham `signals` satırlarını (her durum geçişi AYRI bir satır) her
    (symbol, timeframe, indicator, pattern_id) zinciri için TEK, EN GÜNCEL
    satıra indirger — bkz. modül docstring'i."""
    if not rows:
        return pd.DataFrame(
            columns=[
                "symbol", "timeframe", "indicator", "pattern_id", "direction", "state",
                "score", "bar_time", "detected_at", "event",
            ]
        )
    df = pd.DataFrame(rows)
    df["event"] = df["payload_json"].apply(lambda raw: json.loads(raw).get("event", ""))
    df = df.sort_values("detected_at", ascending=False)
    df = df.drop_duplicates(subset=["symbol", "timeframe", "indicator", "pattern_id"], keep="first")
    return df.reset_index(drop=True)


def _to_display(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "Sembol": df["symbol"],
            "Kategori": df["indicator"].map(_category_of),
            "İndikatör": df["indicator"],
            "Zaman Dilimi": df["timeframe"],
            "Yön": df["direction"].map(tr_direction),
            "Durum": df["state"].map(tr_state),
            "Olay": df["event"],
            "Sinyal Zamanı": df["bar_time"].str.slice(0, 16).str.replace("T", " "),
        }
    )
    return out


def _format_run_label(run_id: str) -> str:
    # run_id biçimi "{market}_{YYYY-MM-DD}" (bkz. eod.py) — kullanıcıya
    # yalnızca tarihi göstermek yeterli ve daha okunur.
    return run_id.split("_", 1)[-1] if "_" in run_id else run_id


_SCANS_YAML_PATH = Path(__file__).resolve().parent.parent / "config" / "scans.yaml"


def _load_presets() -> dict[str, str]:
    """`config/scans.yaml`'daki preset adlarını Türkçe açıklamalarıyla
    döner (`{preset_adı: açıklama}`) — sıralı gösterim için kullanılır.

    Yol paket köküne göre MUTLAK çözülür (CWD'ye göre DEĞİL) — `_load_scan_
    preset` (cli.py) varsayılan olarak CWD-göreli bir yol kullanır (kullanıcı
    normalde `tlab`'i proje kökünden çalıştırdığı için sorun olmaz), ama bu
    dosya `st.cache_resource` kullanmadığı ve testler (`tests/
    test_dashboard.py`) izolasyon için CWD'yi değiştirdiği için burada
    CWD'den bağımsız olmak GEREKİR."""
    if not _SCANS_YAML_PATH.exists():
        return {}
    raw = yaml.safe_load(_SCANS_YAML_PATH.read_text(encoding="utf-8")) or {}
    presets = raw.get("presets") or {}
    return {name: cfg.get("description", name) for name, cfg in presets.items()}


def _render_header_metrics(
    run_record: RunRecord | None, df_actionable: pd.DataFrame, diff: DiffReport | None,
) -> None:
    cols = st.columns(4)
    cols[0].metric("Tarama Tarihi", _format_run_label(run_record.run_id) if run_record else "—")
    cols[1].metric("Taranan Sembol", run_record.universe_size if run_record else "—")
    cols[2].metric("Aktif Sinyal", len(df_actionable))
    cols[3].metric("Yeni Sinyal", len(diff.new_signals) if diff is not None else "—")


def _render_repaint_alarm(diff: DiffReport | None) -> None:
    if diff is not None and diff.has_repaint_alarm:
        st.error(
            f"⚠ REPAINT ALARMI: {len(diff.missing_signals)} sinyal önceki taramada vardı, "
            "bu taramada YOK. Bu normalde OLMAMASI gereken bir durumdur — bkz. `tlab diff`.",
            icon="🚨",
        )


def _run_scan(market: str, force: bool, indicator_names: list[str] | None, label: str) -> None:
    spinner_msg = (
        "Taranıyor... (evren büyükse birkaç dakika sürebilir)" if indicator_names is None
        else f"'{label}' taraması çalışıyor..."
    )
    with st.spinner(spinner_msg):
        report = run_eod(market=market, force=force, indicator_names=indicator_names)
    status = report.get("status")
    if status == "completed":
        st.success(
            f"Tarama tamamlandı: {report['n_results']} sonuç, "
            f"{report.get('n_new_signals') or 0} yeni sinyal."
        )
    elif status == "skipped_existing":
        st.info(
            "Bugün için zaten tamamlanmış bir tarama var "
            "(yeniden koşmak için 'force'u işaretleyin)."
        )
    elif status == "skipped_holiday":
        st.info("Bugün işlem günü değil, tarama atlandı.")
    else:
        st.warning(f"Durum: {status}")


def _indicator_options() -> list[tuple[str, str]]:
    """(görüntü_etiketi, katalog_anahtarı) listesi, kategoriye göre
    gruplanmış sırayla — `structure.report` (CATALOG'da YOK, `live.py`'nin
    özel bileşik görünümü) "Fiyat Yapısı" kategorisinin başına eklenir."""
    items = [
        (f"{INDICATOR_CATEGORY_TR.get(spec.category, spec.category)} · {key}", key)
        for key, spec in CATALOG.items()
    ]
    report_label = f"{INDICATOR_CATEGORY_TR['structure']} · {STRUCTURE_REPORT_NAME} (Birleşik)"
    items.append((report_label, STRUCTURE_REPORT_NAME))
    return sorted(items)


def _render_reading_guide(indicator: str) -> None:
    reading = signal_reading(indicator)
    if reading is None:
        return
    st.markdown("##### 📖 Nasıl Okunur")
    cols = st.columns(2)
    for i, (key, label) in enumerate(_READING_LABELS):
        with cols[i % 2]:
            st.markdown(f"**{label}**")
            st.caption(reading[key])


def _render_ai_report_button(symbol: str, timeframe: str, market: str) -> None:
    if st.button("🤖 Yapay Zeka Raporu Oluştur", key="ai_report_btn"):
        with st.spinner("Rapor üretiliyor..."):
            ps_result, sf_result, df = compute_structure_report(symbol, timeframe, market)
            report = generate_quant_report(ps_result, sf_result, df, symbol=symbol)
        if report.used_ai:
            st.markdown(report.text)
        else:
            st.info(f"AI sağlayıcısı kullanılamadı ({report.note}) — deterministik özet:")
            st.markdown(report.text)


def main() -> None:
    st.set_page_config(page_title="tlab Tarama Panosu", layout="wide", page_icon="📊")
    st.title("📊 tlab Tarama Panosu")

    with st.sidebar:
        st.header("Kontroller")
        market = st.selectbox("Piyasa", ["bist", "nasdaq"], index=0)

        st.divider()
        st.subheader("🎨 Görsel Tema")
        theme_choice = st.radio("Tasarım", list(_THEME_OPTIONS.keys()), index=0)
        theme = _THEME_OPTIONS[theme_choice]

        st.divider()
        st.subheader("🔍 Tarama Çalıştır")
        force = st.checkbox("Zorla yeniden tara", value=False)
        if st.button("Tam Tarama (Tüm Göstergeler)", width="stretch", type="primary"):
            _run_scan(market, force, indicator_names=None, label="Tam Tarama")
            st.rerun()
        st.caption("veya yalnızca belirli bir tarama türünü çalıştır:")
        presets = _load_presets()
        if presets:
            preset_key = st.selectbox(
                "Tarama Türü", list(presets.keys()), format_func=lambda k: presets[k],
            )
            if st.button("▶ Bu Taramayı Çalıştır", width="stretch"):
                names, _filt = _load_scan_preset(preset_key, path=str(_SCANS_YAML_PATH))
                _run_scan(market, force, indicator_names=names, label=presets[preset_key])
                st.rerun()

        st.divider()
        st.subheader("📋 Taramalar")
        with ResultsStore() as store:
            run_ids = store.list_runs(market, status="completed")
        if not run_ids:
            st.info("Henüz tamamlanmış bir tarama yok — yukarıdaki butonlarla ilk taramayı başlat.")
            st.stop()
        with ResultsStore() as store:
            run_records = [r for r in (store.get_run(rid) for rid in run_ids) if r is not None]
        runs_df = pd.DataFrame(
            {
                "Tarih": [_format_run_label(r.run_id) for r in run_records],
                "Sembol": [r.universe_size for r in run_records],
                "Gösterge": [len(r.indicator_names) for r in run_records],
                "Kapsam": [
                    "Tam" if len(r.indicator_names) >= len(CATALOG) else "Kısmi"
                    for r in run_records
                ],
            }
        )
        run_event = st.dataframe(
            runs_df, hide_index=True, width="stretch",
            on_select="rerun", selection_mode="single-row", key="run_table",
        )
        selected_run_rows = (
            list(run_event.selection.rows) if run_event and run_event.selection else []
        )
        run_id = run_ids[selected_run_rows[0]] if selected_run_rows else run_ids[0]

        st.divider()
        categories = sorted({spec.category for spec in CATALOG.values()})
        selected_categories = st.multiselect(
            "Kategori", categories,
            default=categories,
            format_func=lambda c: INDICATOR_CATEGORY_TR.get(c, c),
        )
        show_all_states = st.checkbox(
            "Tüm durumları göster (beklemede/geçersiz dahil)", value=False,
        )
        direction_choice = st.radio("Yön", ["Hepsi", "long", "short"], horizontal=True)
        recency_days = st.slider(
            "Son kaç gün", min_value=1, max_value=60, value=5,
            help=(
                "trend.breakouts gibi yüksek frekanslı indikatörler yıllar "
                "boyunca birikmiş yüzlerce zincir üretir — bu pencere yalnızca "
                "SON N gün içinde bir durum değişikliği yaşanan zincirleri "
                "gösterir (her zincirin KENDİ tarihçesi bozulmaz, yalnızca "
                "'şu an hâlâ tazedir' filtresi)."
            ),
        )

    with ResultsStore() as store:
        run_record = store.get_run(run_id)
        rows = store.query(run_id=run_id)
        other_runs = [r for r in store.list_runs(market, status="completed") if r != run_id]
        diff = store.diff(other_runs[0], run_id) if other_runs else None

    df_all = _rows_to_frame(rows)
    if not df_all.empty:
        bar_times = pd.to_datetime(df_all["bar_time"], utc=True)
        cutoff = bar_times.max() - pd.Timedelta(days=recency_days)
        df_all = df_all[bar_times >= cutoff]

    df_actionable = df_all[df_all["state"].isin(_ACTIONABLE_STATES)]
    _render_header_metrics(run_record, df_actionable, diff)
    _render_repaint_alarm(diff)

    df = df_all if show_all_states else df_actionable
    df = df[df["indicator"].apply(lambda ind: CATALOG.get(ind, None) is not None
                                   and CATALOG[ind].category in selected_categories)]
    if direction_choice != "Hepsi":
        df = df[df["direction"] == direction_choice]
    df = df.sort_values("detected_at", ascending=False).reset_index(drop=True)

    st.subheader("1 · Sinyaller")
    selected_rows: list[int] = []
    if df.empty:
        st.info("Seçili filtrelerle eşleşen sinyal yok.")
    else:
        display_df = _to_display(df)
        event = st.dataframe(
            display_df[_DISPLAY_COLS], hide_index=True,
            on_select="rerun", selection_mode="single-row", key="signal_table",
        )
        selected_rows = list(event.selection.rows) if event and event.selection else []

    st.divider()
    st.subheader("2 · Grafiğini Seç")
    if selected_rows:
        row = df.iloc[selected_rows[0]]
        default_symbol = row["symbol"]
        default_indicator = row["indicator"]
        default_tf = row["timeframe"]
    else:
        default_symbol, default_indicator, default_tf = "", "harmonic.pesavento", "1d"

    options = _indicator_options()
    keys = [k for _label, k in options]
    label_by_key = {k: label for label, k in options}
    default_idx = keys.index(default_indicator) if default_indicator in keys else 0

    col1, col2, col3 = st.columns([1, 2, 1])
    symbol = col1.text_input("Sembol", value=default_symbol).strip().upper()
    chosen_key = col2.selectbox(
        "Gösterge", keys, index=default_idx, format_func=lambda k: label_by_key[k],
    )
    tf_choices = ["1d", "4h", "1h", "w1"]
    tf_index = tf_choices.index(default_tf.lower()) if default_tf.lower() in tf_choices else 0
    tf = col3.selectbox("Zaman Dilimi", tf_choices, index=tf_index)

    if symbol:
        try:
            with st.spinner("Grafik oluşturuluyor..."):
                fig = _render_live(chosen_key, symbol, tf, market, theme=theme)
            st.plotly_chart(fig, width="stretch")
        except (ValueError, FileNotFoundError) as exc:
            st.error(f"Grafik oluşturulamadı: {exc}")
        else:
            _render_reading_guide(chosen_key)
            if chosen_key == STRUCTURE_REPORT_NAME:
                st.divider()
                _render_ai_report_button(symbol, tf, market)
    else:
        st.info("Bir sembol gir ya da yukarıdaki sinyal tablosundan bir satır seç.")


main()
