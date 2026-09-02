"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brand } from "./Brand";
import { THEMES, THEME_KEYS } from "@/lib/themes";

const NAV = [
  { href: "/scan", label: "Tarama" },
  { href: "/chart", label: "Grafik" },
];

interface Props {
  theme: string;
  onThemeChange: (t: string) => void;
}

/** Sayfalar arası (Tarama/Grafik) ortak sol menü — kullanıcının "sidebar
 * eksik" geri bildirimine yanıt. Tema seçimi burada YAŞAR (her iki sayfa
 * da `useTheme()` ile aynı `localStorage` anahtarını paylaşır). */
export function Sidebar({ theme, onThemeChange }: Props) {
  const pathname = usePathname();
  return (
    <aside className="flex w-56 shrink-0 flex-col gap-6 border-r border-border bg-surface-1 px-4 py-5">
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
