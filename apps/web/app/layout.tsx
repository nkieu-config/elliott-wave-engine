import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";
import { resolveLocale } from "@/lib/resolve-locale";
import { Providers } from "./providers";

// `-next` suffix avoids colliding with Tailwind's --font-sans/--font-mono: the
// same name made :root self-referential and dropped Inter to a system font.
const sans = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans-next",
  display: "swap",
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-mono-next",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://ewl.local"),
  title: {
    default: "Elliott Wave Lab — structure detection",
    template: "%s · Elliott Wave Lab",
  },
  description:
    "Detect Elliott wave structures on log-scale price data. Inspect candidate scenarios, score their quality, and stream analyst narration.",
  applicationName: "Elliott Wave Lab",
  authors: [{ name: "Natthachak" }],
  keywords: ["Elliott Wave", "technical analysis", "trading", "price action", "wave count"],
  openGraph: {
    title: "Elliott Wave Lab",
    description:
      "Detect Elliott wave structures, inspect candidate scenarios, and stream analyst narration.",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "Elliott Wave Lab",
    description: "Detect Elliott wave structures on log-scale price data.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#070a12",
  width: "device-width",
  initialScale: 1,
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Resolve locale server-side so server/client formatting matches (no drift).
  const locale = resolveLocale((await headers()).get("accept-language"));
  return (
    <html lang={locale} className={`${sans.variable} ${mono.variable}`}>
      <body className="min-h-dvh">
        <Providers locale={locale}>{children}</Providers>
      </body>
    </html>
  );
}
