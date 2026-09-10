#!/usr/bin/env python3
"""GERÇEK veriyle grafik üret ve PNG'ye kaydet — `tlab/chart` yolundan.

Bu betik `/api/chart.json` rotasının AYNI kod yolunu kullanır
(`compute_live` -> adaptör -> komposer), yalnızca çıktıyı tarayıcı
yerine dosyaya yazar. Sunucu çalıştırmadan, tek komutla gerçek bir
sinyalin grafiğini görmek için.

Kullanım:
    python scripts/grafik_cek.py THYAO patterns.triangle
    python scripts/grafik_cek.py THYAO patterns.triangle --tf 4h --tema classic
    python scripts/grafik_cek.py THYAO harmonic.carney --bayat 200

Notlar:
  * Veri yerel önbellekten okunur; yoksa önce `tlab eod` ya da
    `Store.update()` gerekir.
  * `--bayat` tazelik kapısı (varsayılan 60 bar). Eski bir formasyonu
    görmek için büyüt, kapatmak için 0 ver.
  * Desteklenen göstergeler: `chart_json._SUPPORTED` (bağlı olmayanlar
    net bir hata mesajı verir).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException  # noqa: E402

import web.backend.routes.chart_json as cj  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sembol")
    ap.add_argument("gosterge")
    ap.add_argument("--tf", default="1d", choices=["1h", "4h", "1d", "w1"])
    ap.add_argument("--market", default="bist")
    ap.add_argument("--tema", default="dark", choices=["dark", "classic", "editorial"])
    ap.add_argument("--bayat", type=int, default=60,
                    help="tazelik kapısı, bar (0 = kapalı)")
    ap.add_argument("--cikti", default=None, help="PNG yolu")
    ap.add_argument("--genislik", type=int, default=1600)
    ap.add_argument("--yukseklik", type=int, default=900)
    a = ap.parse_args()

    if a.gosterge not in cj._SUPPORTED:
        bagli = "\n  ".join(sorted(cj._SUPPORTED))
        print(f"'{a.gosterge}' henüz tlab/chart'a bağlı değil.\nBağlı olanlar:\n  {bagli}")
        return 2

    try:
        resp = cj.get_chart_json(
            symbol=a.sembol, tf=a.tf, indicator=a.gosterge, market=a.market,
            theme=a.tema, max_bars_ago=(a.bayat or None),
        )
    except HTTPException as e:
        print(f"HTTP {e.status_code}: {e.detail}")
        return 1

    fig = go.Figure(json.loads(resp.body))
    fig.update_layout(width=a.genislik, height=a.yukseklik)
    out = Path(a.cikti or f"outputs/samples/{a.sembol}_{a.gosterge}_{a.tf}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    # PNG kaleido ister; yoksa HTML'e düş (tarayıcıda açılır, hover çalışır).
    try:
        fig.write_image(str(out), scale=2)
    except Exception as exc:                                  # noqa: BLE001
        out = out.with_suffix(".html")
        fig.write_html(str(out), include_plotlyjs="cdn")
        print(f"(kaleido yok: {type(exc).__name__}) HTML olarak yazıldı")
    print(f"yazıldı: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
