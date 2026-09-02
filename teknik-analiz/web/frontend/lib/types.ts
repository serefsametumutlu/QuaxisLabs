// tlab/core/types.py::IndicatorResult ve primitiflerinin (Level/Line/Box/
// Polygon/Marker) TypeScript karşılığı — backend'in `/api/chart` endpoint'i
// bu şekli aynen döner (bkz. web/backend/routes/chart.py).

export interface Level {
  price: number;
  label: string;
  style: string;
  start: string | null;
  end: string | null;
}

export interface Line {
  points: [string, number][];
  label: string;
  style: string;
  extend_right: boolean;
}

export interface Box {
  t0: string;
  t1: string;
  low: number;
  high: number;
  label: string;
  style: string;
}

export interface Polygon {
  points: [string, number][];
  label: string;
  style: string;
}

export interface Marker {
  t: string;
  price: number;
  text: string;
  kind: string;
}

export interface Signal {
  bar_time: string;
  detected_at: string;
  direction: string;
  state: string;
  score: number;
  payload: Record<string, unknown>;
}

export interface IndicatorResultJson {
  indicator: string;
  version: string;
  params_hash: string;
  symbol: string;
  timeframe: string;
  signals: Signal[];
  levels: Level[];
  lines: Line[];
  boxes: Box[];
  polygons: Polygon[];
  markers: Marker[];
  series: Record<string, Record<string, number | null>>;
  series_layout: Record<string, string[]>;
  last_state: Record<string, unknown>;
}

export interface OhlcvBar {
  time: number; // unix saniye (UTC)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartResponse {
  symbol: string;
  market: string;
  tf: string;
  ohlcv: OhlcvBar[];
  result: IndicatorResultJson;
}

export interface CatalogEntry {
  name: string;
  category: string;
  needs_context: boolean;
  needs_universe: boolean;
}
