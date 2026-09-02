import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Ev dizini kökünde (C:\Users\Samet) ilgisiz bir package-lock.json var
  // (bilanco-radar'ın 4GB'lık .git deposuyla aynı üst klasör) — Turbopack
  // bunu yanlışlıkla proje kökü sanmasın diye açıkça sabitleniyor.
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
