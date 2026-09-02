import { guideFor } from "@/lib/guide";

export function ChartGuide({ indicator }: { indicator: string }) {
  const g = guideFor(indicator);
  return (
    <div className="grid gap-3 rounded-lg border border-border bg-surface-1 p-4 sm:grid-cols-3">
      <div>
        <div className="mb-1 font-mono text-[10px] uppercase tracking-wide text-text-3">Ne Ölçer</div>
        <p className="text-sm leading-relaxed text-text-2">{g.whatItMeasures}</p>
      </div>
      <div>
        <div className="mb-1 font-mono text-[10px] uppercase tracking-wide text-text-3">Nereye Bak</div>
        <p className="text-sm leading-relaxed text-text-2">{g.whereToLook}</p>
      </div>
      <div className="border-l-4 border-accent pl-3 sm:border-l-0 sm:border-l-4">
        <div className="mb-1 font-mono text-[10px] uppercase tracking-wide text-accent">AL Sinyali Ne Zaman Oluşur</div>
        <p className="text-sm leading-relaxed text-text-1">{g.buySignal}</p>
      </div>
    </div>
  );
}
