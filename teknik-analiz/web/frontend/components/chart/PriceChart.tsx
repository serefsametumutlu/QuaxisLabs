"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from "lightweight-charts";
import type { Box, ChartResponse, Level, Line, Marker, Polygon } from "@/lib/types";

interface Props {
  data: ChartResponse;
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
    up: get("--clr-up") || get("--clr-accent"),
    down: get("--clr-down") || get("--clr-danger"),
  };
}

interface LevelGeom {
  x1: number;
  x2: number;
  y: number;
  labelY: number;
  labelX: number;
  anchorEnd: boolean;
  color: string;
  label: string;
}
interface LineGeom {
  d: string;
  color: string;
  label: string;
  labelX: number;
  labelY: number;
}
interface BoxGeom {
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  label: string;
  labelX: number;
  labelY: number;
}
interface VpBarGeom {
  y: number;
  w: number;
  h: number;
  color: string;
}

interface Geometry {
  levels: LevelGeom[];
  lines: LineGeom[];
  boxes: BoxGeom[];
  polygons: { d: string; color: string }[];
  markers: { x: number; y: number; text: string; color: string }[];
  vpBars: VpBarGeom[];
  vpGaussPath: string;
}

const EMPTY_GEOMETRY: Geometry = {
  levels: [],
  lines: [],
  boxes: [],
  polygons: [],
  markers: [],
  vpBars: [],
  vpGaussPath: "",
};

const VP_COLUMN_WIDTH = 90;

/** Aynı gruptaki (ör. aynı `style`) onlarca satırdan yalnızca EN GÜNCEL
 * (zamanı en büyük) olanın METNİ gösterilir — `renderer.py::_latest_per_
 * group`'un basitleştirilmiş TS karşılığı. Şekil (çizgi/kutu) HER ZAMAN
 * çizilir, yalnızca etiket METNİ kısıtlanır. */
function pickLatestPerGroup<T>(items: T[], groupKey: (t: T) => string, time: (t: T) => number): Set<number> {
  const best = new Map<string, { idx: number; t: number }>();
  items.forEach((item, idx) => {
    const g = groupKey(item);
    const t = time(item);
    const cur = best.get(g);
    if (!cur || t >= cur.t) best.set(g, { idx, t });
  });
  return new Set(Array.from(best.values()).map((v) => v.idx));
}

/** Fiyata göre yakın levellerin metinleri üst üste binmesin diye dikey
 * "merdiven": önce fiyata (dolayısıyla piksel-Y'ye) göre sıralanır, her
 * öğe bir öncekinden en az `minGap` piksel aşağıda kalacak şekilde metin
 * Y'si (yalnızca metin — çizginin KENDİSİ hep gerçek fiyatta kalır)
 * itilir. `renderer.py::_stagger_yshifts`in ÇOK basitleştirilmiş TS
 * karşılığı — genel bir yerleşim çözücü değil, tek geçişli açgözlü. */
function staggerLabelY(items: { y: number }[], minGap = 15): number[] {
  const order = items.map((_, i) => i).sort((a, b) => items[a].y - items[b].y);
  const labelY = items.map((it) => it.y);
  for (let k = 1; k < order.length; k++) {
    const prevIdx = order[k - 1];
    const curIdx = order[k];
    if (labelY[curIdx] - labelY[prevIdx] < minGap) {
      labelY[curIdx] = labelY[prevIdx] + minGap;
    }
  }
  return labelY;
}

export function PriceChart({ data }: Props) {
  const { ohlcv, result } = data;
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const paneSeriesRef = useRef<ISeriesApi<"Line" | "Histogram">[]>([]);
  const [geometry, setGeometry] = useState<Geometry>(EMPTY_GEOMETRY);
  const [size, setSize] = useState({ width: 900 });
  const [chartHeight, setChartHeight] = useState(480);

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
    const fullWidth = containerRef.current.clientWidth;
    const hasVp = (result.series.vp_volumes && Object.keys(result.series.vp_volumes).length > 0) ?? false;
    const width = hasVp ? fullWidth - VP_COLUMN_WIDTH : fullWidth;

    const X = (iso: string): number | null => {
      const coord = timeScale.timeToCoordinate(isoToUnix(iso) as Time);
      return coord === null ? null : coord;
    };
    const Y = (price: number): number | null => series.priceToCoordinate(price);

    const levelsRaw: { price: number; y: number; x1: number; x2: number; color: string; label: string }[] = [];
    for (const lv of result.levels as Level[]) {
      const startT = lv.start ? isoToUnix(lv.start) : from;
      const endT = lv.end ? isoToUnix(lv.end) : to;
      if (!inRange(startT) && !inRange(endT) && !(startT <= from && endT >= to)) continue;
      const y = Y(lv.price);
      if (y === null) continue;
      const x1 = lv.start ? X(lv.start) ?? 0 : 0;
      const x2 = lv.end ? X(lv.end) ?? width : width;
      levelsRaw.push({
        price: lv.price,
        y,
        x1,
        x2,
        color: styleColor(lv.style, theme),
        label: displayText(lv.label, lv.style),
      });
    }
    const staggeredY = staggerLabelY(levelsRaw, 20);
    // GERÇEK HATA (bulunup düzeltildi): `end=null` (henüz açık) levellerin
    // x2'si HAM `width`e (SVG'nin kendi genişliği) düşüyordu — metin
    // `x2+4`te, yani SVG sınırının HEMEN DIŞINDA, TAMAMEN KIRPILARAK
    // render ediliyordu (fib retracement/bearish D-hedef etiketleri hiç
    // görünmüyordu). Sağ kenara `~90px` yakın olan etiketler artık SOLA
    // doğru büyüyecek şekilde sağa hizalanıyor (`anchorEnd`).
    const RIGHT_MARGIN = 90;
    const levels: LevelGeom[] = levelsRaw.map((lv, i) => {
      const rawX2 = Math.max(lv.x1, lv.x2);
      const anchorEnd = rawX2 > width - RIGHT_MARGIN;
      return {
        x1: lv.x1,
        x2: lv.x2,
        y: lv.y,
        labelY: staggeredY[i],
        labelX: anchorEnd ? width - 4 : rawX2 + 4,
        anchorEnd,
        color: lv.color,
        label: lv.label,
      };
    });

    const latestLineIdx = pickLatestPerGroup(
      result.lines as Line[],
      (ln) => ln.style,
      (ln) => (ln.points.length ? isoToUnix(ln.points[ln.points.length - 1][0]) : 0)
    );
    const lines: LineGeom[] = [];
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
      const showLabel = ln.style !== "swing" && latestLineIdx.has(idx);
      lines.push({
        d,
        color: styleColor(ln.style, theme),
        label: showLabel ? displayText(ln.label, ln.style) : "",
        labelX,
        labelY,
      });
    });

    const latestBoxIdx = pickLatestPerGroup(
      result.boxes as Box[],
      (bx) => bx.style,
      (bx) => isoToUnix(bx.t1)
    );
    const boxes: BoxGeom[] = [];
    (result.boxes as Box[]).forEach((bx, idx) => {
      const t0 = isoToUnix(bx.t0);
      const t1 = isoToUnix(bx.t1);
      if (!inRange(t0) && !inRange(t1) && !(t0 <= from && t1 >= to)) return;
      const x1 = X(bx.t0) ?? 0;
      const x2 = X(bx.t1) ?? width;
      const y1 = Y(bx.high);
      const y2 = Y(bx.low);
      if (y1 === null || y2 === null) return;
      boxes.push({
        x: Math.min(x1, x2),
        y: y1,
        w: Math.abs(x2 - x1),
        h: y2 - y1,
        color: styleColor(bx.style, theme),
        label: latestBoxIdx.has(idx) ? displayText(bx.label, bx.style) : "",
        labelX: Math.min(x1, x2) + 4,
        labelY: y1 + 12,
      });
    });

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

    // Hacim profili (fiyat-indeksli vp_bins/vp_volumes/vp_hvn) — sağ kenara
    // sabit genişlikte bir sütun, gerçek `priceToCoordinate` ile hizalı.
    const vpBars: VpBarGeom[] = [];
    let vpGaussPath = "";
    if (hasVp) {
      const volEntries = Object.entries(result.series.vp_volumes ?? {});
      const hvnMap = result.series.vp_hvn ?? {};
      const maxVol = Math.max(...volEntries.map(([, v]) => v ?? 0), 1);
      const barMaxW = VP_COLUMN_WIDTH - 8;
      const priceStep =
        volEntries.length > 1
          ? Math.abs(parseFloat(volEntries[1][0]) - parseFloat(volEntries[0][0]))
          : 1;
      for (const [priceStr, vol] of volEntries) {
        const price = parseFloat(priceStr);
        const yMid = Y(price);
        if (yMid === null || vol === null) continue;
        const halfPx = (Y(price - priceStep / 2) ?? yMid) - (Y(price + priceStep / 2) ?? yMid);
        const h = Math.max(1.5, Math.abs(halfPx));
        const w = (vol / maxVol) * barMaxW;
        const isHvn = (hvnMap[priceStr] ?? 0) > 0;
        vpBars.push({
          y: yMid - h / 2,
          w,
          h,
          color: isHvn ? theme.up : theme.info,
        });
      }
      const gaussEntries = Object.entries(result.series.vp_gauss ?? {});
      if (gaussEntries.length > 1) {
        const maxG = Math.max(...gaussEntries.map(([, v]) => v ?? 0), 1e-9);
        const pts = gaussEntries
          .map(([priceStr, v]) => {
            const y = Y(parseFloat(priceStr));
            if (y === null || v === null) return null;
            const x = width + 4 + (v / maxG) * (barMaxW - 4);
            return `${x},${y}`;
          })
          .filter((v): v is string => v !== null);
        if (pts.length > 1) vpGaussPath = `M ${pts.join(" L ")}`;
      }
    }

    setGeometry({ levels, lines, boxes, polygons, markers, vpBars, vpGaussPath });
  }, [result]);

  // Chart kurulumu — bir kez.
  useEffect(() => {
    if (!containerRef.current) return;
    const theme = readThemeColors();
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: chartHeight,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: theme.text2,
        fontFamily: "var(--font-body)",
        panes: { separatorColor: theme.border },
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
      upColor: theme.up,
      downColor: theme.down,
      borderVisible: false,
      wickUpColor: theme.up,
      wickDownColor: theme.down,
    });
    chartRef.current = chart;
    seriesRef.current = series;
    // React StrictMode (dev) mount/unmount/remount yapar — `chart.remove()`
    // ile ATILAN bir önceki chart'ın pane series referansları burada
    // sıfırlanmazsa, veri-değişim effect'i onları YENİ chart üzerinde
    // silmeye çalışıp "Value is undefined" runtime hatası veriyordu.
    paneSeriesRef.current = [];

    const resizeObserver = new ResizeObserver((entries) => {
      const { width } = entries[0].contentRect;
      chart.applyOptions({ width });
      setSize({ width });
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

  // Veri/gösterge değişince: mum + alt panelleri (hacim/MACD/RSI) baştan kurar.
  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart || ohlcv.length === 0) return;
    const theme = readThemeColors();

    series.setData(
      ohlcv.map((b) => ({
        time: b.time as Time,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      }))
    );

    for (const s of paneSeriesRef.current) chart.removeSeries(s);
    paneSeriesRef.current = [];
    while (chart.panes().length > 1) chart.removePane(chart.panes().length - 1);

    const panelKeys = Object.keys(result.series_layout ?? {});
    const lineColors = [theme.info, theme.accent, theme.warning];
    panelKeys.forEach((panelKey, paneOffset) => {
      const paneIndex = paneOffset + 1;
      const seriesNames = result.series_layout[panelKey];
      let colorCursor = 0;
      for (const name of seriesNames) {
        const raw = result.series[name] ?? {};
        const isHist = /hist|volume$/i.test(name) && name !== "volume_ma";
        if (isHist) {
          const closeByTime = new Map(ohlcv.map((b) => [b.time, b.close]));
          const openByTime = new Map(ohlcv.map((b) => [b.time, b.open]));
          const hist = chart.addSeries(
            HistogramSeries,
            {
              color: theme.info,
              priceLineVisible: false,
              lastValueVisible: false,
              // "volume" gibi büyük sayılar (20000000.00) yerine kompakt
              // format (20M) — yalnızca hacim/hacim-benzeri serilerde.
              priceFormat: name === "volume" ? { type: "volume" } : undefined,
            },
            paneIndex
          );
          hist.setData(
            Object.entries(raw)
              .map(([iso, v]) => {
                const t = isoToUnix(iso) as Time;
                let color = theme.info;
                if (name === "volume") {
                  const o = openByTime.get(t as unknown as number);
                  const c = closeByTime.get(t as unknown as number);
                  color = c !== undefined && o !== undefined && c >= o ? theme.up : theme.down;
                } else if (v !== null) {
                  color = v >= 0 ? theme.up : theme.down;
                }
                return v === null ? null : { time: t, value: v, color };
              })
              .filter((v): v is { time: Time; value: number; color: string } => v !== null)
          );
          paneSeriesRef.current.push(hist);
        } else {
          const color = lineColors[colorCursor % lineColors.length];
          colorCursor += 1;
          const line = chart.addSeries(
            LineSeries,
            { color, lineWidth: 1, priceLineVisible: false, lastValueVisible: false },
            paneIndex
          );
          line.setData(
            Object.entries(raw)
              .map(([iso, v]) => (v === null ? null : { time: isoToUnix(iso) as Time, value: v }))
              .filter((v): v is { time: Time; value: number } => v !== null)
          );
          if (name === "rsi_14") {
            line.createPriceLine({ price: 70, color: theme.danger, lineWidth: 1, lineStyle: 2, title: "70" });
            line.createPriceLine({ price: 30, color: theme.up, lineWidth: 1, lineStyle: 2, title: "30" });
          }
          paneSeriesRef.current.push(line);
        }
      }
      chart.panes()[paneIndex]?.setHeight(120);
    });

    const priceHeight = 480;
    const totalHeight = priceHeight + panelKeys.length * 120;
    setChartHeight(totalHeight);
    chart.resize(containerRef.current?.clientWidth ?? size.width, totalHeight);
    chart.panes()[0]?.setHeight(priceHeight);

    const DEFAULT_LAST_N = 150;
    chart.timeScale().setVisibleLogicalRange({
      from: Math.max(0, ohlcv.length - DEFAULT_LAST_N),
      to: ohlcv.length - 1,
    });
    requestAnimationFrame(recompute);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const exportPng = useCallback(() => {
    const chart = chartRef.current;
    const container = containerRef.current;
    if (!chart || !container) return;
    const chartCanvas = chart.takeScreenshot();
    const svgEl = container.parentElement?.querySelector("svg.overlay-svg");
    const finalCanvas = document.createElement("canvas");
    finalCanvas.width = chartCanvas.width;
    finalCanvas.height = chartCanvas.height;
    const ctx = finalCanvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(chartCanvas, 0, 0);
    const finish = () => {
      const url = finalCanvas.toDataURL("image/png");
      const a = document.createElement("a");
      a.href = url;
      a.download = `${data.symbol}_${result.indicator}_${data.tf}.png`;
      a.click();
    };
    if (svgEl) {
      const svgData = new XMLSerializer().serializeToString(svgEl);
      const svgUrl = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
      const img = new Image();
      img.onload = () => {
        // SVG CSS-piksel boyutunda (container.clientWidth × chartHeight);
        // `chartCanvas` cihaz piksel oranına göre daha büyük olabilir —
        // drawImage hedef dikdörtgene göre otomatik ölçekler.
        ctx.drawImage(img, 0, 0, chartCanvas.width, chartCanvas.height);
        finish();
      };
      img.onerror = finish;
      img.src = svgUrl;
    } else {
      finish();
    }
  }, [data, result.indicator]);

  return (
    <div className="relative w-full">
      <button
        onClick={exportPng}
        className="absolute right-1 top-1 z-10 rounded border border-border bg-surface-1/90 px-2 py-1 text-xs text-text-2 hover:border-accent hover:text-text-1"
      >
        PNG indir
      </button>
      <div className="relative w-full" style={{ height: chartHeight }}>
        <div
          ref={containerRef}
          className="absolute inset-y-0 left-0"
          style={{ width: geometry.vpBars.length ? `calc(100% - ${VP_COLUMN_WIDTH}px)` : "100%" }}
        />
        <svg className="overlay-svg absolute inset-0 pointer-events-none" width={size.width} height={chartHeight}>
          {geometry.boxes.map((b, i) => (
            <g key={`box-${i}`}>
              <rect x={b.x} y={b.y} width={b.w} height={b.h} fill={b.color} fillOpacity={0.12} stroke={b.color} strokeOpacity={0.5} strokeWidth={1} />
              {b.label && (
                <text x={b.labelX} y={b.labelY} fill={b.color} fontSize={10} fontFamily="var(--font-body)">
                  {b.label}
                </text>
              )}
            </g>
          ))}
          {geometry.polygons.map((p, i) => (
            <path key={`poly-${i}`} d={p.d} fill={p.color} fillOpacity={0.14} stroke={p.color} strokeWidth={1.3} />
          ))}
          {geometry.levels.map((lv, i) => (
            <g key={`lv-${i}`}>
              <line x1={lv.x1} y1={lv.y} x2={lv.x2} y2={lv.y} stroke={lv.color} strokeWidth={1} strokeDasharray="4,3" opacity={0.8} />
              <text
                x={lv.labelX}
                y={lv.labelY}
                fill={lv.color}
                fontSize={10.5}
                fontFamily="var(--font-mono)"
                textAnchor={lv.anchorEnd ? "end" : "start"}
              >
                {lv.label}
              </text>
            </g>
          ))}
          {geometry.lines.map((ln, i) => (
            <g key={`ln-${i}`}>
              <path d={ln.d} fill="none" stroke={ln.color} strokeWidth={1.4} opacity={0.85} />
              {ln.label && (
                <text x={ln.labelX} y={ln.labelY} fill={ln.color} fontSize={10} textAnchor={ln.labelX > size.width - 80 ? "end" : "start"}>
                  {ln.label}
                </text>
              )}
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
          {geometry.vpBars.length > 0 && (
            <g transform={`translate(${size.width - VP_COLUMN_WIDTH},0)`}>
              {geometry.vpBars.map((v, i) => (
                <rect key={`vp-${i}`} x={0} y={v.y} width={v.w} height={v.h} fill={v.color} fillOpacity={0.55} />
              ))}
            </g>
          )}
          {geometry.vpGaussPath && (
            <path d={geometry.vpGaussPath} fill="none" stroke="currentColor" className="text-accent" strokeWidth={1.3} opacity={0.85} />
          )}
        </svg>
      </div>
    </div>
  );
}
