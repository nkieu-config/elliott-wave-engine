import type { Mode } from "@/lib/hooks/use-narration-stream";

export interface ModeMeta {
  key: Mode;
  num: string;
  tab: string;
  title: string;
  subtitle: string;
  accent: string;
}

export const MODES: ModeMeta[] = [
  {
    key: "explanation",
    num: "1",
    tab: "Structure",
    title: "What am I looking at?",
    subtitle: "The structure.",
    accent: "var(--color-cyan)",
  },
  {
    key: "outlook",
    num: "2",
    tab: "Outlook",
    title: "Where could it go?",
    subtitle: "Targets and conditions.",
    // Brighter mint so the active lens doesn't blend into the app's emerald
    // chrome (focus rings, send, brand mark). Keeps green = upside.
    accent: "var(--color-accent-bright)",
  },
  {
    key: "risk",
    num: "3",
    tab: "Risk",
    title: "What's the risk?",
    subtitle: "The weakest link.",
    // Caution (amber), not error (red) — keeps --color-down meaning "invalidated".
    accent: "var(--color-warn)",
  },
  {
    key: "differentiator",
    num: "4",
    tab: "Alternative",
    title: "What if I'm wrong?",
    subtitle: "Runner-up scenarios.",
    accent: "var(--color-violet)",
  },
];
