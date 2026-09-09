"""Stratejiye ÖZEL grafik besteleyicileri.

Mimari kararın kalbi burası. Eski `tlab/viz/renderer.py` TEK bir jenerik
yol üzerinden 24 göstergeyi çiziyordu: her gösterge `Line`/`Box`/`Marker`
torbası üretiyor, renderer hepsini aynı biçimde basıyordu. Kullanıcının
"karma karışık", "bizim sistemi ben bile anlamıyorum" şikâyeti bunun
doğrudan sonucuydu — referans görsellerin hiçbiri jenerik bir çizici
çıktısı değil, HER BİRİ o stratejiye özel bestelenmiş.

Sözleşme: bir besteleyici, göstergenin TİPLİ sonucunu alır (jenerik
primitif torbası değil) ve `go.Figure` döndürür. Tip zorunluluğu, eksik
bir alanın sessizce boş/gri çizilmesini imkânsız kılar.
"""
