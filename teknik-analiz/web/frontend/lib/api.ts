import type { CatalogEntry, CategoryEntry } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as { detail?: string }).detail ?? `İstek başarısız (${res.status})`
    );
  }
  return res.json() as Promise<T>;
}

export function fetchCatalog(): Promise<CatalogEntry[]> {
  return getJson<CatalogEntry[]>("/catalog");
}

export function fetchCategories(): Promise<CategoryEntry[]> {
  return getJson<CategoryEntry[]>("/categories");
}

export function fetchUniverse(market: string): Promise<string[]> {
  return getJson<string[]>(`/universe?market=${encodeURIComponent(market)}`);
}

export interface QuantReportResponse {
  text: string;
  used_ai: boolean;
  provider: string | null;
  note: string | null;
}

export function fetchReport(params: {
  symbol: string;
  tf: string;
  indicator: string;
  market: string;
}): Promise<QuantReportResponse> {
  const qs = new URLSearchParams(params).toString();
  return getJson<QuantReportResponse>(`/report?${qs}`);
}

export interface GuideEntry {
  watch: string;
  measures: string;
  values: string;
  signal: string;
}

export function fetchGuide(indicator: string): Promise<GuideEntry | null> {
  return getJson<GuideEntry | null>(`/guide?indicator=${encodeURIComponent(indicator)}`);
}

export interface ScanRun {
  run_id: string;
  started_at: string;
  finished_at: string | null;
  market: string;
  timeframes: string[];
  universe_size: number;
  status: string;
}

export function fetchRuns(market: string): Promise<ScanRun[]> {
  return getJson<ScanRun[]>(`/runs?market=${encodeURIComponent(market)}`);
}

export interface ScanSignal {
  symbol: string;
  timeframe: string;
  indicator: string;
  display_name: string;
  pattern_label: string | null;
  state: string;
  direction: string;
  score: number;
  bar_time: string;
  detected_at: string;
  pattern_id: string;
  payload: Record<string, unknown>;
}

export interface ScanSignalsResponse {
  signals: ScanSignal[];
  total: number;
  limit: number;
  offset: number;
}

export interface ScanJob {
  job_id: string;
  market: string;
  status: "queued" | "running" | "completed" | "failed" | "already_running";
  started_at: string;
  finished_at?: string;
  error?: string;
  result?: { run_id: string; status: string };
}

export async function startScan(market: string, force = false, category?: string): Promise<ScanJob> {
  const qs = new URLSearchParams({ market, force: String(force) });
  if (category) qs.set("category", category);
  const res = await fetch(`${API_BASE}/scan/start?${qs.toString()}`, { method: "POST" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `İstek başarısız (${res.status})`);
  }
  return res.json() as Promise<ScanJob>;
}

export function fetchScanStatus(jobId: string): Promise<ScanJob> {
  return getJson<ScanJob>(`/scan/status?job_id=${encodeURIComponent(jobId)}`);
}

export function fetchSignals(params: {
  run_id: string;
  market?: string;
  tf?: string;
  indicator?: string;
  category?: string;
  direction?: string;
  symbol?: string;
  all_states?: boolean;
  limit?: number;
  offset?: number;
}): Promise<ScanSignalsResponse> {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== "")
        .map(([k, v]) => [k, String(v)])
    )
  ).toString();
  return getJson<ScanSignalsResponse>(`/signals?${qs}`);
}
