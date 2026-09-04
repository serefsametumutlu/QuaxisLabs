# Faz 3 — SVG Çizim Motoru (Çekirdek) — Tamamlama Raporu

**Tarih:** 2026-09-04 · **Kapsam:** `tlab/viz/svg/` + tek kanıt sahnesi
(`patterns.double_top_bottom`) + web entegrasyonu.

## Özet

`docs/design/grafik_stil_vitrini.html` (artifact, "Grafik Stil Vitrini") saf
SVG referansının altyapı katmanı (`seeded`/`svgLine`/`svgRect`/`svgPoly`/
`svgText`/`svgCircle`/`pill`/`makeChart`/`drawCandles`/`niceTicks`/
`priceLabels`/`xLabels`/`rightLabel`/`panelLabel`/`glowFilterDefs`/`THEMES`)
Python'a çevrildi (`tlab/viz/svg/`). Artifact'te YOK olan, bu fazın asıl
katkısı olan parça `layout.py::resolve_collisions` — genel amaçlı bir
etiket-çakışma çözücü (açgözlü + itme). `patterns.double_top_bottom` sahnesi
gerçek `IndicatorResult` verisiyle (uydurma değil) portlandı, 4 iterasyon
gerçek BIST verisiyle GÖRÜLEREK düzeltildi, 3 temada (classic/dark/
editorial) doğrulandı.

## Referans dosyasının bulunması (önemli bir yan not)

`docs/design/grafik_stil_vitrini.html`'in yerel kopyası, Claude.ai
Artifacts görüntüleyicisinin DIŞ çerçeve kabuğuydu (gerçek içerik bir
iframe'e dinamik yükleniyordu, tarayıcının "Kaynağı Görüntüle"si bunu
yakalamamış). Gerçek içerik, artifact'in kendi `claude.ai` URL'inden
(`Artifact(action="read")`) yeniden okunarak kurtarıldı.

## Modül yapısı

```
tlab/viz/svg/
  prim.py      -- svg_line/svg_rect/svg_poly/svg_text/svg_circle/pill/
                  glow_filter_defs/group/defs. XML kaçışı ZORUNLU (escape_xml).
  scale.py     -- Chart dataclass (X ekseni BAR-İNDEKSLİ, tarih değil --
                  hafta sonu boşluğu bu yüzden doğal olarak yok), nice_ticks,
                  pad_range, bar_index.
  candles.py   -- draw_candles (artifact'le birebir: gövde min 1.1px, fitil
                  ayrı, yukarı/aşağı renk temadan).
  axes.py      -- price_labels/x_labels/right_label/panel_label.
  layout.py    -- LabelBox/PlacedLabel/CollisionResult, resolve_collisions,
                  leader_line. SAF fonksiyon, SVG'den bağımsız.
  theme.py     -- SVGTheme + CLASSIC/DARK/EDITORIAL, artifact'in THEMES
                  sabitinden BİREBİR (bkz. aşağıdaki "tespit edilen fark").
  scenes/base.py -- Scene protokolü (SceneOut: title/subtitle/badge/
                  panels|two_up).
  scenes/double_top_bottom.py -- tek portlanmış sahne.
  __init__.py  -- render_svg(result, df, theme, last_n) -> str, supports().
```

## `layout.py::resolve_collisions` — mimari not

Plotly'de (ve artifact'in kendi el-ayarlı sahnelerinde) YOK olan yetenek.
Mevcut `renderer.py::_stagger_yshifts`/`_declutter_levels`in ilkel hâliydi
— onlar BİLGİ SİLEREK (yalnızca en güncel grubu göster) çözüyordu. Bu motor
"yerini bul, sığmıyorsa öncelikle ele (drop)" ilkesiyle çalışır: kutular
önceliğe göre sıralanır, her biri tercih sırasına göre (above/below/right/
left) denenir, çakışırsa dikey/yatay adımlarla itilir, hâlâ sığmazsa DROP
edilir (sessizce kaybolmaz, `CollisionResult.dropped` raporlar).

4 saf-fonksiyon testi (spec'in istediği BİREBİR 4 senaryo):
`test_two_overlapping_boxes_separate`, `test_box_hanging_off_bounds_is_pulled_inside`,
`test_fifty_boxes_at_one_point_drops_low_priority`, `test_resolve_collisions_is_deterministic`
— `tests/test_viz/test_svg/test_layout.py`.

## Tema — tespit edilen fark

`tlab/viz/themes.py::Theme.muted`, artifact'in `neckline` alanıyla YALNIZCA
editorial'da tam eşleşiyor (`#8c7d5f`) — classic'te `muted=#c7cdd6` ama
artifact `neckline=#8b93a1`, dark'ta `muted=#2a303c` ama artifact
`neckline=#565d6a`. Spec'in talimatına uyularak mevcut `Theme`'in yaklaşık
eşlemesi yerine artifact'in kendi hex değerleri temel alınan YENİ bir
`SVGTheme` dataclass'ı yazıldı (bkz. `theme.py` docstring'i).

## `patterns.double_top_bottom` sahnesi — veri-güdümlü tasarım

Artifact'in sahnesi (satır ~764-844) UYDURMA pivotlarla, sahneye özel el-
ayarlı ofsetlerle çiziyordu. Port edilen versiyon:

- Hologram/boyun/hedef/rozet hepsi gerçek `Level`/`Polygon`/`Marker`/
  `Signal` primitiflerinden okunur (`_group_patterns`).
- **TÜM değişken-konumlu etiketler** (boyun yazısı, kırılım, onay, hedef
  metni, hedef rozeti, AL/SAT) `layout.py::resolve_collisions`e verilir —
  hiçbiri elle konumlanmıyor (1. iterasyonda elle konumlanan hedef rozeti
  panel kenarını taşıyordu, bu yüzden rozet de collision havuzuna alındı).
- Durum rozeti (`ÇİFT TEPE/DİP · {ONAY|HEDEFE ULAŞTI|GEÇERSİZ|SÜRESİ DOLDU|
  OLUŞUYOR}`) `result.signals`daki GERÇEK olay geçmişinden (breakout/
  retest/completed/invalidated/expired) türetilir — `tlab/core/
  pattern_state.py::SUFFIX_LABEL_TR` ile aynı sözlük. GEÇERSİZ/SÜRESİ
  DOLDU'da hedef çizgisi/metni artık ÇİZİLMİYOR (3. iterasyonda "geçersiz
  bir formasyon hâlâ 'ONAY' rozeti taşıyordu" hatası bulunup düzeltildi).
- **Pencere seçimi** — CLAUDE.md'nin "Faz 0.5'te bulunan, henüz
  kapatılmamış" listesindeki **BULUNAN HATA 2**'nin (`tail(last_n)` sabit
  penceresi eski sinyalleri kadraj dışına atıyordu) bu sahnedeki çözümü:
  sabit "son N bar" yerine seçilen formasyonun p1 pivotundan son sinyaline
  kadar SIĞACAK bir pencere seçilir (`_pattern_window`).

## Doğrulama döngüsü (zorunlu, ≥3 iterasyon)

`scripts/render_svg_scene.py` ile gerçek BIST verisi (`data/ohlcv/bist/`
önbelleği) üzerinde SVG üretilip `resvg_py` ile PNG'ye çevrildi, PNG'ler
Read ile GÖRÜLDÜ. Önce/sonra görüntüleri `docs/design/iterasyon/` altında.

| İterasyon | Sembol | Tema | Bulunan/Düzeltilen |
|---|---|---|---|
| 1 | BAKAB | classic | Baseline çalışıyor; hedef rozeti panel kenarını taşıyor (elle konumlanmış, `resolve_collisions`e girmemiş); retest ("Onay: Test Tuttu") hiç çizilmiyor. |
| 2 | BAKAB | classic | Rozet `resolve_collisions`e taşındı (kenar taşması düzeldi); retest marker eklendi; "1"/"2" rozet dikey ofseti yön-tutarlı hâle getirildi. |
| 3 | BAKAB | dark, editorial; CELHA (tek sinyal) | 3 temada da doğrulandı (glow/renk/font birebir); tek-pattern (single-panel) yolu doğrulandı; TUCLK (3 aday, çoklu durum) ile "GEÇERSİZ" bir adayın hâlâ "ONAY" rozeti taşıdığı GERÇEK bir hata bulundu. |
| 4 | TUCLK | classic | Durum rozeti gerçek `breakout`/`retest`/`completed`/`invalidated`/`expired` sinyallerinden türetilecek şekilde düzeltildi; GEÇERSİZ/SÜRESİ DOLDU'da hedef çizgisi artık çizilmiyor. |

**Bilinen sınırlama:** proje önbelleğindeki (`data/ohlcv/bist/`) TÜM
semboller ~506 barlık (yfinance varsayılan derinliği) bir pencereye sahip —
spec'in istediği "çok uzun geçmişli sembol" senaryosu bu yüzden GERÇEK
anlamda test edilemedi; TUCLK'nin 3 eş-zamanlı aday/durum çeşitliliği
(ONAY/HEDEFE ULAŞTI/GEÇERSİZ) en yakın makul vekil olarak kullanıldı.

## Performans ölçümü (BAKAB, `patterns.double_top_bottom`, 20 tekrar ortalaması)

| Yol | Süre |
|---|---|
| SVG metin üretimi (`render_svg`) | **21.0 ms** |
| SVG + `resvg_py` PNG rasterleştirme | **142.5 ms** |
| Plotly figure üretimi (`render`) | 37.6 ms |
| Plotly + kaleido PNG (ısındıktan sonra, headless Chromium) | **1880.6 ms** |

SVG+resvg yolu, kaleido'ya göre PNG üretiminde **~13x daha hızlı** ve
Chromium alt-süreç bağımlılığı taşımıyor. Ham SVG metin üretimi de Plotly
figure kurulumundan ~%45 daha hızlı.

## Web entegrasyonu

- `tlab/viz/live.py::render_live` yeni `engine: Literal["svg","plotly"]`
  parametresi aldı. **Varsayılan `"plotly"`** — spec'in önerdiği "varsayılan
  svg"den BİLİNÇLİ bir sapma: 3 mevcut çağıran (`tlab/cli.py::plot`,
  `tlab/dashboard.py`, `tlab/viz/report.py::ensure_chart`) hâlâ koşulsuz
  `go.Figure` API'si kullanıyor, varsayılanı `svg` yapmak bunları SESSİZCE
  kırardı. SVG yolu yalnızca açıkça `engine="svg"` isteyen İKİ YENİ
  entegrasyon noktasından çalışır (aşağıda). `@overload` ile tiplenmiş —
  `engine="svg"` verilmeden çağıranlar mypy'de hâlâ saf `go.Figure` görür.
- `web/backend/routes/chart_svg.py` (YENİ): `GET /api/chart.svg ->
  image/svg+xml`. Portlanmamış bir gösterge istenirse 422 (sessizce
  Plotly'e düşmez).
- `web/backend/routes/chart_png.py`: artık `render_live(engine="svg")`
  çağırıyor — SVG sahnesi olan göstergeler için PNG `resvg_py` ile
  rasterleştirilir (kaleido'ya hiç uğramaz); portlanmamış göstergeler eski
  Plotly+kaleido yoluna otomatik düşer.
- `tests/test_viz/golden/svg_double_top_bottom_classic.svg` (YENİ): SVG
  metni üzerinden golden karşılaştırma (`test_golden.py`nin mevcut
  `--update-golden` makinesini paylaşır, yalnızca `ext="svg"`).

## Test

34 yeni test (`tests/test_viz/test_svg/`) + 1 yeni golden test = 35 yeni,
toplam **738 test yeşil** (`pytest -q -m "not network"`, 703→738). ruff
(baseline 19), mypy (baseline 1), lint_lookahead (mevcut 5 uyarı — hepsi
bu fazdan ÖNCEKİ dosyalarda, CLAUDE.md'nin "3" rakamı `coint_monitor.py`nin
eklenmesinden önceki bir oturuma ait, güncellenmesi gerekiyor ama bu fazın
kapsamı dışında) hepsi temiz/değişmedi.

## Bitti kriteri karşılaştırması

- [x] `tlab/viz/svg/` modülü + layout motoru + en az 12 yeni test (34 yazıldı).
- [x] `resolve_collisions` saf-fonksiyon testleri (4 senaryo).
- [x] `patterns.double_top_bottom` sahnesi 3 temada üretiliyor, PNG'leri
      GÖRÜLDÜ, 4 iterasyon (≥3 istenen), önce/sonra `docs/design/iterasyon/`.
- [x] `GET /api/chart.svg` çalışıyor (`TestClient` ile uçtan uca doğrulandı).
- [x] Grafik üretim süresi ölçüldü ve raporlandı (yukarıda).
- [x] `pytest -q -m "not network"` yeşil (738 geçti).
