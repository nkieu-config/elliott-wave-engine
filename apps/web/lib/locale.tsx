"use client";

import { createContext, useContext } from "react";
import { FALLBACK_LOCALE } from "@/lib/resolve-locale";

// Seeded from the server-resolved locale (layout.tsx) so useLocale() matches on
// server and client — formatting stays hydration-stable.
const LocaleContext = createContext<string>(FALLBACK_LOCALE);

export function LocaleProvider({
  locale,
  children,
}: {
  locale: string;
  children: React.ReactNode;
}) {
  return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>;
}

export function useLocale(): string {
  return useContext(LocaleContext);
}
