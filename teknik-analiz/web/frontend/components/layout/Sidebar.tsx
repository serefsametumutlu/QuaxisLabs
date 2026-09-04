"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brand } from "./Brand";
import { THEMES, THEME_KEYS } from "@/lib/themes";
import { fetchCategories } from "@/lib/api";
import type { CategoryEntry } from "@/lib/types";

const NAV = [
  { href: "/scan", label: "Tarama" },
  { href: "/chart", label: "Grafik" },
  { href: "/share", label: "Paylaşım Metni" },
];

interface Props {
  theme: string;
  onThemeChange: (t: string) => void;
}

/** Sayfalar arası (Tarama/Grafik) ortak sol menü — kullanıcının "sidebar
 * eksik" geri bildirimine yanıt. Tema seçimi burada YAŞAR (her iki sayfa
 * da `useTheme()` ile aynı `localStorage` anahtarını paylaşır).
 *
 * 2026-09-02: "Stratejiler" bölümü eklendi — kullanıcı "sol bar da tarama ve
 * grafik yazan yerde stratejiler kısmı olsun ... gruplandıralım stratejileri
 * mesela harmonik, arbitraj, momentum, trend vs. gibi alanlarına göre"
 * dedi. Kategori listesi `/api/categories`'ten (gerçek CATALOG kayıtlarından
 * türetilir, elle bakımlı ikinci bir liste DEĞİL) gelir; her satır
 * `/scan?category=<kategori>`'ye gider — tarama sayfası bunu okuyup SADECE
 * o kategorinin sinyallerini listeler (bkz. app/scan/page.tsx). Kullanıcı
 * kendisi de bu gruplamanın kesin olmadığını belirtti ("ben örnek verdim
 * böyle olmak zorunda değil") — bu yüzden liste sabit KODLANMADI, katalog
 * hangi kategorileri taşıyorsa o gösterilir; ileride yeni bir kategori
 * eklenirse (bootstrap.py::CATALOG) burada otomatik belirir. */
export function Sidebar({ theme, onThemeChange }: Props) {
  const pathname = usePathname();
  const [categories, setCategories] = useState<CategoryEntry[]>([]);

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setCategories([]));
  }, []);

  return (
    <aside className="flex w-56 shrink-0 flex-col gap-6 overflow-y-auto border-r border-border bg-surface-1 px-4 py-5">
      <Brand />
      <nav className="flex flex-col gap-1">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active ? "bg-accent/15 text-accent" : "text-text-2 hover:bg-surface-2 hover:text-text-1"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      {categories.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="px-3 text-[11px] font-semibold uppercase tracking-wide text-text-3">
            Stratejiler
          </span>
          {categories.map((c) => (
            <Link
              key={c.category}
              href={`/scan?category=${encodeURIComponent(c.category)}`}
              className="rounded-md px-3 py-1.5 text-sm text-text-2 transition-colors hover:bg-surface-2 hover:text-text-1"
            >
              {c.category_label}
            </Link>
          ))}
        </div>
      )}

      <label className="mt-auto flex flex-col gap-1 text-xs text-text-3">
        Tasarım
        <select
          value={theme}
          onChange={(e) => onThemeChange(e.target.value)}
          className="rounded-md border border-border bg-surface-2 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
        >
          {THEME_KEYS.map((k) => (
            <option key={k} value={k}>
              {THEMES[k].name}
            </option>
          ))}
        </select>
      </label>
    </aside>
  );
}
