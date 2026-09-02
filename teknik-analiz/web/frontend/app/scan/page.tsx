"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  fetchCatalog,
  fetchCategories,
  fetchRuns,
  fetchScanStatus,
  fetchSignals,
  startScan,
} from "@/lib/api";
import type { ScanJob, ScanRun, ScanSignal } from "@/lib/api";
import type { CatalogEntry, CategoryEntry } from "@/lib/types";
import { Sidebar } from "@/components/layout/Sidebar";
import { useTheme } from "@/lib/useTheme";

const MARKETS = ["bist", "nasdaq"];
const PAGE_SIZE = 50;

const STATE_COLOR: Record<string, string> = {
  confirmed: "text-accent",
  completed: "text-accent",
  active: "text-warning",
  pending: "text-text-3",
  invalidated: "text-danger",
  expired: "text-text-3",
};

/** 2026-09-03: kullanıcı "tamamlandı sinyali veren hisseler AL sinyali geldi
 * olarak gösterilsin, aktif/beklemede olanlar BEKLENİYOR olarak gösterilsin"
 * dedi -- çıplak `state` sözcükleri (confirmed/active/pending...) yerine bu
 * okunabilir Türkçe metni kullanıyoruz. Yön burada da hesaba katılıyor
 * ("AL sinyali geldi" / "SAT sinyali geldi") çünkü TAMAMLANDI/onaylanmış bir
 * sinyalin AL mı SAT mı olduğu asıl önemli bilgi. */
function statusLabel(state: string, direction: string): string {
  if (state === "confirmed" || state === "completed") {
    if (direction === "long") return "AL sinyali geldi";
    if (direction === "short") return "SAT sinyali geldi";
    return "Sinyal geldi";
  }
  if (state === "active" || state === "pending") return "BEKLENİYOR";
  if (state === "invalidated") return "Geçersiz";
  if (state === "expired") return "Süresi doldu";
  return state.toUpperCase();
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("tr-TR", { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

/** Mevcut taramaları (`outputs/results.db`) listeler VE "Yeni Tarama Başlat"
 * ile `web/backend/routes/scan_trigger.py`'nin arka planda (thread içinde)
 * çalıştırdığı `run_eod()`'u tetikleyip durumunu (`queued/running/completed/
 * failed`) periyodik sorgulayarak (polling) izler — tam evrende dakikalarca
 * sürebileceği için sayfa bu süre boyunca bloklanmaz, bittiğinde tarama
 * listesi otomatik yenilenir.
 *
 * 2026-09-02: kullanıcının "hem tüm tarama olsun hem de harmonikleri kendi
 * arasında, arbitrajı kendi arasında ayrı ayrı tarayabilsem ... LONG SHORT
 * filtreleyebilmem gerek" isteğine yanıt — Kategori (Sidebar'daki
 * "Stratejiler"le AYNI kaynak) ve Yön (AL/SAT) filtreleri eklendi; Sidebar'dan
 * `?category=` ile gelindiğinde bu sayfa onu okuyup baştan uygular. "Yeni
 * Tarama Başlat" da seçili kategoriye göre YALNIZCA o kategorinin
 * göstergelerini yeniden koşabiliyor (bkz. `web/backend/routes/
 * scan_trigger.py` — bu UPSERT olduğu için diğer göstergelerin sonuçlarını
 * SİLMİYOR). */
function ScanPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [theme, setTheme] = useTheme();
  const [market, setMarket] = useState("bist");
  const [runs, setRuns] = useState<ScanRun[]>([]);
  const [runId, setRunId] = useState<string>("");
  const [tf, setTf] = useState("");
  const [category, setCategory] = useState(() => searchParams.get("category") ?? "");
  const [indicator, setIndicator] = useState(() => searchParams.get("indicator") ?? "");
  const [direction, setDirection] = useState("");
  const [symbol, setSymbol] = useState("");
  const [allStates, setAllStates] = useState(false);
  const [offset, setOffset] = useState(0);
  const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
  const [categories, setCategories] = useState<CategoryEntry[]>([]);
  const [signals, setSignals] = useState<ScanSignal[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanJob, setScanJob] = useState<ScanJob | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);

  useEffect(() => {
    fetchCatalog().then(setCatalog).catch(() => setCatalog([]));
    fetchCategories().then(setCategories).catch(() => setCategories([]));
  }, []);

  const loadRuns = useCallback((selectLatest: boolean) => {
    fetchRuns(market)
      .then((rs) => {
        setRuns(rs);
        if (selectLatest) {
          setRunId(rs[0]?.run_id ?? "");
          setOffset(0);
        }
      })
      .catch(() => setRuns([]));
  }, [market]);

  useEffect(() => {
    loadRuns(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [market]);

  // Aktif bir tarama işi varsa (queued/running) her 5sn'de bir durumunu
  // sorgular; bitince (completed/failed) tarama listesini yeniler.
  useEffect(() => {
    if (!scanJob || scanJob.status === "completed" || scanJob.status === "failed") return;
    const interval = setInterval(() => {
      fetchScanStatus(scanJob.job_id)
        .then((job) => {
          setScanJob(job);
          if (job.status === "completed") loadRuns(true);
        })
        .catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [scanJob, loadRuns]);

  const triggerScan = () => {
    setScanError(null);
    startScan(market, false, category || undefined)
      .then(setScanJob)
      .catch((e: Error) => setScanError(e.message));
  };

  const load = useCallback(() => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    fetchSignals({
      run_id: runId,
      tf: tf || undefined,
      indicator: indicator || undefined,
      category: indicator ? undefined : category || undefined,
      direction: direction || undefined,
      symbol: symbol || undefined,
      all_states: allStates,
      limit: PAGE_SIZE,
      offset,
    })
      .then((res) => {
        setSignals(res.signals);
        setTotal(res.total);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [runId, tf, indicator, category, direction, symbol, allStates, offset]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const openChart = (s: ScanSignal) => {
    const qs = new URLSearchParams({
      symbol: s.symbol,
      tf: s.timeframe.toLowerCase(),
      indicator: s.indicator,
      market,
    });
    router.push(`/chart?${qs.toString()}`);
  };

  const selectedRun = runs.find((r) => r.run_id === runId);
  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const indicatorsInCategory = category ? catalog.filter((c) => c.category === category) : catalog;
  const selectedCategoryLabel = categories.find((c) => c.category === category)?.category_label;

  return (
    <div className="flex min-h-screen bg-bg text-text-1">
      <Sidebar theme={theme} onThemeChange={setTheme} />
      <div className="flex-1">
        <header className="flex flex-wrap items-end gap-4 border-b border-border px-6 py-4">
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Piyasa
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              className="rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              {MARKETS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Tarama
            <select
              value={runId}
              onChange={(e) => {
                setRunId(e.target.value);
                setOffset(0);
              }}
              className="min-w-48 rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} ({r.universe_size} sembol)
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Zaman Dilimi
            <select
              value={tf}
              onChange={(e) => {
                setTf(e.target.value);
                setOffset(0);
              }}
              className="rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              <option value="">Tümü</option>
              {(selectedRun?.timeframes ?? []).map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Strateji Kategorisi
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setIndicator("");
                setOffset(0);
              }}
              className="min-w-40 rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              <option value="">Tümü</option>
              {categories.map((c) => (
                <option key={c.category} value={c.category}>
                  {c.category_label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Gösterge
            <select
              value={indicator}
              onChange={(e) => {
                setIndicator(e.target.value);
                setOffset(0);
              }}
              className="min-w-48 rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              <option value="">Tümü</option>
              {indicatorsInCategory.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.display_name}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Yön
            <select
              value={direction}
              onChange={(e) => {
                setDirection(e.target.value);
                setOffset(0);
              }}
              className="rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              <option value="">Tümü</option>
              <option value="long">AL</option>
              <option value="short">SAT</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Sembol
            <input
              value={symbol}
              onChange={(e) => {
                setSymbol(e.target.value.toUpperCase());
                setOffset(0);
              }}
              placeholder="ör. AKBNK"
              className="w-32 rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            />
          </label>
          <label className="flex items-center gap-2 pb-1.5 text-xs text-text-3">
            <input
              type="checkbox"
              checked={allStates}
              onChange={(e) => {
                setAllStates(e.target.checked);
                setOffset(0);
              }}
            />
            Tüm durumları göster
          </label>
          <div className="ml-auto flex items-center gap-3">
            {scanJob && (scanJob.status === "queued" || scanJob.status === "running") && (
              <span className="font-mono text-xs text-warning">
                Tarama çalışıyor… (birkaç dakika sürebilir)
              </span>
            )}
            {scanJob?.status === "completed" && (
              <span className="font-mono text-xs text-accent">
                Tarama tamamlandı — {scanJob.result?.run_id}
              </span>
            )}
            {scanJob?.status === "failed" && (
              <span className="font-mono text-xs text-danger">Tarama başarısız: {scanJob.error}</span>
            )}
            {scanJob?.status === "already_running" && (
              <span className="font-mono text-xs text-warning">Bu piyasa için zaten bir tarama çalışıyor</span>
            )}
            <button
              onClick={triggerScan}
              disabled={scanJob?.status === "queued" || scanJob?.status === "running"}
              className="rounded-md bg-accent px-3.5 py-1.5 text-sm font-medium text-bg hover:opacity-90 disabled:opacity-50"
            >
              {category ? `${selectedCategoryLabel ?? category} Taraması Başlat` : "Yeni Tarama Başlat"}
            </button>
          </div>
        </header>

        <main className="flex flex-col gap-4 px-6 py-5">
          {scanError && (
            <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
              {scanError}
            </div>
          )}
          {selectedRun && (
            <div className="flex flex-wrap gap-4 text-xs text-text-3">
              <span>
                Durum: <span className="text-text-1">{selectedRun.status}</span>
              </span>
              <span>
                Bitiş: <span className="text-text-1">{formatDate(selectedRun.finished_at ?? selectedRun.started_at)}</span>
              </span>
              <span>
                Toplam eşleşme: <span className="text-text-1">{total.toLocaleString("tr-TR")}</span>
              </span>
            </div>
          )}
          {error && (
            <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
              {error}
            </div>
          )}
          {runs.length === 0 && !error && (
            <div className="rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-text-2">
              Bu piyasa için henüz bir tarama sonucu yok. Terminalden{" "}
              <code className="font-mono text-text-1">tlab eod --market {market}</code> çalıştırıp
              buraya geri dönebilirsin.
            </div>
          )}

          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-surface-1 text-xs text-text-3">
                <tr>
                  <th className="px-3 py-2 font-medium">Sembol</th>
                  <th className="px-3 py-2 font-medium">TF</th>
                  <th className="px-3 py-2 font-medium">Gösterge</th>
                  <th className="px-3 py-2 font-medium">Durum</th>
                  <th className="px-3 py-2 font-medium">Yön</th>
                  <th className="px-3 py-2 font-medium">Skor</th>
                  <th className="px-3 py-2 font-medium">Tespit</th>
                </tr>
              </thead>
              <tbody>
                {signals.map((s, i) => (
                  <tr
                    key={`${s.symbol}-${s.timeframe}-${s.indicator}-${s.pattern_id}-${i}`}
                    onClick={() => openChart(s)}
                    className="cursor-pointer border-t border-border hover:bg-surface-2"
                  >
                    <td className="px-3 py-2 font-medium">{s.symbol}</td>
                    <td className="px-3 py-2 font-mono text-xs text-text-2">{s.timeframe}</td>
                    <td className="px-3 py-2 text-xs text-text-2">{s.display_name}</td>
                    <td className={`px-3 py-2 font-medium ${STATE_COLOR[s.state] ?? "text-text-2"}`}>
                      {statusLabel(s.state, s.direction)}
                    </td>
                    <td className="px-3 py-2">
                      {s.direction === "long" ? (
                        <span className="text-up">AL</span>
                      ) : s.direction === "short" ? (
                        <span className="text-down">SAT</span>
                      ) : (
                        <span className="text-text-3">{s.direction}</span>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{s.score.toFixed(2)}</td>
                    <td className="px-3 py-2 text-xs text-text-3">{formatDate(s.detected_at)}</td>
                  </tr>
                ))}
                {!loading && signals.length === 0 && runs.length > 0 && (
                  <tr>
                    <td colSpan={7} className="px-3 py-6 text-center text-sm text-text-3">
                      Bu filtrelerle eşleşen sinyal yok.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {loading && <div className="font-mono text-sm text-text-3">Yükleniyor…</div>}

          {total > PAGE_SIZE && (
            <div className="flex items-center gap-3 text-sm text-text-2">
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                className="rounded-md border border-border px-3 py-1 disabled:opacity-40"
              >
                Önceki
              </button>
              <span className="font-mono text-xs">
                Sayfa {page} / {pageCount}
              </span>
              <button
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className="rounded-md border border-border px-3 py-1 disabled:opacity-40"
              >
                Sonraki
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

/** Sidebar'daki "Stratejiler" linkleri AYNI /scan rotasına farklı bir
 * `?category=` ile Next `<Link>` üzerinden gelir — App Router aynı route'a
 * client-side geçişte component'i YENİDEN MOUNT ETMEZ, bu yüzden
 * `ScanPageInner`'ın mount-anı `useState(() => searchParams.get(...))`
 * lazy initializer'ı ikinci bir Stratejiler tıklamasında GÜNCELLENMEZ
 * (gerçek bulgu: tarayıcıda doğrulandı — URL değişti ama filtre
 * uygulanmadı). Çözüm, `AiReportPanel`/`ChartImage`'ta zaten kullanılan
 * AYNI "key değişince yeniden mount et" deseni — `searchParams.toString()`
 * her Stratejiler tıklamasında değişir, `key` değişince React tüm state'i
 * SIFIRLAYIP yeniden başlatır (effect-içi setState'e gerek KALMAZ). */
function ScanPageKeyed() {
  const searchParams = useSearchParams();
  return <ScanPageInner key={searchParams.toString()} />;
}

export default function ScanPage() {
  return (
    <Suspense fallback={null}>
      <ScanPageKeyed />
    </Suspense>
  );
}
