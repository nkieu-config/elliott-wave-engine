"use client";

import { create } from "zustand";

// One state driven by three entry points (header toggle, "/" hotkey,
// end-of-narration follow-up link). `focusNonce` bumps on every open request so
// QaPanel re-focuses even when already open. `grounded` is sticky.
interface AskPanelState {
  open: boolean;
  grounded: boolean;
  focusNonce: number;
  toggle: () => void;
  openAsk: (opts?: { grounded?: boolean }) => void;
  close: () => void;
  setGrounded: (grounded: boolean) => void;
}

export const useAskPanel = create<AskPanelState>((set) => ({
  open: false,
  grounded: false,
  focusNonce: 0,
  toggle: () => set((s) => ({ open: !s.open, focusNonce: s.focusNonce + 1 })),
  openAsk: (opts) =>
    set((s) => ({
      open: true,
      grounded: opts?.grounded ?? s.grounded,
      focusNonce: s.focusNonce + 1,
    })),
  close: () => set({ open: false }),
  setGrounded: (grounded) => set({ grounded }),
}));
