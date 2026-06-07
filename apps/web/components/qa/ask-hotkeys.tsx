"use client";

import { useEffect } from "react";
import { useAskPanel } from "@/lib/ask-store";

// "/" opens Ask, Escape closes. Renders nothing; just a window listener.
function isEditable(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
}

export function AskHotkeys() {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const { open, openAsk, close } = useAskPanel.getState();
      if (
        e.key === "/" &&
        !e.metaKey &&
        !e.ctrlKey &&
        !e.altKey &&
        !isEditable(e.target)
      ) {
        // Don't let "/" land as a character — it summons Ask instead.
        e.preventDefault();
        openAsk();
      } else if (e.key === "Escape" && open) {
        // Close from the Ask input itself or from anywhere non-editable, but
        // leave Escape in OTHER fields (e.g. the symbol input) alone.
        const t = e.target;
        const inAskInput = t instanceof HTMLElement && t.id === "qa-q";
        if (inAskInput || !isEditable(t)) close();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  return null;
}
