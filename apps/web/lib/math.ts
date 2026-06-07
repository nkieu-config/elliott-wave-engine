export const clamp = (n: number, lo: number, hi: number): number =>
  Math.min(hi, Math.max(lo, n));

export const clamp01 = (n: number): number => clamp(n, 0, 1);

export const lerp = (from: number, to: number, t: number): number => from + (to - from) * t;

// framer-motion's default curve. t in [0, 1].
export const easeOutCubic = (t: number): number => 1 - (1 - t) ** 3;

// Wraps both directions. len > 0.
export const wrapIndex = (index: number, delta: number, len: number): number =>
  (index + delta + len) % len;

// Min-gap keeps paired sliders from inverting on a fast drag.
export const orderedWindow = (lo: number, hi: number, gap = 0.01): [number, number] => [
  Math.min(lo, hi - gap),
  Math.max(hi, lo + gap),
];
