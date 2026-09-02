"use client";

import { useEffect, useState } from "react";
import { fetchGuide, type GuideEntry } from "@/lib/api";

const FALLBACK: GuideEntry = {
  watch: "Grafikteki çizgi/kutu/işaretlere ve renk koduna (yeşil=boğa, kırmızı=ayı) bakın.",
  measures: "Bu gösterge, fiyat verisinden türetilmiş bir teknik analiz sinyali üretir.",
  values: "Değerler, sinyalin gücünü/geçerliliğini belirtir.",
  signal: "Sinyal metnindeki durum etiketine (ör. 'ONAY'/'TAMAMLANDI') bakın.",
};

/** `tlab/viz/labels_tr.py::signal_reading()`den (Streamlit dashboard'un ZATEN
 * kullandığı, indikatöre özel — kategori-geneli DEĞİL — rehber) gelir. */
export function ChartGuide({ indicator }: { indicator: string }) {
  const [guide, setGuide] = useState<GuideEntry | null>(null);

  useEffect(() => {
    fetchGuide(indicator)
      .then(setGuide)
      .catch(() => setGuide(null));
  }, [indicator]);

  const g = guide ?? FALLBACK;

  return (
    <div className="grid gap-3 rounded-lg border border-border bg-surface-1 p-4 sm:grid-cols-2 lg:grid-cols-4">
      <div>
        <div className="mb-1 font-mono text-[10px] uppercase tracking-wide text-text-3">Nereye Bak</div>
        <p className="text-sm leading-relaxed text-text-2">{g.watch}</p>
      </div>
      <div>
        <div className="mb-1 font-mono text-[10px] uppercase tracking-wide text-text-3">Ne Ölçer</div>
        <p className="text-sm leading-relaxed text-text-2">{g.measures}</p>
      </div>
      <div>
        <div className="mb-1 font-mono text-[10px] uppercase tracking-wide text-text-3">Değerler Ne Demek</div>
        <p className="text-sm leading-relaxed text-text-2">{g.values}</p>
      </div>
      <div className="border-l-4 border-accent pl-3">
        <div className="mb-1 font-mono text-[10px] uppercase tracking-wide text-accent">AL Sinyali Ne Zaman Oluşur</div>
        <p className="text-sm leading-relaxed text-text-1">{g.signal}</p>
      </div>
    </div>
  );
}
