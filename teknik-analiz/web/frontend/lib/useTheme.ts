"use client";

import { useEffect, useState } from "react";
import { applyTheme } from "./themes";

const STORAGE_KEY = "quaxislabs-theme";

function readStored(): string {
  if (typeof window === "undefined") return "dark";
  try {
    return localStorage.getItem(STORAGE_KEY) ?? "dark";
  } catch {
    return "dark";
  }
}

/** Tema seçimini sayfalar arası (client-side navigasyonda) korur —
 * `localStorage`'a yazar, her sayfa mount olduğunda oradan okur. Başlangıç
 * değeri `useState`'in tembel initializer'ında (senkron `localStorage.
 * getItem`) okunur — bir effect içinde `setState` ÇAĞIRMAK YERİNE; effect
 * yalnızca "DOM'a (CSS custom property) uygula" YAN ETKİSİ için kullanılır. */
export function useTheme(): [string, (t: string) => void] {
  const [theme, setThemeState] = useState<string>(readStored);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = (t: string) => {
    setThemeState(t);
    try {
      localStorage.setItem(STORAGE_KEY, t);
    } catch {
      // localStorage kapalı/erişilemez olabilir (gizli sekme vb.) — sessizce yut.
    }
  };

  return [theme, setTheme];
}
