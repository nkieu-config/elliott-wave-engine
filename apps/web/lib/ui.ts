import type { CSSProperties } from "react";

export const TOAST_DURATION = 1500;

// Accurate type for inline styles setting `--foo` vars (vs. `as CSSProperties`).
export type CSSVars = CSSProperties & Record<`--${string}`, string | number>;
