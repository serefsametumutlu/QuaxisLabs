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
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
