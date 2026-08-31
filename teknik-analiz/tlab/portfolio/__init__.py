"""Sinyalden portföye: forecast birleştirme, volatilite hedefleme/pozisyon
boyutlama, handcrafting (ağırlıklandırma), portföy riski — Faz 10.

Bu paket `IndicatorResult`/`Signal` ÜRETMEZ (tarama/sinyal katmanı değil,
zaten üretilmiş forecast/sinyal serilerini GERÇEK pozisyon büyüklüğüne
çeviren bir hesap katmanı) — bkz. `docs/spec/tlab_10_portfolio.md` ve
kaynak `bilgi-bankasi/teknik/11_carver_systematic.md` (K3, Carver
"Systematic Trading" çıkarımı)."""

from __future__ import annotations
