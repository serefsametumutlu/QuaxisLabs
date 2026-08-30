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
"""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from tlab.indicators.bootstrap import CATALOG
from tlab.scanner.eod import run_eod
from tlab.scanner.results import DiffReport, ResultsStore, RunRecord
from tlab.viz.labels_tr import INDICATOR_CATEGORY_TR, tr_direction, tr_state
from tlab.viz.live import render_live

_ACTIONABLE_STATES = ("confirmed", "completed")

_DISPLAY_COLS = [
    "Sembol", "Kategori", "İndikatör", "Zaman Dilimi", "Yön", "Durum", "Olay", "Sinyal Zamanı",
]


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


def _run_scan(market: str, force: bool) -> None:
    with st.spinner("Taranıyor... (evren büyükse birkaç dakika sürebilir)"):
        report = run_eod(market=market, force=force)
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


def main() -> None:
    st.set_page_config(page_title="tlab Tarama Panosu", layout="wide", page_icon="📊")
    st.title("📊 tlab Tarama Panosu")

    with st.sidebar:
        st.header("Kontroller")
        market = st.selectbox("Piyasa", ["bist", "nasdaq"], index=0)
        force = st.checkbox("Zorla yeniden tara", value=False)
        if st.button("🔄 Bugünü Tara", width="stretch", type="primary"):
            _run_scan(market, force)
            st.rerun()

        st.divider()
        with ResultsStore() as store:
            run_ids = store.list_runs(market, status="completed")
        if not run_ids:
            st.info("Henüz tamamlanmış bir tarama yok — yukarıdaki butonla ilk taramayı başlatın.")
            st.stop()
        run_id = st.selectbox("Tarama (Run)", run_ids, format_func=_format_run_label)

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

    st.subheader("Sinyaller")
    if df.empty:
        st.info("Seçili filtrelerle eşleşen sinyal yok.")
        return

    display_df = _to_display(df)
    event = st.dataframe(
        display_df[_DISPLAY_COLS], hide_index=True,
        on_select="rerun", selection_mode="single-row", key="signal_table",
    )
    selected_rows = list(event.selection.rows) if event and event.selection else []

    st.divider()
    if selected_rows:
        row = df.iloc[selected_rows[0]]
        st.subheader(f"{row['symbol']} — {row['indicator']} ({row['timeframe']})")
        try:
            with st.spinner("Grafik oluşturuluyor..."):
                fig = render_live(row["indicator"], row["symbol"], row["timeframe"], market)
            st.plotly_chart(fig)
        except (ValueError, FileNotFoundError) as exc:
            st.error(f"Grafik oluşturulamadı: {exc}")
    else:
        st.info("Grafiği görmek için yukarıdaki tablodan bir satır seçin.")

    with st.expander("Hızlı bakış (sinyal listesinden bağımsız, herhangi bir sembol/indikatör)"):
        col1, col2, col3 = st.columns(3)
        quick_symbol = col1.text_input("Sembol", value="")
        quick_indicator = col2.selectbox("İndikatör", sorted(CATALOG.keys()))
        quick_tf = col3.selectbox("Zaman Dilimi", ["1d", "4h", "1h", "w1"], index=0)
        if quick_symbol and st.button("Grafiği Göster"):
            try:
                symbol = quick_symbol.strip().upper()
                with st.spinner("Grafik oluşturuluyor..."):
                    fig = render_live(quick_indicator, symbol, quick_tf, market)
                st.plotly_chart(fig)
            except (ValueError, FileNotFoundError) as exc:
                st.error(f"Grafik oluşturulamadı: {exc}")


main()
