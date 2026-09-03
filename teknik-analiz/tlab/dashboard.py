"""QuaxisLabs Tarama Panosu — Streamlit uygulaması.

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
  EN GÜNCEL (`detected_at` en büyük) satırı gösterir.
- SQLite bağlantısı HER script koşusunda TAZE açılıp kapanır
  (`st.cache_resource` KULLANILMAZ) — Streamlit'in çoklu-oturum/thread
  modeli sqlite3 bağlantılarını thread'ler arası paylaştırmayı YASAKLAR.

2026-09-02 eklentileri (kullanıcı geri bildirimi — "hâlâ istediğim gibi
değil, karmaşık"):
- **Sidebar kaldırıldı.** Streamlit'in varsayılan sol paneli hiçbir zaman
  onaylanan mockup'ın (Artifact `f1184381...`) tasarımına uymadı. Piyasa +
  tema seçici artık üstte tek satırlık, CSS ile yeniden derilendirilmiş bir
  şerit; kategori/durum/yön/gün filtreleri anlamsal olarak ait oldukları
  Sonuç Listesi ekranına taşındı.
- **Otomatik ekran geçişi.** `st.tabs` (elle tıklama gerektiriyordu, ayrıca
  programatik geçiş DESTEKLENMİYOR) yerine `st.session_state["screen"]`
  ile sürülen tek-ekran render — bir tarama bitince veya bir sinyal satırı
  seçilince sayfa KENDİLİĞİNDEN bir sonraki ekrana geçer.
- **AI rapor her göstergede.** `_render_ai_report_button` artık yalnızca
  `structure.report` için değil, seçili HERHANGİ bir gösterge için görünür
  (`quant_report.generate_indicator_report` — genel amaçlı yedek olgu
  çıkarıcı, bkz. `report_text.py::build_generic_summary_lines`).
- **Grafik indirme artık İSTEĞE BAĞLI (lazy).** Eskiden `fig.to_image()`
  (kaleido) grafik ekranı her açıldığında/her rerun'da KOŞULSUZ çağrılıyordu
  — Streamlit'in "herhangi bir widget etkileşiminde TÜM script yeniden
  çalışır" modeliyle birleşince, sayfanın alakasız bir yerinde yapılan HER
  tıklama bile kaleido'nun headless-Chrome sürecini yeniden başlatıyordu
  (tek başına saniyeler sürebilen bir işlem). Kullanıcı: "tek tek grafik
  açmak aşırı yavaş kalıyor". Artık PNG yalnızca "🖼️ PNG Oluştur" butonuna
  basılınca üretilip `st.session_state`'te tutuluyor.

2026-09-02 performans + eksik-özellik düzeltmeleri (kullanıcı: "bu şekilde
çok yavaş çalışıyor... eski taramalara tekrar girip görüntüleyemiyorum...
hisse bazlı arama yok... 4h ve günlük ayrımı yapamıyorum" — `Desktop/
quant-platform` klasöründeki, kullanıcının FastAPI+React+Redis ile yazdığı
ayrı bir proje incelendi, karşılaştırma için bkz. aşağıdaki not):
- **Grafik önbellekleme.** `tlab/viz/live.py::render_live`, HER çağrıda
  ilgili göstergeyi SIFIRDAN hesaplıyordu (bazıları — `structure.
  price_structure`'ın O(n²) trendline üretimi, `momentum.*`'ın TÜM evreni
  hesaplaması — saniyeler sürebiliyor); yukarıdaki "her rerun'da her şey
  yeniden çalışır" modeliyle birleşince asıl yavaşlığın kaynağı BUYDU
  (kaleido değil). `_cached_chart_figure` (`st.cache_data`, günlük
  `cache_bust`) ekledi; manuel "🔄 Yenile" butonu önbelleği elle temizler.
- **"Tüm Sinyaller" ekranı.** Eskiden Sonuç Listesi yalnızca TEK bir
  `run_id`'yi gösterebiliyordu — kullanıcı farklı zamanlarda farklı
  stratejiler taradıkça (her biri kendi run'ında) "genel olarak sinyal
  aldığım hisseleri" görecek birleşik bir ekran YOKTU (DB katmanı —
  `ResultsStore.query()` — buna zaten izin veriyordu, sadece UI eksikti).
  `_render_all_signals_screen`, son N tamamlanmış run'ı birleştirip AYNI
  (sembol,tf,indikatör,pattern_id) zincir-bazlı en-güncel-durum mantığıyla
  gösteriyor.
  - **Sembol arama + zaman dilimi filtresi.** `ResultsStore.query()` zaten
  `symbol`/`timeframe` parametrelerini destekliyordu — Filtreler panelinde
  hiç arayüzü YOKTU. `_render_signal_table` (Sonuç Listesi VE Tüm
  Sinyaller'in PAYLAŞTIĞI ortak fonksiyon) artık ikisini de içeriyor.
- **quant-platform karşılaştırması — mimari DEĞİŞTİRİLMEDİ, bilinçli
  karar**: quant-platform (FastAPI+Postgres+Redis+React) hızlı çünkü grafiği
  SUNUCUDA hiç render etmiyor — ham OHLCV JSON'unu REST'ten döndürüp
  TARAYICIDA (recharts) çiziyor, ve sinyaller Postgres'te sınırsız/indeksli
  sorgulanabiliyor. tlab'ın asıl yavaşlığı ise bu mimari farktan DEĞİL,
  yukarıdaki önbellekleme eksikliğinden kaynaklanıyordu — bu düzeltmeyle
  Streamlit içinde kalarak aynı sorunlar çözüldü; FastAPI+React'e geçiş
  (tüm `tlab/viz/renderer.py`'nin — 2500+ satır Plotly declutter/etiket
  mantığının — bir JS grafik kütüphanesinde yeniden yazılmasını gerektirir)
  haftalar sürecek bir yeniden yazım olurdu, bu düzeltmeler onu gereksiz
  kılıyor."""

from __future__ import annotations

import base64
import json
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

# `streamlit run tlab/dashboard.py` (paketi `pip install -e .` ETMEDEN, en
# doğal/beklenen çalıştırma şekli) Python'un `sys.path[0]`'ını bu dosyanın
# KENDİ klasörüne (`tlab/`) ayarlar — proje köküne (`tlab/`nin ebeveyni)
# DEĞİL. Bu yüzden `import tlab.cli` "No module named 'tlab'" ile patlar
# (kullanıcı geri bildirimi — gerçek hata budur). `python -m streamlit run
# ...` farklı davranır (`sys.path[0]` = CWD) ama bunu HERKESİN hatırlaması
# beklenemez; en doğal komut ("streamlit run tlab/dashboard.py") kutudan
# çıktığı gibi ÇALIŞMALI. Proje kökü burada elle sys.path'e eklenir.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from tlab.cli import _load_scan_preset  # noqa: E402
from tlab.indicators.bootstrap import CATALOG  # noqa: E402
from tlab.scanner.eod import run_eod  # noqa: E402
from tlab.scanner.results import DiffReport, ResultsStore, RunRecord  # noqa: E402
from tlab.viz.labels_tr import (  # noqa: E402
    INDICATOR_CATEGORY_TR,
    signal_reading,
    tr_direction,
    tr_indicator,
    tr_state,
)
from tlab.viz.live import (  # noqa: E402
    STRUCTURE_REPORT_NAME,
    compute_live,
    compute_structure_report,
)
from tlab.viz.live import render_live as _render_live  # noqa: E402
from tlab.viz.quant_report import generate_indicator_report, generate_quant_report  # noqa: E402
from tlab.viz.themes import LIGHT_ANALYSIS, resolve_theme  # noqa: E402

_ACTIONABLE_STATES = ("confirmed", "completed")

_DISPLAY_COLS = [
    "Sembol", "Kategori", "İndikatör", "Zaman Dilimi", "Yön", "Durum", "Olay", "Sinyal Zamanı",
]


_READING_LABELS: tuple[tuple[str, str], ...] = (
    ("watch", "🔎 Nereye Bak"), ("measures", "📐 Ne Ölçer"),
    ("values", "📊 Değerler Ne Demek"), ("signal", "📈 AL Sinyali Ne Zaman Oluşur"),
)

_SCREENS: tuple[tuple[str, str], ...] = (
    ("home", "1 · Ana Sayfa"), ("results", "2 · Sonuç Listesi"),
    ("chart", "3 · Grafik Detayı"),
)


_PERSISTED_QUERY_KEYS: tuple[str, ...] = (
    "screen", "active_run_id", "chart_symbol", "chart_indicator", "chart_tf",
)


def _goto(screen: str, **extra: object) -> None:
    st.session_state["screen"] = screen
    for k, v in extra.items():
        st.session_state[k] = v
    _sync_query_params_from_state()
    st.rerun()


def _sync_query_params_from_state() -> None:
    """Ekran/durum bilgisini URL query param'larına da yazar. Kullanıcı
    geri bildirimi: "geri tuşuna basınca tamamen sıfırlanıyor" — Streamlit
    ekran geçişlerini yalnızca `st.session_state`te tutuyordu, bu hiçbir
    GERÇEK tarayıcı geçmişi/URL bırakmıyordu; tarayıcının geri tuşu (ya da
    sayfayı yenilemek) `session_state`i TAMAMEN SIFIRLIYOR (yepyeni bir
    Streamlit oturumu gibi). Kritik ekran durumunu (hangi run/sembol/
    gösterge) URL'e yansıtmak, bir yenileme/geri-navigasyon SONRASI aynı
    ekrana DÖNMEYİ sağlıyor. **Dürüst sınır**: bu adım-adım geri/ileri
    gitmeyi SAĞLAMAZ (Streamlit'in mimarisi buna izin vermiyor) — yalnızca
    "tamamen sıfırlanma" yerine "son bırakılan ekrana dön" davranışı
    sağlar, ki bu kullanıcının asıl şikayet ettiği kayıp."""
    for key in _PERSISTED_QUERY_KEYS:
        value = st.session_state.get(key)
        if value is None:
            st.query_params.pop(key, None)
        else:
            st.query_params[key] = str(value)


def _restore_state_from_query_params() -> None:
    """`main()`'in en başında, HER ŞEYDEN ÖNCE çağrılır: bu tamamen YENİ
    bir Streamlit oturumuysa (session_state boş — ör. sayfa yenilendi ya
    da tarayıcının geri tuşu bu URL'e döndürdü) ama URL'de daha önce
    `_sync_query_params_from_state`'in bıraktığı bir `screen` parametresi
    varsa, o durumu geri yükler. Zaten devam eden bir oturumda (session_
    state'te "screen" varsa) HİÇBİR ŞEY YAPMAZ — kullanıcının o anki elle
    yaptığı seçimleri ASLA ezmez."""
    if "screen" not in st.query_params or "screen" in st.session_state:
        return
    for key in _PERSISTED_QUERY_KEYS:
        if key in st.query_params:
            st.session_state[key] = st.query_params[key]


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
            "İndikatör": df["indicator"].map(tr_indicator),
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
_LOGO_PATH = Path(__file__).resolve().parent / "assets" / "quaxislabs_logo.png"
_FAVICON_PATH = Path(__file__).resolve().parent / "assets" / "quaxislabs_favicon_round.png"


def _ensure_round_favicon() -> Path | None:
    """Sekme ikonu (favicon) tarayıcıda KARE görünüyordu — kullanıcı geri
    bildirimi: "logoyu yuvarlak yap". `_LOGO_PATH`'teki görsel zaten
    dairesel bir rozet ÇİZİMİ ama SEFFAF olmayan kare bir tuval üzerinde;
    tarayıcı sekmeleri favicon'u OLDUĞU GİBİ (köşeleri yuvarlamadan) çizer.
    Burada Pillow ile köşeleri SAYDAM yapan bir alfa maskesi uygulanmış
    YENİ bir PNG üretilir (kaynak dosya DEĞİŞTİRİLMEZ — sidebar'daki kare
    logo aynı kalır, yalnızca favicon için ayrı bir varyant). Üretilen
    dosya `assets/`e yazılıp sonraki çalıştırmalarda YENİDEN ÜRETİLMEZ
    (kaynak logodan daha yeni ise atlanır)."""
    if not _LOGO_PATH.exists():
        return None
    if _FAVICON_PATH.exists() and _FAVICON_PATH.stat().st_mtime >= _LOGO_PATH.stat().st_mtime:
        return _FAVICON_PATH
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    img = Image.open(_LOGO_PATH).convert("RGBA")
    size = img.size
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size[0], size[1]), fill=255)
    img.putalpha(mask)
    _FAVICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(_FAVICON_PATH)
    return _FAVICON_PATH


_PAREN_SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")


def _short_name(description: str) -> str:
    """Sondaki "(patterns.head_shoulders)" gibi ham katalog kimliği
    parantezini temizler — kullanıcı geri bildirimi: "bunları neden
    kullanıcı görsün ki çirkin duruyor". Tam açıklama (parantezli hâliyle)
    detay sayfasında hâlâ gösterilir, yalnızca sol menüdeki KISA ad
    sadeleştirilir."""
    return _PAREN_SUFFIX_RE.sub("", description).strip()


def _strategies_by_category() -> dict[str, list[dict]]:
    """Sol menüdeki "Stratejiler" ağacı — iki kaynaktan derlenir:
    (1) `config/scans.yaml` presetleri, kendi `indicators` listesinin ilk
    öğesinin `CATALOG` kategorisine göre gruplanır; (2) presetlerde HİÇ
    temsil edilmeyen kategoriler için (ör. Harmonik Formasyon — scans.
    yaml'da hiçbir harmonik preset YOK, kullanıcı "harmonik nerede,
    göremiyorum" dedi) `CATALOG`'daki HER göstergeden bire bir üretilen
    bir yedek giriş — o kategoriyi ZATEN temsil eden bir preset varsa
    (ör. Trend/Fiyat Yapısı) tekrar/karışıklık olmasın diye eklenmez.
    Her giriş: `short` (sol menüde gösterilen kısa ad), `description`
    (detay sayfasında gösterilen tam metin), `preset_key` (varsa
    `_load_scan_preset` ile çalıştırılır), `indicator_names` (yoksa
    doğrudan bu göstergelerle taranır)."""
    grouped: dict[str, list[dict]] = {}
    represented_categories: set[str] = set()

    if _SCANS_YAML_PATH.exists():
        raw = yaml.safe_load(_SCANS_YAML_PATH.read_text(encoding="utf-8")) or {}
        for key, cfg in (raw.get("presets") or {}).items():
            description = cfg.get("description", key)
            indicators = cfg.get("indicators") or []
            cat = "Diğer"
            if indicators:
                spec = CATALOG.get(indicators[0])
                if spec is not None:
                    cat = INDICATOR_CATEGORY_TR.get(spec.category, spec.category)
            represented_categories.add(cat)
            grouped.setdefault(cat, []).append({
                "id": key, "short": _short_name(description), "description": description,
                "preset_key": key, "indicator_names": None,
            })

    for key, spec in CATALOG.items():
        cat = INDICATOR_CATEGORY_TR.get(spec.category, spec.category)
        if cat in represented_categories:
            continue
        grouped.setdefault(cat, []).append({
            "id": key, "short": tr_indicator(key),
            "description": f"{tr_indicator(key)} — evrende bu göstergeye göre tarar.",
            "preset_key": None, "indicator_names": [key],
        })
    return grouped


def _categories_for_indicator_names(names: list[str] | None) -> list[str] | None:
    """Bir strateji hangi `CATALOG` kategori(ler)ine ait göstergelerle
    tarandıysa onları döner (Sonuç Listesi'nin Kategori filtresini otomatik
    daraltmak için) — `names` boş/None ise (ör. Tam Tarama) `None` döner,
    bu da "hepsi" anlamına gelir."""
    if not names:
        return None
    cats = sorted({CATALOG[n].category for n in names if n in CATALOG})
    return cats or None


def _catalog_keys_by_category() -> dict[str, list[str]]:
    """`_strategies_by_category()`'nin YANINDA — kategori başına TÜM
    `CATALOG` anahtarları (kullanıcı isteği: "her grubu hem ayrı ayrı hem
    de toplu tarama yapabilmeliyim", ör. 8 harmonik ekolünü TEK seferde).
    Presetlerden BAĞIMSIZ, doğrudan katalogdan — bu yüzden bir kategorinin
    HİÇ preset'i olmasa bile (Harmonik gibi) toplu tarama seçeneği yine de
    doğru göstergelerle çalışır."""
    grouped: dict[str, list[str]] = {}
    for key, spec in CATALOG.items():
        cat = INDICATOR_CATEGORY_TR.get(spec.category, spec.category)
        grouped.setdefault(cat, []).append(key)
    return grouped


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


def _run_scan(
    market: str, force: bool, indicator_names: list[str] | None, label: str,
) -> str | None:
    """Taramayı çalıştırır, sonucu bildirir, tamamlandıysa `run_id` döner
    (çağıran taraf bunu Sonuç Listesi'ne otomatik geçiş için kullanır)."""
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
        return report.get("run_id")
    if status == "skipped_existing":
        st.info(
            "Bugün için zaten tamamlanmış bir tarama var "
            "(yeniden koşmak için 'force'u işaretleyin)."
        )
        return report.get("run_id")
    if status == "skipped_holiday":
        st.info("Bugün işlem günü değil, tarama atlandı.")
        return None
    st.warning(f"Durum: {status}")
    return None


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


def _render_ai_report_button(chosen_key: str, symbol: str, timeframe: str, market: str) -> None:
    """`structure.report` seçiliyken ZENGİN, özel yola (`generate_quant_
    report`); diğer HERHANGİ bir gösterge için genel yedek yola
    (`generate_indicator_report`) düşer — pair göstergeleri (`needs_
    context`) `compute_live`'dan `df=None` döndürdüğü için (bkz. `live.py`)
    şimdilik kapsam dışı, anlaşılır bir mesajla belirtilir."""
    if st.button("🤖 Yapay Zeka Raporu Oluştur", key="ai_report_btn", width="stretch"):
        with st.spinner("Rapor üretiliyor..."):
            if chosen_key == STRUCTURE_REPORT_NAME:
                ps_result, sf_result, df = compute_structure_report(symbol, timeframe, market)
                report = generate_quant_report(ps_result, sf_result, df, symbol=symbol)
            else:
                result, df = compute_live(chosen_key, symbol, timeframe, market)
                if df is None:
                    st.info(
                        "Pair göstergeleri için yapay zeka raporu şimdilik desteklenmiyor."
                    )
                    return
                report = generate_indicator_report(result, df, symbol=symbol)
        if report.used_ai:
            st.markdown(report.text)
        else:
            st.info(f"AI sağlayıcısı kullanılamadı ({report.note}) — deterministik özet:")
            st.markdown(report.text)


@st.cache_data(show_spinner=False, ttl=1800)
def _cached_chart_figure(
    indicator_name: str, symbol: str, timeframe: str, market: str, theme: str, cache_bust: str,
):
    """`_render_live` HER çağrıda göstergeyi SIFIRDAN hesaplar (bazıları —
    `structure.price_structure`'ın O(n²) trendline üretimi, `momentum.*`'ın
    TÜM evreni hesaplaması — saniyeler sürebilir); Streamlit'in "her widget
    etkileşiminde TÜM script yeniden çalışır" modeliyle birleşince, grafik
    ekranındayken sayfanın ALAKASIZ bir yerinde yapılan bir tıklama bile bunu
    yeniden tetikliyordu — asıl yavaşlığın kaynağı buydu. `cache_bust`
    (bugünün tarihi) günlük doğal geçersizleşme sağlar; "🔄 Yenile" butonu
    `.clear()` ile elle temizler (aynı gün içinde yeni bir tarama sonrası)."""
    return _render_live(indicator_name, symbol, timeframe, market, theme=theme)


def _inject_theme_css(theme_key: str) -> None:
    """Streamlit'in varsayılan (jenerik, kullanıcının "hiç güzel değil"
    dediği) beyaz/gri kromunu, seçili grafik temasının KENDİ renkleriyle
    (bkz. `themes.py`) yeniden derilendirir — yeni bir renk paleti İCAT
    EDİLMEDİ, tek doğru kaynak (`Theme`) burada da okunuyor."""
    theme = resolve_theme(theme_key, default=LIGHT_ANALYSIS)
    bg, panel, text, muted, accent, border = (
        theme.page_bg, theme.bg, theme.text, theme.muted, theme.accent, theme.border,
    )
    # "Grafik Stil Vitrini" mockup'ının fontlarını (Inter/JetBrains Mono/
    # Source Serif 4/Playfair Display) gerçekten YÜKLER — `themes.py`'nin
    # `font`/`font_display` alanları artık bu isimleri taşıyor (2026-09-02)
    # ama tarayıcı bu Google Font'ları İNDİRMEDİKÇE hiçbir fark etmez, sessizce
    # sistem fontuna düşer. Yalnızca CANLI (tarayıcıda görüntülenen) grafikleri
    # kapsar — kaleido PNG dışa aktarımı AYRI bir süreç, bu `<link>`i görmez.
    st.markdown(
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        "family=Inter:wght@400;500;600;700&"
        "family=JetBrains+Mono:wght@400;500;600;700&"
        "family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&"
        "family=Playfair+Display:wght@600;700;800&"
        'display=swap">',
        unsafe_allow_html=True,
    )
    # 2026-09-02 (kullanıcı: "light dark kısmında karışıklık var ... bazı
    # yerler dark bazı yerler light"): eskiden yalnızca `.stApp` içindeki
    # görünür elemanlar hedefleniyordu — Streamlit'in KENDİ iç bileşenleri
    # (selectbox açılır listesi, checkbox/radio gibi) `--background-color`/
    # `--text-color`/`--secondary-background-color`/`--primary-color` CSS
    # DEĞİŞKENLERİNİ okuyarak boyanıyor (Streamlit'in resmi `[theme]`
    # mekanizmasıyla AYNI değişkenler) — bunlar set edilmeyince, `.stApp`
    # DIŞINA (bir "portal" olarak `<body>` köküne) render edilen açılır
    # listeler gibi öğeler HÂLÂ Streamlit'in varsayılan (aydınlık) temasını
    # kullanmaya devam ediyordu; bu yüzden "bazı yerler dark bazı yerler
    # light" oluyordu. Kök `:root` değişkenlerini set etmek, DOM'da nerede
    # olursa olsun TÜM Streamlit-yerel bileşenlere tek seferde yayılıyor —
    # aşağıdaki elle yazılmış seçiciler yalnızca EK bir güvenlik payı.
    st.markdown(
        f"""<style>
        :root, .stApp {{
            --primary-color: {accent};
            --background-color: {bg};
            --secondary-background-color: {panel};
            --text-color: {text};
        }}
        .stApp {{ background: {bg}; font-family: {theme.font}; }}
        section.main > div {{ padding-top: 1rem; }}
        h1, h2, h3, h4, h5, h6, p, span, label, li {{
            color: {text}; font-family: {theme.font};
        }}
        .stApp [data-testid="stHeader"] {{ background: transparent; }}
        div[data-testid="stMetric"] {{
            background: {panel}; border: 1px solid {border}; border-radius: 10px;
            padding: 10px 14px;
        }}
        [data-testid="stSidebar"] {{ background: {panel}; border-right: 1px solid {border}; }}
        [data-testid="stSidebar"] * {{ color: {text}; }}
        [data-testid="stExpander"] {{
            background: {panel}; border: 1px solid {border}; border-radius: 8px;
        }}
        .quaxis-brand {{ font-size: 19px; font-weight: 800; color: {text}; margin-bottom: 6px; }}
        .quaxis-step {{ font-size: 12px; font-weight: 700; color: {muted}; margin: 4px 0 14px; }}
        .quaxis-step .on {{ color: {accent}; }}
        div.stButton > button {{
            background: {panel}; color: {text}; border: 1px solid {border};
        }}
        div.stButton > button[kind="primary"] {{
            background: {accent}; border-color: {accent}; color: {bg};
        }}
        /* Selectbox/multiselect/text_input KAPALI kutuları — kullanıcı
        geri bildirimi: "piyasa... kısımları bu koyuya uymuyor beyaz
        kalıyor". Bunlar BaseWeb bileşenleri, kök CSS değişkenlerini HER
        ZAMAN okumuyor — inline stiller `!important`le ezilmesi gerekiyor. */
        [data-baseweb="select"] > div, [data-baseweb="base-input"],
        [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {{
            background: {panel} !important; color: {text} !important;
            border-color: {border} !important;
        }}
        [data-baseweb="select"] * {{ color: {text} !important; }}
        [data-baseweb="tag"] {{ background: {accent} !important; color: {bg} !important; }}
        [data-baseweb="tag"] * {{ color: {bg} !important; }}
        [data-testid="stCheckbox"] label p, [data-testid="stRadio"] label p,
        [data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p {{
            color: {text} !important;
        }}
        [data-testid="stCaptionContainer"] {{ color: {muted} !important; }}
        /* Selectbox/multiselect açılır listesi + diğer Streamlit "portal"
        bileşenleri — `.stApp` alt ağacının DIŞINDA render edilir, kök
        değişkenler yetmezse diye AYRICA hedeflenir. */
        [data-baseweb="popover"], [data-baseweb="menu"],
        ul[data-testid="stSelectboxVirtualDropdown"] {{
            background: {panel} !important;
        }}
        [data-baseweb="popover"] *, [data-baseweb="menu"] *,
        ul[data-testid="stSelectboxVirtualDropdown"] * {{ color: {text} !important; }}
        /* `st.dataframe` glide-data-grid ile CANVAS'a çiziliyor — hücre
        renkleri Python'dan CSS ile ERİŞİLEMEZ (Streamlit'in KENDİ resmi
        tema anahtarı bile bunu yalnızca YENİ bir oturum/sayfa yüklemesinde
        değiştirebiliyor, bizim çalışma-anı düğmemizin ERİŞEMEYECEĞİ bir
        mekanizma — bkz. dashboard.py modül docstring'i, "DÜRÜST SINIR").
        Bu yüzden ızgara BİLİNÇLİ OLARAK her zaman kendi (açık/"kağıt")
        rengini korur — belirgin bir çerçeve/gölgeyle "koyu sayfa üzerinde
        duran bir rapor kartı" gibi ÇERÇEVELENİR, kazara unutulmuş
        stilsiz bir kalıntı gibi GÖRÜNMEZ. */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {accent}; border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.18); overflow: hidden;
        }}
        </style>""",
        unsafe_allow_html=True,
    )


def _render_step_indicator() -> None:
    current = st.session_state.get("screen", "home")
    steps_html = "  ›  ".join(
        f'<span class="{"on" if key == current else ""}">{label}</span>'
        for key, label in _SCREENS
    )
    st.markdown(f'<div class="quaxis-step">{steps_html}</div>', unsafe_allow_html=True)


def _render_top_bar() -> str:
    """Sağ üstte açık/koyu tema anahtarı. Kullanıcı geri bildirimi:
    "bu dark light düğmeli bir buton olmalıydı sağ yukarı da onu da
    bulamıyorum" — eskiden sidebar'a gömülü, üç seçenekli (Klasik Beyaz/
    Terminal Koyu/Kağıt) bir `st.selectbox` idi; fark edilmiyordu. Artık
    `st.toggle` ile iki değerli (açık/koyu) bir anahtar, sayfanın en
    üstünde sağda. "Kağıt Rapor" üçüncü teması bu hızlı erişimden ÇIKARILDI
    (bilinçli sadeleştirme — iki değerli bir anahtarla üç seçenek doğal
    olarak ifade edilemez); gerekirse ileride ayrı bir yolla geri
    eklenebilir."""
    _, col_toggle = st.columns([8, 1])
    with col_toggle:
        dark = st.toggle(
            "🌙 Koyu", value=st.session_state.get("dark_mode", False), key="dark_mode",
        )
    return "dark" if dark else "light"


def _render_sidebar_brand() -> None:
    """Logo + "QuaxisLabs" yazısı yan yana, TEK satırda. Kullanıcı geri
    bildirimi: "logoyu pat diye olduğu gibi koymuşsun... logonun yanında
    sol üstte QuaxisLabs yazısı da olmalı". `st.image` + `st.markdown` ayrı
    blok seviyesi elemanlar olduğu için yan yana konamıyor — logo base64
    olarak gömülüp TEK bir `<div>` içinde metinle birlikte flex satırına
    yerleştiriliyor (hem açık hem koyu temada `.quaxis-brand`'in KENDİ
    metin rengini miras alır, ayrı bir renk İCAT EDİLMEDİ)."""
    if not _LOGO_PATH.exists():
        st.markdown('<div class="quaxis-brand">QuaxisLabs</div>', unsafe_allow_html=True)
        return
    logo_b64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <img src="data:image/png;base64,{logo_b64}"
             style="width:34px;height:34px;border-radius:50%;object-fit:cover;
             flex-shrink:0;" />
        <span class="quaxis-brand" style="margin-bottom:0;">QuaxisLabs</span>
        </div>""",
        unsafe_allow_html=True,
    )


def _render_sidebar() -> str:
    """Sol menü — kullanıcı isteği (2026-09-02): logo + Piyasa üstte;
    "Stratejiler" kendisi de (alt kategoriler gibi) tıklanınca aşağı açılan
    bir buton (Streamlit expander'ı KENDİ İÇİNDE expander barındıramadığı
    için — üst seviye burada `st.session_state` ile sürülen bir aç/kapa
    butonu, alt kategoriler kendi `st.expander`'ı); HER strateji artık
    ham katalog kimliği İÇERMEYEN kısa bir adla görünür ve tıklanınca
    DOĞRUDAN taramayı başlatmaz — önce "Strateji Detayı" ekranına geçer
    (tam açıklama + onay butonu orada, bkz. `_render_strategy_detail_
    screen`) — sol menüyü uzun tutmamak için. Tema artık BURADA DEĞİL —
    bkz. `_render_top_bar` (sağ üst köşe anahtarı)."""
    with st.sidebar:
        _render_sidebar_brand()
        market = st.selectbox("Piyasa", ["bist", "nasdaq"], index=0)
        st.divider()

        st.session_state.setdefault("strategies_open", True)
        arrow = "▾" if st.session_state["strategies_open"] else "▸"
        if st.button(f"{arrow}  Stratejiler", key="toggle_strategies", width="stretch"):
            st.session_state["strategies_open"] = not st.session_state["strategies_open"]

        if st.session_state["strategies_open"]:
            force = st.checkbox("Zorla yeniden tara", value=False)
            if st.button("↻ Tam Tarama (Tüm Göstergeler)", width="stretch", type="primary"):
                run_id = _run_scan(market, force, indicator_names=None, label="Tam Tarama")
                if run_id:
                    _goto("results", active_run_id=run_id, active_categories=None)
            bulk_keys_by_cat = _catalog_keys_by_category()
            for cat, items in _strategies_by_category().items():
                with st.expander(cat):
                    bulk_keys = bulk_keys_by_cat.get(cat, [])
                    if len(bulk_keys) > 1:
                        bulk_label = f"▶▶ Tüm {cat} Göstergelerini Tara ({len(bulk_keys)})"
                        bulk_item: dict[str, object] = {
                            "id": f"bulk::{cat}",
                            "short": bulk_label,
                            "description": (
                                f"{cat} kategorisindeki TÜM göstergeleri "
                                f"({len(bulk_keys)} adet) tek seferde tarar."
                            ),
                            "preset_key": None,
                            "indicator_names": bulk_keys,
                        }
                        if st.button(bulk_label, key=f"bulk_{cat}", width="stretch"):
                            _goto(
                                "strategy_detail", detail_strategy=bulk_item,
                                detail_force=force,
                            )
                        st.divider()
                    for item in items:
                        if st.button(item["short"], key=f"strat_{item['id']}", width="stretch"):
                            _goto("strategy_detail", detail_strategy=item, detail_force=force)
    return market


def _render_home_screen(market: str) -> None:
    """Ekran 1 — Ana Sayfa. Strateji başlatma artık TAMAMEN sol menüde
    (bkz. `_render_sidebar`) — burada yalnızca geçmiş taramaların listesi
    kalır; bir run'a tıklamak OTOMATİK Sonuç Listesi'ne geçer."""
    st.subheader("📋 Geçmiş Taramalar")
    with ResultsStore() as store:
        run_ids = store.list_runs(market, status="completed")
    if not run_ids:
        st.info(
            "Henüz tamamlanmış bir tarama yok — sol menüden "
            "**Stratejiler** ile ilk taramayı başlatın."
        )
        return
    if st.button("🗂 Tüm Sinyaller (Tüm Taramaların Birleşimi)", width="stretch"):
        _goto("all_signals")
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
    selected_run_rows = list(run_event.selection.rows) if run_event and run_event.selection else []
    if selected_run_rows:
        _goto("results", active_run_id=run_ids[selected_run_rows[0]], active_categories=None)


def _render_strategy_detail_screen(market: str) -> None:
    """Strateji Detayı — sol menüden bir strateji seçilince buraya düşülür
    (kullanıcı isteği: "içine girince detay sayfası olur orada detayını
    yazarsın ilk göründüğü yerde çok uzun tutma"). Tam açıklama + hangi
    gösterge(ler)in çalışacağı burada, taramayı fiilen başlatan onay
    butonu de burada — sol menüdeki tek tıkla YANLIŞLIKLA tarama
    başlatılmasının da önüne geçer."""
    item: dict | None = st.session_state.get("detail_strategy")
    if st.button("← Stratejilere Dön"):
        _goto("home")
    if item is None:
        st.info("Bir strateji seçilmedi — sol menüden bir tane seçin.")
        return

    st.subheader(item["short"])
    st.write(_short_name(item["description"]) or item["short"])
    if item.get("preset_key"):
        st.caption(f"Kullanılan tarama tanımı: `{item['preset_key']}`")
    elif item.get("indicator_names"):
        st.caption(f"Kullanılan gösterge: `{', '.join(item['indicator_names'])}`")

    force = st.checkbox(
        "Zorla yeniden tara", value=bool(st.session_state.get("detail_force", False)),
    )
    if st.button("▶ Taramayı Çalıştır", type="primary", width="stretch"):
        names: list[str] | None
        if item.get("preset_key"):
            names, _filt = _load_scan_preset(item["preset_key"], path=str(_SCANS_YAML_PATH))
        else:
            names = item.get("indicator_names")
        run_id = _run_scan(market, force, indicator_names=names, label=item["short"])
        if run_id:
            # Kullanıcı geri bildirimi: "genel tarama yaptıktan sonra
            # buralarda çıkması lazım ama çıkmıyor" — bu strateji BUGÜN
            # zaten bir Tam Tarama'nın İÇİNDE koşulmuş olabilir (`run_eod`
            # `force=False` iken günün run'ını AYNEN döner), bu durumda
            # Sonuç Listesi TÜM kategorileri karışık gösteriyordu ve
            # kullanıcının aradığı sinyaller (ör. Harmonik) yüzlerce
            # başka satırın arasında kayboluyordu. Artık bu strateji hangi
            # kategori(ler)e aitse Sonuç Listesi'nin Kategori filtresi
            # OTOMATİK olarak ona daralıyor (elle değiştirilebilir).
            _goto(
                "results", active_run_id=run_id,
                active_categories=_categories_for_indicator_names(names),
            )


_TF_FILTER_OPTIONS: tuple[str, ...] = ("1h", "4h", "1d", "w1")
_ALL_SIGNALS_MAX_RUNS = 20


@st.cache_data(show_spinner="Sinyaller yükleniyor...", ttl=1800)
def _cached_run_rows(run_id: str) -> list[dict]:
    """Büyük evrenli (648 sembol × 26 gösterge) bir run için `signals`
    tablosundaki HER durum geçişini çeker — onbinlerce satır olabilir, her
    biri `_rows_to_frame`'de bir `json.loads()` gerektirir. Bu, önbellek
    OLMADAN Sonuç Listesi'ndeki HER filtre değişikliğinde (Streamlit'in
    "her etkileşimde tüm script yeniden çalışır" modeli yüzünden) yeniden
    koşuyordu — filtre panelini kullanmak bile yavaş hissettiriyordu."""
    with ResultsStore() as store:
        return store.query(run_id=run_id)


@st.cache_data(show_spinner="Sinyaller yükleniyor...", ttl=1800)
def _cached_multi_run_rows(run_ids: tuple[str, ...]) -> list[dict]:
    """`_cached_run_rows` ile AYNI gerekçe, `_render_all_signals_screen`
    birden fazla run'ı birleştirdiği için (yükü N run'a katlıyor)."""
    with ResultsStore() as store:
        rows: list[dict] = []
        for rid in run_ids:
            rows.extend(store.query(run_id=rid))
        return rows


def _render_signal_table(
    rows: list[dict], *, key_prefix: str,
    run_record: RunRecord | None = None, diff: DiffReport | None = None,
    default_categories: list[str] | None = None,
) -> None:
    """`_render_results_screen` (tek run) ve `_render_all_signals_screen`
    (çoklu run birleşimi) arasında PAYLAŞILAN filtre+tablo mantığı.
    Kullanıcı geri bildirimi ("sembol bazlı arama yok", "4h ve günlük
    ayrımı yapamıyorum") — `ResultsStore.query()` bu iki alanı ZATEN
    destekliyordu, eksik olan yalnızca bu arayüzdü. `default_categories`:
    belirli bir stratejiden gelindiyse (bkz. `_categories_for_indicator_
    names`) Kategori filtresi otomatik ona daralır — kullanıcı geri
    bildirimi: "genel tarama yaptıktan sonra buralarda çıkması lazım ama
    çıkmıyor" (aslında oradaydı, yalnızca yüzlerce başka kategorinin
    satırı arasında kayboluyordu)."""
    with st.expander("Filtreler", expanded=False):
        categories = sorted({spec.category for spec in CATALOG.values()})
        default_cats = (
            [c for c in default_categories if c in categories]
            if default_categories else categories
        )
        selected_categories = st.multiselect(
            "Kategori", categories, default=default_cats or categories,
            format_func=lambda c: INDICATOR_CATEGORY_TR.get(c, c), key=f"{key_prefix}_cat",
        )
        show_all_states = st.checkbox(
            "Tüm durumları göster (beklemede/geçersiz dahil)", value=False,
            key=f"{key_prefix}_states",
        )
        direction_choice = st.radio(
            "Yön", ["Hepsi", "long", "short"], horizontal=True, key=f"{key_prefix}_dir",
        )
        selected_tfs = st.multiselect(
            "Zaman Dilimi", list(_TF_FILTER_OPTIONS), default=list(_TF_FILTER_OPTIONS),
            key=f"{key_prefix}_tf",
        )
        symbol_query = st.text_input(
            "Sembol ara (ör. TCELL)", value="", key=f"{key_prefix}_sym",
        ).strip().upper()
        recency_days = st.slider(
            "Son kaç gün", min_value=1, max_value=90, value=5, key=f"{key_prefix}_days",
            help=(
                "trend.breakouts gibi yüksek frekanslı indikatörler yıllar "
                "boyunca birikmiş yüzlerce zincir üretir — bu pencere yalnızca "
                "SON N gün içinde bir durum değişikliği yaşanan zincirleri gösterir."
            ),
        )

    df_all = _rows_to_frame(rows)
    if not df_all.empty:
        bar_times = pd.to_datetime(df_all["bar_time"], utc=True)
        cutoff = bar_times.max() - pd.Timedelta(days=recency_days)
        df_all = df_all[bar_times >= cutoff]

    df_actionable = df_all[df_all["state"].isin(_ACTIONABLE_STATES)]
    if run_record is not None or diff is not None:
        _render_header_metrics(run_record, df_actionable, diff)
        _render_repaint_alarm(diff)
    else:
        st.metric("Aktif Sinyal", len(df_actionable))

    df = df_all if show_all_states else df_actionable
    df = df[df["indicator"].apply(lambda ind: CATALOG.get(ind, None) is not None
                                   and CATALOG[ind].category in selected_categories)]
    if direction_choice != "Hepsi":
        df = df[df["direction"] == direction_choice]
    if selected_tfs:
        df = df[df["timeframe"].str.lower().isin([t.lower() for t in selected_tfs])]
    if symbol_query:
        df = df[df["symbol"].str.upper().str.contains(symbol_query, regex=False)]
    df = df.sort_values("detected_at", ascending=False).reset_index(drop=True)

    if df.empty:
        st.info("Seçili filtrelerle eşleşen sinyal yok.")
        return
    display_df = _to_display(df)
    event = st.dataframe(
        display_df[_DISPLAY_COLS], hide_index=True,
        on_select="rerun", selection_mode="single-row", key=f"{key_prefix}_table",
    )
    selected_rows = list(event.selection.rows) if event and event.selection else []
    if selected_rows:
        row = df.iloc[selected_rows[0]]
        _goto(
            "chart", chart_symbol=row["symbol"], chart_indicator=row["indicator"],
            chart_tf=row["timeframe"],
        )


def _render_results_screen(market: str) -> None:
    """Ekran 2 — TEK bir taramanın (run) sinyal listesi. Bir satıra
    tıklamak OTOMATİK olarak Grafik Detayı'na geçer."""
    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.info("Önce sol menüden **Stratejiler** ile bir tarama çalıştırın ya da seçin.")
        if st.button("← Ana Sayfaya Dön"):
            _goto("home")
        return
    if st.button("← Ana Sayfaya Dön"):
        _goto("home")

    with ResultsStore() as store:
        run_record = store.get_run(run_id)
        other_runs = [r for r in store.list_runs(market, status="completed") if r != run_id]
        diff = store.diff(other_runs[0], run_id) if other_runs else None
    rows = _cached_run_rows(run_id)

    # `st.multiselect`'in `default=` parametresi yalnızca widget'ın bu
    # `key`le İLK KEZ oluşturulduğu anda etkilidir — aynı `key` (burada
    # sabit "results_cat") ile sonraki her rerun'da Streamlit `session_
    # state`teki SAKLI değeri kullanır, `default` göz ardı edilir. Bu
    # yüzden bir stratejiden gelen `active_categories`'i widget'a `default`
    # olarak vermek TEK BAŞINA yetmiyordu (kategori filtresi Sonuç
    # Listesi'ne daha önce hiç girilmemişse çalışırdı, ama ikinci bir
    # ziyarette ESKİ seçim yapışıp kalırdı). `_goto`'nun bıraktığı bu
    # navigasyona-özgü değeri BİR KEZ tüketip widget'ın session_state
    # anahtarına DOĞRUDAN yazıyoruz (widget çağrılmadan ÖNCE) — sonraki
    # rerun'larda anahtar session_state'te zaten olduğu için bu blok hiç
    # çalışmaz, kullanıcının kendi elle yaptığı filtre değişikliği ASLA
    # ezilmez.
    _NO_NAV = object()
    pending_categories = st.session_state.pop("active_categories", _NO_NAV)
    if pending_categories is not _NO_NAV:
        all_cats = sorted({spec.category for spec in CATALOG.values()})
        st.session_state["results_cat"] = (
            [c for c in pending_categories if c in all_cats] if pending_categories else all_cats
        )

    _render_signal_table(rows, key_prefix="results", run_record=run_record, diff=diff)


def _render_all_signals_screen(market: str) -> None:
    """'Tüm Sinyaller' — kullanıcı farklı zamanlarda farklı stratejiler
    taradıkça (her biri KENDİ `run_id`'sinde) tek bir run'a bakan Sonuç
    Listesi bunların hiçbirini birleştirmiyordu. Kullanıcı geri bildirimi:
    "hem strateji bazlı hem de genel olarak sinyal aldığım hisseleri
    görüntüleyemiyorum". DB katmanı (`ResultsStore`) zaten TÜM geçmiş
    run'ları saklıyordu — eksik olan, birden fazla run'ı tek listede
    birleştiren bu ekrandı. Son `_ALL_SIGNALS_MAX_RUNS` tamamlanmış run
    birleştirilir; `_rows_to_frame` her (sembol,tf,indikatör,pattern_id)
    zinciri için zaten yalnızca EN GÜNCEL durumu tutuyor (bkz. modül
    docstring'i), bu yüzden farklı run'lardan gelen satırlar da doğru
    şekilde dedup edilir."""
    if st.button("← Ana Sayfaya Dön", key="all_signals_back"):
        _goto("home")
    st.subheader("🗂 Tüm Sinyaller — Geçmiş Taramaların Birleşimi")

    with ResultsStore() as store:
        run_ids = store.list_runs(market, status="completed")
    if not run_ids:
        st.info("Henüz tamamlanmış bir tarama yok.")
        return
    recent_run_ids = tuple(run_ids[:_ALL_SIGNALS_MAX_RUNS])
    rows = _cached_multi_run_rows(recent_run_ids)

    st.caption(
        f"Son {len(recent_run_ids)} tamamlanmış taramanın (farklı stratejiler dahil) "
        "birleşimi — her (sembol, zaman dilimi, indikatör) zinciri için yalnızca en "
        "güncel durum gösterilir."
    )
    _render_signal_table(rows, key_prefix="all_signals")


def _render_chart_screen(market: str, theme: str) -> None:
    """Ekran 3 — sembol/gösterge/TF seçici + grafik + indirme + okuma
    rehberi + AI rapor. Ekran 2'de seçilen satırdan `st.session_state`
    üzerinden ön-doldurulur, her zaman elle değiştirilebilir."""
    if st.button("← Sonuçlara Dön"):
        _goto("results")

    default_symbol = st.session_state.get("chart_symbol", "")
    default_indicator = st.session_state.get("chart_indicator", "harmonic.pesavento")
    default_tf = st.session_state.get("chart_tf", "1d")

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

    if not symbol:
        st.info("Bir sembol gir ya da 2 · Sonuç Listesi ekranından bir satır seç.")
        return
    try:
        with st.spinner("Grafik oluşturuluyor..."):
            fig = _cached_chart_figure(
                chosen_key, symbol, tf, market, theme, date.today().isoformat(),
            )
    except (ValueError, FileNotFoundError) as exc:
        st.error(f"Grafik oluşturulamadı: {exc}")
        return

    refresh_col, _spacer = st.columns([1, 5])
    if refresh_col.button(
        "🔄 Yenile", help="Bugün yeni bir tarama/veri güncellemesi yaptıysan önbelleği temizler.",
    ):
        _cached_chart_figure.clear()
        st.rerun()

    st.plotly_chart(fig, width="stretch")

    # PNG dışa aktarımı (kaleido) artık İSTEĞE BAĞLI — eskiden her rerun'da
    # koşulsuz çağrılıyordu, kaleido'nun headless-Chrome başlatma maliyeti
    # yüzünden tek başına ana yavaşlık kaynaklarından biriydi.
    png_key = (symbol, chosen_key, tf)
    if st.session_state.get("chart_png_key") != png_key:
        st.session_state["chart_png_key"] = png_key
        st.session_state["chart_png_bytes"] = None
    dl_col1, dl_col2 = st.columns([1, 1])
    if dl_col1.button("🖼️ PNG Oluştur", width="stretch"):
        with st.spinner("PNG oluşturuluyor..."):
            try:
                st.session_state["chart_png_bytes"] = fig.to_image(format="png", scale=2)
            except Exception:  # kaleido/chrome eksikse sessizce atlanır
                st.session_state["chart_png_bytes"] = None
                st.warning("PNG oluşturulamadı (kaleido/chrome eksik olabilir).")
    if st.session_state.get("chart_png_bytes"):
        dl_col2.download_button(
            "⬇ Grafiği İndir (PNG)", data=st.session_state["chart_png_bytes"],
            file_name=f"{symbol}_{chosen_key}_{tf}.png", mime="image/png", width="stretch",
        )
    _render_reading_guide(chosen_key)
    st.divider()
    _render_ai_report_button(chosen_key, symbol, tf, market)


def main() -> None:
    round_favicon = _ensure_round_favicon()
    st.set_page_config(
        page_title="QuaxisLabs Tarama Panosu", layout="wide",
        page_icon=str(round_favicon) if round_favicon else "📊",
    )
    _restore_state_from_query_params()
    st.session_state.setdefault("screen", "home")

    market = _render_sidebar()
    theme = _render_top_bar()
    _inject_theme_css(theme)
    _render_step_indicator()

    screen = st.session_state["screen"]
    if screen == "home":
        _render_home_screen(market)
    elif screen == "strategy_detail":
        _render_strategy_detail_screen(market)
    elif screen == "results":
        _render_results_screen(market)
    elif screen == "all_signals":
        _render_all_signals_screen(market)
    else:
        _render_chart_screen(market, theme)


main()
