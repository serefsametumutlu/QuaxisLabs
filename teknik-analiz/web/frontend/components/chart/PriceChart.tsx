"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  createChart,
  CandlestickSeries,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from "lightweight-charts";
import type { Box, IndicatorResultJson, Level, Line, Marker, OhlcvBar, Polygon } from "@/lib/types";

interface Props {
  ohlcv: OhlcvBar[];
  result: IndicatorResultJson;
}

/** `style` metnine göre kaba bir renk sınıflandırması — Calm-Trading-UI'nin
 * 4 aksan rengine (accent/danger/warning/info) eşler. `renderer.py`'nin
 * `themes.py::_LINE_STYLE_COLOR` haritasının basitleştirilmiş hâli — tam
 * eşleme YOK, "boğa/ayı/uyarı/nötr" kabaca ayrımı yeterli (Faz 1 kapsamı). */
function styleColor(style: string, theme: Record<string, string>): string {
  const s = style.toLowerCase();
  if (/(bull|demand|support|confirmed|target|golden|accent)/.test(s)) return theme.accent;
  if (/(bear|supply|resistance|danger|invalidated|fail)/.test(s)) return theme.danger;
  if (/(warn|pending|active|pole)/.test(s)) return theme.warning;
  return theme.info;
}

// `renderer.py::_display_text`'in basitleştirilmiş TS karşılığı — bazı
// indikatörler (harmonik) `Level.label`'da eşleştirme amaçlı ham bir
// dahili kimlik taşıyabilir (ör. "carney_gartley_12_18_24_30_prz_low");
// bilinen bir son ek varsa kısa Türkçe karşılığı, yoksa (boşluksuz + ≥2
// alt çizgi deseni) `style`in kendisi gösterilir.
const LABEL_SUFFIX_TR: Record<string, string> = {
  _xb: "X-B",
  _xd_envelope: "Hedef Zarfı",
  _prz_low: "PRZ Alt",
  _prz_high: "PRZ Üst",
};
function looksLikeRawId(label: string): boolean {
  return !label.includes(" ") && (label.match(/_/g)?.length ?? 0) >= 2;
}
function displayText(label: string, style: string): string {
  for (const [suffix, short] of Object.entries(LABEL_SUFFIX_TR)) {
    if (label.endsWith(suffix)) return short;
  }
  if (looksLikeRawId(label)) return style;
  return label;
}

function isoToUnix(iso: string): number {
  return Math.floor(new Date(iso).getTime() / 1000);
}

function readThemeColors(): Record<string, string> {
  const css = getComputedStyle(document.documentElement);
  const get = (name: string) => css.getPropertyValue(name).trim();
  return {
    bg: get("--clr-bg"),
    surface: get("--clr-surface-1"),
    border: get("--clr-border"),
    accent: get("--clr-accent"),
    danger: get("--clr-danger"),
    warning: get("--clr-warning"),
    info: get("--clr-info"),
    text1: get("--clr-text-1"),
    text2: get("--clr-text-2"),
    text3: get("--clr-text-3"),
  };
}

interface Geometry {
  levels: { x1: number; x2: number; y: number; color: string; label: string }[];
  lines: { d: string; color: string; label: string; labelX: number; labelY: number }[];
  boxes: { x: number; y: number; w: number; h: number; color: string; label: string }[];
  polygons: { d: string; color: string }[];
  markers: { x: number; y: number; text: string; color: string }[];
}

const EMPTY_GEOMETRY: Geometry = { levels: [], lines: [], boxes: [], polygons: [], markers: [] };

export function PriceChart({ ohlcv, result }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [geometry, setGeometry] = useState<Geometry>(EMPTY_GEOMETRY);
  const [size, setSize] = useState({ width: 900, height: 560 });

  const recompute = useCallback(() => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart || !series || !containerRef.current) return;
    const theme = readThemeColors();
    const timeScale = chart.timeScale();
    const range = timeScale.getVisibleRange();
    if (!range) return;
    const from = range.from as number;
    const to = range.to as number;
    const padding = (to - from) * 0.15;
    const inRange = (t: number) => t >= from - padding && t <= to + padding;
    const width = containerRef.current.clientWidth;

    const X = (iso: string): number | null => {
      const coord = timeScale.timeToCoordinate(isoToUnix(iso) as Time);
      return coord === null ? null : coord;
    };
    const Y = (price: number): number | null => series.priceToCoordinate(price);

    const levels: Geometry["levels"] = [];
    for (const lv of result.levels as Level[]) {
      const startT = lv.start ? isoToUnix(lv.start) : from;
      const endT = lv.end ? isoToUnix(lv.end) : to;
      if (!inRange(startT) && !inRange(endT) && !(startT <= from && endT >= to)) continue;
      const y = Y(lv.price);
      if (y === null) continue;
      const x1 = lv.start ? X(lv.start) ?? 0 : 0;
      const x2 = lv.end ? X(lv.end) ?? width : width;
      levels.push({ x1, x2, y, color: styleColor(lv.style, theme), label: displayText(lv.label, lv.style) });
    }

    // `renderer.py::_latest_per_group`'un basitleştirilmiş karşılığı: aynı
    // `style`'daki onlarca çizgi/kutu (ör. swing yapısı her pivot arası ayrı
    // bir "swing_N" segmenti taşır — ŞEKİL hep çizilir ama yalnızca stilin
    // EN GÜNCEL örneği METİN alır, gerisi sessiz kalır. "swing" stili hiç
    // metin almaz (kaynak sistemde de yalnızca HH/HL/LH/LL marker'ları
    // konuşur, bağlayıcı çizginin kendi iç kimliği — "swing_138" gibi —
    // hiçbir zaman ekrana yazılmaz)."
    const latestLineIdxByStyle = new Map<string, { idx: number; t: number }>();
    (result.lines as Line[]).forEach((ln, idx) => {
      if (ln.points.length === 0) return;
      const t = isoToUnix(ln.points[ln.points.length - 1][0]);
      const cur = latestLineIdxByStyle.get(ln.style);
      if (!cur || t >= cur.t) latestLineIdxByStyle.set(ln.style, { idx, t });
    });

    const lines: Geometry["lines"] = [];
    (result.lines as Line[]).forEach((ln, idx) => {
      const pts = ln.points;
      if (pts.length === 0) return;
      const lastT = isoToUnix(pts[pts.length - 1][0]);
      const anyVisible = pts.some(([t]) => inRange(isoToUnix(t))) || inRange(lastT);
      if (!anyVisible) return;
      const coords = pts
        .map(([t, p]) => {
          const x = X(t);
          const y = Y(p);
          return x !== null && y !== null ? `${x},${y}` : null;
        })
        .filter((v): v is string => v !== null);
      if (coords.length === 0) return;
      let d = `M ${coords.join(" L ")}`;
      let labelX = 0;
      let labelY = 0;
      const lastCoord = coords[coords.length - 1].split(",").map(Number);
      if (ln.extend_right) {
        d += ` L ${width},${lastCoord[1]}`;
        labelX = width - 8;
        labelY = lastCoord[1] - 6;
      } else {
        labelX = lastCoord[0] + 6;
        labelY = lastCoord[1] - 6;
      }
      const showLabel = ln.style !== "swing" && latestLineIdxByStyle.get(ln.style)?.idx === idx;
      lines.push({
        d,
        color: styleColor(ln.style, theme),
        label: showLabel ? displayText(ln.label, ln.style) : "",
        labelX,
        labelY,
      });
    });

    const boxes: Geometry["boxes"] = [];
    for (const bx of result.boxes as Box[]) {
      const t0 = isoToUnix(bx.t0);
      const t1 = isoToUnix(bx.t1);
      if (!inRange(t0) && !inRange(t1) && !(t0 <= from && t1 >= to)) continue;
      const x1 = X(bx.t0) ?? 0;
      const x2 = X(bx.t1) ?? width;
      const y1 = Y(bx.high);
      const y2 = Y(bx.low);
      if (y1 === null || y2 === null) continue;
      boxes.push({
        x: Math.min(x1, x2),
        y: y1,
        w: Math.abs(x2 - x1),
        h: y2 - y1,
        color: styleColor(bx.style, theme),
        label: bx.label,
      });
    }

    const polygons: Geometry["polygons"] = [];
    for (const pg of result.polygons as Polygon[]) {
      const anyVisible = pg.points.some(([t]) => inRange(isoToUnix(t)));
      if (!anyVisible) continue;
      const coords = pg.points
        .map(([t, p]) => {
          const x = X(t);
          const y = Y(p);
          return x !== null && y !== null ? `${x},${y}` : null;
        })
        .filter((v): v is string => v !== null);
      if (coords.length < 2) continue;
      polygons.push({ d: `M ${coords.join(" L ")} Z`, color: styleColor(pg.style, theme) });
    }

    const markers: Geometry["markers"] = [];
    for (const mk of result.markers as Marker[]) {
      const t = isoToUnix(mk.t);
      if (!inRange(t)) continue;
      const x = X(mk.t);
      const y = Y(mk.price);
      if (x === null || y === null) continue;
      markers.push({ x, y, text: mk.text, color: styleColor(mk.kind, theme) });
    }

    setGeometry({ levels, lines, boxes, polygons, markers });
  }, [result]);

  // Chart kurulumu — bir kez.
  useEffect(() => {
    if (!containerRef.current) return;
    const theme = readThemeColors();
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 560,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: theme.text2,
        fontFamily: "var(--font-body)",
      },
      grid: {
        vertLines: { color: theme.border },
        horzLines: { color: theme.border },
      },
      rightPriceScale: { borderColor: theme.border },
      timeScale: {
        borderColor: theme.border,
        rightOffset: 12, // son mumdan sonra boşluk — "mumlar sağa yapışık" şikayetinin doğrudan çözümü
        barSpacing: 8,
      },
      crosshair: { mode: 0 },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: theme.accent,
      downColor: theme.danger,
      borderVisible: false,
      wickUpColor: theme.accent,
      wickDownColor: theme.danger,
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const resizeObserver = new ResizeObserver((entries) => {
      const { width } = entries[0].contentRect;
      chart.applyOptions({ width });
      setSize((s) => ({ ...s, width }));
    });
    resizeObserver.observe(containerRef.current);

    const onVisibleRangeChange = () => recompute();
    chart.timeScale().subscribeVisibleTimeRangeChange(onVisibleRangeChange);

    return () => {
      chart.timeScale().unsubscribeVisibleTimeRangeChange(onVisibleRangeChange);
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Veri değişince mum verisini bas + görünür aralığı sıfırla.
  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart || ohlcv.length === 0) return;
    series.setData(
      ohlcv.map((b) => ({
        time: b.time as Time,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      }))
    );
    // `fitContent()` KULLANILMIYOR — tüm geçmişi (ör. 2.5 yıl) tek ekrana
    // sığdırmak, `renderer.py::_DEFAULT_LAST_N`'in de kaçındığı AYNI
    // "onlarca etiket üst üste biner" sorununu yaratıyordu (bkz. görev
    // notları). Varsayılan olarak yalnızca SON `DEFAULT_LAST_N` bar
    // gösterilir — kullanıcı isterse serbestçe geriye kaydırıp yakınlaştırabilir.
    const DEFAULT_LAST_N = 150;
    chart.timeScale().setVisibleLogicalRange({
      from: Math.max(0, ohlcv.length - DEFAULT_LAST_N),
      to: ohlcv.length - 1,
    });
    // `setVisibleLogicalRange`'in tetiklediği görünür-aralık değişimi zaten
    // recompute'u çağırır (subscribeVisibleTimeRangeChange), ama emin olmak
    // için bir sonraki frame'de de çağırıyoruz.
    requestAnimationFrame(recompute);
  }, [ohlcv, recompute]);

  return (
    <div className="relative w-full" style={{ height: 560 }}>
      <div ref={containerRef} className="absolute inset-0" />
      <svg
        className="absolute inset-0 pointer-events-none"
        width={size.width}
        height={560}
      >
        {geometry.boxes.map((b, i) => (
          <rect
            key={`box-${i}`}
            x={b.x}
            y={b.y}
            width={b.w}
            height={b.h}
            fill={b.color}
            fillOpacity={0.12}
            stroke={b.color}
            strokeOpacity={0.5}
            strokeWidth={1}
          />
        ))}
        {geometry.polygons.map((p, i) => (
          <path key={`poly-${i}`} d={p.d} fill={p.color} fillOpacity={0.14} stroke={p.color} strokeWidth={1.3} />
        ))}
        {geometry.levels.map((lv, i) => (
          <g key={`lv-${i}`}>
            <line x1={lv.x1} y1={lv.y} x2={lv.x2} y2={lv.y} stroke={lv.color} strokeWidth={1} strokeDasharray="4,3" opacity={0.8} />
            <text x={Math.max(lv.x1, lv.x2) + 4} y={lv.y - 4} fill={lv.color} fontSize={10.5} fontFamily="var(--font-mono)">
              {lv.label}
            </text>
          </g>
        ))}
        {geometry.lines.map((ln, i) => (
          <g key={`ln-${i}`}>
            <path d={ln.d} fill="none" stroke={ln.color} strokeWidth={1.4} opacity={0.85} />
            <text x={ln.labelX} y={ln.labelY} fill={ln.color} fontSize={10} textAnchor={ln.labelX > size.width - 80 ? "end" : "start"}>
              {ln.label}
            </text>
          </g>
        ))}
        {geometry.markers.map((mk, i) => (
          <g key={`mk-${i}`}>
            <circle cx={mk.x} cy={mk.y} r={3} fill={mk.color} />
            <text x={mk.x} y={mk.y - 8} fill={mk.color} fontSize={10} fontWeight={600} textAnchor="middle">
              {mk.text}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
