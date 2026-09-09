"""Çok panelli grafik iskeleti — paylaşılan x ekseni, panel başına BAĞIMSIZ y.

`tlab/viz/renderer.py`'nin K2 hatası (alt panellerin y aralığının tüm
geçmişten ölçeklenmesi; MACD −40..+20 aralığında −5..+5 veri çizilmesi)
burada YAPISAL olarak imkânsız: `Panel.autorange()` her panelin y sınırını
YALNIZCA o panele verilen serilerden hesaplar, ortak bir havuzdan değil.

Etkileşim sözleşmesi (kullanıcının 2026-09-08 isteği):
  - `hovermode="x unified"` — imleç nereye giderse o bardaki TÜM seriler
    tek kutuda görünür (fiyat + hacim + gösterge).
  - dikey crosshair (`spikemode`) tüm panellerde ortak.
  - zaman aralığı düğmeleri (3A/6A/1Y/Tümü) fiyat panelinin x ekseninde.
Bu üçü ancak grafiğin TARAYICIDA plotly.js ile çizilmesiyle çalışır;
sunucuda PNG'ye rasterleştirilen sürümde sessizce devre dışı kalırlar
(aynı figür tanımı iki çıktıyı da besler).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tlab.chart.tokens import METRICS, ThemeName, palette


@dataclass
class Panel:
    """Tek bir alt panel. `key` eksen adreslemesi için (1'den başlar)."""

    name: str
    height_ratio: float
    y_title: str = ""
    y_range: tuple[float, float] | None = None
    y_tickformat: str | None = None
    # İKİNCİL y ekseni: aynı panelde ölçekleri farklı iki seri
    # (referans HRcUk75bgAApv6n: solda korelasyon, sağda beta).
    # `make_subplots` seviyesinde tanımlanmak ZORUNDA -- sonradan
    # `add_trace(..., yaxis="y5")` demek alt-panelli figürde çalışmaz,
    # trace sessizce ilk panelin eksenine düşer ve ekrandan çıkar.
    secondary_y: bool = False
    y_side: str = "right"
    secondary_title: str = ""
    _values: list[float] = field(default_factory=list)
    _values2: list[float] = field(default_factory=list)

    def observe2(self, values) -> None:
        """İkincil eksene çizilecek seriyi kaydet."""
        s = pd.Series(values, dtype="float64").replace(
            [float("inf"), float("-inf")], pd.NA
        ).dropna()
        if len(s):
            self._values2.extend(s.tolist())

    def autorange2(self, pad: float = 0.06) -> tuple[float, float] | None:
        if not self._values2:
            return None
        lo, hi = min(self._values2), max(self._values2)
        if lo == hi:
            span = abs(lo) * 0.05 or 1.0
            return (lo - span, hi + span)
        span = hi - lo
        return (lo - span * pad, hi + span * pad)

    def observe(self, values) -> None:
        """Bu panele çizilecek bir seriyi y-aralığı hesabına dahil et."""
        s = pd.Series(values, dtype="float64").replace([float("inf"), float("-inf")], pd.NA)
        s = s.dropna()
        if len(s):
            self._values.extend(s.tolist())

    def autorange(self, pad: float = 0.06) -> tuple[float, float] | None:
        """SADECE bu panele verilen serilerden y sınırı. Sabit aralık
        verilmişse (RSI 0-100 gibi) ona dokunulmaz."""
        if self.y_range is not None:
            return self.y_range
        if not self._values:
            return None
        lo, hi = min(self._values), max(self._values)
        if lo == hi:
            span = abs(lo) * 0.05 or 1.0
            return (lo - span, hi + span)
        span = hi - lo
        return (lo - span * pad, hi + span * pad)


class ChartFrame:
    """Panelleri kurar, ortak x/hover/crosshair ayarlarını uygular."""

    def __init__(
        self,
        panels: list[Panel],
        theme: ThemeName = "light",
        title: str = "",
        subtitle: str = "",
        width: int = 1600,
        height: int = 900,
        rangeselector: bool = True,
    ) -> None:
        if not panels:
            raise ValueError("en az bir panel gerekli")
        self.panels = panels
        self.theme = theme
        self.pal = palette(theme)
        self.m = METRICS
        self.title = title
        self.subtitle = subtitle
        self.width = width
        self.height = height
        self.rangeselector = rangeselector
        self._index: dict[str, int] = {p.name: i + 1 for i, p in enumerate(panels)}
        # Sağ kenar etiketleri burada TOPLANIR, `finish()`'te çakışmaları
        # çözülerek basılır. Tek tek `add_annotation` ile basıldıklarında
        # birbirinin üstüne biniyorlardı (fibo merdiveninde `0.500` etiketi
        # `ALTIN BÖLGE` etiketinin altında kayboldu).
        self._edge: list[dict] = []

        total = sum(p.height_ratio for p in panels)
        self.fig = make_subplots(
            rows=len(panels), cols=1, shared_xaxes=True,
            vertical_spacing=self.m.panel_gap,
            row_heights=[p.height_ratio / total for p in panels],
            specs=[[{"secondary_y": p.secondary_y}] for p in panels],
        )

    def row(self, panel_name: str) -> int:
        try:
            return self._index[panel_name]
        except KeyError:
            raise ValueError(
                f"panel {panel_name!r} tanımlı değil — geçerli: {sorted(self._index)}"
            ) from None

    def yref(self, panel_name: str) -> str:
        r = self.row(panel_name)
        return "y" if r == 1 else f"y{r}"

    def xref(self, panel_name: str) -> str:
        r = self.row(panel_name)
        return "x" if r == 1 else f"x{r}"

    def add(self, trace, panel_name: str, *, observe=None, secondary: bool = False) -> None:
        """Trace ekle ve (verilmişse) y-aralığı hesabına kat."""
        panel = next(p for p in self.panels if p.name == panel_name)
        if secondary and not panel.secondary_y:
            raise ValueError(
                f"panel {panel_name!r} ikincil eksenle tanımlanmadı "
                "(Panel(..., secondary_y=True) gerekli)"
            )
        kw = {"secondary_y": secondary} if panel.secondary_y else {}
        self.fig.add_trace(trace, row=self.row(panel_name), col=1, **kw)
        if observe is not None:
            (panel.observe2 if secondary else panel.observe)(observe)

    def edge_label(
        self, panel: str, y: float, text: str, color: str, *, weight: int = 0,
    ) -> None:
        """Grafiğin SAĞ kenarına, y hizasında bir etiket kaydeder.

        `weight` büyük olan, çakışma çözümünde yerini korur (bölge başlığı
        gibi önemli etiketler kaymaz, fibo seviyeleri onların etrafından
        akar).
        """
        self._edge.append(
            {"panel": panel, "y": float(y), "text": text, "color": color, "weight": weight}
        )

    def _emit_edge_labels(self) -> None:
        """Kaydedilen sağ kenar etiketlerini çakışmasız biçimde basar.

        Yöntem: her etiketin piksel karşılığı hesaplanır, ağırlığa ve y'ye
        göre sıralanır, ardından birbirine `min_gap` pikselden yakın olanlar
        aşağı doğru itilir. İtme YALNIZCA etiketi kaydırır; gösterdiği
        çizgi/seviye yerinde kalır, yani sayı yanlış hizaya gelmez —
        etiketin ait olduğu değer metnin içinde zaten yazılı.
        """
        if not self._edge:
            return
        m = self.m
        line_h = m.font_label + 3
        total = sum(p.height_ratio for p in self.panels)
        plot_h = self.height - m.margin_t - m.margin_b

        by_panel: dict[str, list[dict]] = {}
        for item in self._edge:
            by_panel.setdefault(item["panel"], []).append(item)

        for panel_name, items in by_panel.items():
            panel = next(p for p in self.panels if p.name == panel_name)
            rng = panel.autorange()
            if rng is None:
                continue
            lo, hi = rng
            if hi <= lo:
                continue
            idx = self.row(panel_name) - 1
            above = sum(p.height_ratio for p in self.panels[:idx]) / total
            frac = panel.height_ratio / total
            top_px = m.margin_t + plot_h * (above + frac * self.m.panel_gap * 0)
            panel_px = plot_h * frac

            def to_px(y: float) -> float:
                return top_px + panel_px * (hi - y) / (hi - lo)

            for it in items:
                it["px"] = to_px(it["y"])
                # Çok satırlı etiket daha fazla dikey yer kaplar; tek satır
                # varsayılırsa üç satırlık bir bölge etiketi bir sonrakinin
                # üstüne biner (arz/talep grafiğinde tam olarak bu oldu).
                it["h"] = line_h * (it["text"].count("<br>") + 1) + 4
            # önce ağırlıklılar yerini alsın, sonra diğerleri onların etrafına
            items.sort(key=lambda it: (-it["weight"], it["px"]))
            placed: list[tuple[float, float]] = []      # (merkez, yükseklik)
            for it in items:
                px, h = it["px"], it["h"]
                moved = True
                while moved:
                    moved = False
                    for q, qh in placed:
                        if abs(px - q) < (h + qh) / 2:
                            px = q + (h + qh) / 2
                            moved = True
                placed.append((px, h))
                it["px_final"] = px

            for it in items:
                shift = it["px_final"] - it["px"]
                self.fig.add_annotation(
                    xref=f"{self.xref(panel_name)} domain", yref=self.yref(panel_name),
                    x=1.008, y=it["y"], yshift=-shift,
                    xanchor="left", yanchor="middle", showarrow=False,
                    align="left", text=it["text"],
                    font=dict(family=m.font_family, size=m.font_label, color=it["color"]),
                )

    def finish(self) -> go.Figure:
        p, m = self.pal, self.m
        n = len(self.panels)

        self.fig.update_layout(
            width=self.width, height=self.height,
            paper_bgcolor=p.bg, plot_bgcolor=p.panel_bg,
            font=dict(family=m.font_family, size=m.font_axis, color=p.text),
            margin=dict(l=m.margin_l, r=m.margin_r, t=m.margin_t, b=m.margin_b),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor=p.hover_bg, bordercolor=p.hover_border,
                font=dict(family=m.font_mono, size=m.font_label, color=p.text),
            ),
            showlegend=False,
            dragmode="pan",
        )

        if self.title:
            self.fig.add_annotation(
                x=0, y=1.0, xref="paper", yref="paper",
                xanchor="left", yanchor="bottom", yshift=34,
                text=f"<b>{self.title}</b>", showarrow=False,
                font=dict(family=m.font_family, size=m.font_title, color=p.text),
            )
        if self.subtitle:
            self.fig.add_annotation(
                x=0, y=1.0, xref="paper", yref="paper",
                xanchor="left", yanchor="bottom", yshift=16,
                text=self.subtitle, showarrow=False,
                font=dict(family=m.font_family, size=m.font_sub, color=p.text_muted),
            )

        for i, panel in enumerate(self.panels, start=1):
            xaxis = self.fig.layout[f"xaxis{'' if i == 1 else i}"]
            yaxis = self.fig.layout[f"yaxis{'' if i == 1 else i}"]

            xaxis.update(
                showgrid=True, gridcolor=p.grid, gridwidth=1,
                zeroline=False, linecolor=p.axis, showline=False,
                rangeslider=dict(visible=False),
                showspikes=True, spikemode="across", spikesnap="cursor",
                spikecolor=p.text_muted, spikethickness=1, spikedash="dot",
                tickfont=dict(color=p.text_muted, size=m.font_axis),
                # BİST hafta sonu/tatil boşluklarını kaldır: mumlar bitişik dursun
                rangebreaks=[dict(bounds=["sat", "mon"])],
            )
            yaxis.update(
                side=panel.y_side, showgrid=True, gridcolor=p.grid, gridwidth=1,
                zeroline=False, linecolor=p.axis, showline=False,
                tickfont=dict(color=p.text_muted, size=m.font_axis),
                title=dict(
                    text=panel.y_title,
                    font=dict(color=p.text_muted, size=m.font_label),
                ),
            )
            if panel.y_tickformat:
                yaxis.update(tickformat=panel.y_tickformat)
            rng = panel.autorange()
            if rng is not None:
                yaxis.update(range=list(rng))

            if panel.secondary_y:
                # make_subplots ikincil ekseni bir sonraki yaxis numarasına
                # koyar; onu panelin karşı tarafına al ve KENDİ verisinden
                # ölçekle (birincil eksenin aralığını miras almasın).
                sec = self.fig.layout[f"yaxis{i + 1}"]
                sec.update(
                    side="left" if panel.y_side == "right" else "right",
                    showgrid=False, zeroline=False,
                    tickfont=dict(color=p.text_muted, size=m.font_axis),
                    title=dict(
                        text=panel.secondary_title,
                        font=dict(color=p.text_muted, size=m.font_label),
                    ),
                )
                r2 = panel.autorange2()
                if r2 is not None:
                    sec.update(range=list(r2))

            if i < n:
                xaxis.update(showticklabels=False)

        # Eksen başlığı, sağ kenar etiketleriyle aynı şeridi paylaşıyor —
        # ikisi birden olursa başlık etiketlerin üstüne biniyor (fibo
        # grafiğinde "Fiyat" yazısı `0.786` etiketini kesti).
        if self._edge:
            for panel in self.panels:
                n_edge = sum(1 for e in self._edge if e["panel"] == panel.name)
                if not n_edge:
                    continue
                r = self.row(panel.name)
                ax = self.fig.layout[f"yaxis{'' if r == 1 else r}"]
                ax.title.text = ""
                # Etiket ÇOK yoğunsa (fibo merdiveni gibi) eksen rakamları da
                # etiketleri seviyeyi zaten fiyatıyla yazıyor, ikisi
                # birden üst üste biniyordu ("1.0 (X): 99.35" ile "100").
                if n_edge >= 6:
                    ax.showticklabels = False

        self._emit_edge_labels()

        if self.rangeselector:
            self.fig.layout.xaxis.update(
                rangeselector=dict(
                    buttons=[
                        dict(count=3, label="3A", step="month", stepmode="backward"),
                        dict(count=6, label="6A", step="month", stepmode="backward"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(step="all", label="Tümü"),
                    ],
                    bgcolor=p.panel_bg, activecolor=p.grid,
                    bordercolor=p.axis, borderwidth=1,
                    font=dict(color=p.text_muted, size=m.font_label),
                    x=1.0, xanchor="right", y=1.0, yanchor="bottom",
                )
            )
        return self.fig
