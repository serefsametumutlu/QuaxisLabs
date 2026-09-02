import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ variable: "--font-body", subsets: ["latin"] });
const jetbrainsMono = JetBrains_Mono({ variable: "--font-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "tlab",
  description: "Teknik Lab — non-repainting çoklu zaman dilimi indikatör tarama laboratuvarı",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="tr" data-theme="dark" className={`${inter.variable} ${jetbrainsMono.variable} h-full`}>
      <head>
        {/* `lib/themes.ts`'in "classic"/"editorial" temalarının kullandığı,
            next/font'a dahil edilmemiş ek yazı tipleri (Inter/JetBrains Mono
            zaten next/font ile yükleniyor). */}
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap"
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
