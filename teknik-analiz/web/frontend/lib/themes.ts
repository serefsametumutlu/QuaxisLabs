// "Grafik Stil Vitrini" artifact'ından (claude.ai/code/artifact/18f4bb4c-...)
// birebir taşınan 3 tema — kullanıcı bu 3'ünü ("Klasik Beyaz Rapor",
// "Terminal Koyu", "Kağıt Rapor") özellikle istedi. Renk değerleri o
// artifact'ın kendi `THEMES` sözlüğünden AYNEN alındı (bkz. görev notları).

export interface ThemeDef {
  key: "classic" | "dark" | "editorial";
  name: string;
  pageBg: string;
  cardBg: string;
  cardBorder: string;
  text: string;
  textMuted: string;
  textFaint: string;
  grid: string;
  axis: string;
  up: string;
  down: string;
  accent: string;
  accent2: string;
  fontDisplay: string;
  fontBody: string;
  mono: string;
}

export const THEMES: Record<string, ThemeDef> = {
  classic: {
    key: "classic",
    name: "Klasik Beyaz Rapor",
    pageBg: "#eef0f3",
    cardBg: "#ffffff",
    cardBorder: "#e3e6ea",
    text: "#161a20",
    textMuted: "#838b98",
    textFaint: "#aeb4bf",
    grid: "#eef1f4",
    axis: "#c7cdd6",
    up: "#1f9d5c",
    down: "#cf4a3e",
    accent: "#b8892f",
    accent2: "#35618c",
    fontDisplay: "'Source Serif 4', Georgia, serif",
    fontBody: "'Inter', -apple-system, 'Segoe UI', sans-serif",
    mono: "'IBM Plex Mono', ui-monospace, monospace",
  },
  dark: {
    key: "dark",
    name: "Terminal Koyu",
    pageBg: "#090b0f",
    cardBg: "#0d1015",
    cardBorder: "#1b2028",
    text: "#e7eaf0",
    textMuted: "#6d7480",
    textFaint: "#454b56",
    grid: "#161a21",
    axis: "#232935",
    up: "#22d67f",
    down: "#ff5c5c",
    accent: "#f5b400",
    accent2: "#35b8ff",
    fontDisplay: "'JetBrains Mono', ui-monospace, monospace",
    fontBody: "'Inter', -apple-system, sans-serif",
    mono: "'JetBrains Mono', ui-monospace, monospace",
  },
  editorial: {
    key: "editorial",
    name: "Kağıt Rapor",
    pageBg: "#efe7d4",
    cardBg: "#faf6ec",
    cardBorder: "#e1d5b7",
    text: "#2c2418",
    textMuted: "#8c7d5f",
    textFaint: "#c3b696",
    grid: "#eadfc4",
    axis: "#d8c9a3",
    up: "#3c6b4c",
    down: "#a3402c",
    accent: "#b8802a",
    accent2: "#4d5c73",
    fontDisplay: "'Playfair Display', Georgia, serif",
    fontBody: "'Source Serif 4', Georgia, serif",
    mono: "'IBM Plex Mono', ui-monospace, monospace",
  },
};

export const THEME_KEYS = Object.keys(THEMES) as (keyof typeof THEMES)[];

/** `lib/api.ts`ye paralel — sayfanın CSS custom property'lerini (globals.css
 * `:root` tanımları) seçilen temanın değerleriyle DOĞRUDAN üzerine yazar.
 * Tek kaynak burası (`THEMES`) — CSS'te tema-başına ayrı blok YOK. */
export function applyTheme(key: string) {
  const t = THEMES[key] ?? THEMES.dark;
  const root = document.documentElement.style;
  root.setProperty("--clr-bg", t.pageBg);
  root.setProperty("--clr-surface-1", t.cardBg);
  root.setProperty("--clr-surface-2", t.cardBg);
  root.setProperty("--clr-border", t.cardBorder);
  root.setProperty("--clr-accent", t.accent);
  root.setProperty("--clr-danger", t.down);
  root.setProperty("--clr-warning", t.accent);
  root.setProperty("--clr-info", t.accent2);
  root.setProperty("--clr-text-1", t.text);
  root.setProperty("--clr-text-2", t.textMuted);
  root.setProperty("--clr-text-3", t.textFaint);
  root.setProperty("--font-body", t.fontBody);
  root.setProperty("--font-mono", t.mono);
  root.setProperty("--clr-up", t.up);
  root.setProperty("--clr-down", t.down);
  root.setProperty("--clr-grid", t.grid);
  root.setProperty("--clr-axis", t.axis);
  document.documentElement.setAttribute("data-theme", key);
}
