import type { CatalogEntry, ChartResponse } from "./types";

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

export function fetchChart(params: {
  symbol: string;
  tf: string;
  indicator: string;
  market: string;
}): Promise<ChartResponse> {
  const qs = new URLSearchParams(params).toString();
  return getJson<ChartResponse>(`/chart?${qs}`);
}
