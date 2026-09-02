import Image from "next/image";
import Link from "next/link";

/** `tlab/assets/quaxislabs_logo.png`'den (Streamlit dashboard'un ZATEN
 * kullandığı marka) küçültülmüş `public/logo.png` — küçük boyutta (28px)
 * kendi koyu rozet zemini rahatsız etmiyor, herhangi bir tema arka planında
 * "yabancı" durmuyor (Discord/Slack rozet-logo deseniyle aynı mantık). */
export function Brand({ size = 28 }: { size?: number }) {
  return (
    <Link href="/chart" className="flex items-center gap-2 shrink-0">
      <Image src="/logo.png" alt="QuaxisLabs" width={size} height={size} className="rounded-full" priority />
      <span className="font-mono text-sm font-semibold tracking-wide text-text-1">QuaxisLabs</span>
    </Link>
  );
}
