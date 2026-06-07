"use client";

import { useEffect, useRef, useState } from "react";
import { useMediaQuery } from "@/lib/hooks/use-media-query";
import { clamp01, easeOutCubic, lerp } from "@/lib/math";

// Hand-rolled rAF loop, not framer-motion — avoids ~60KB gzipped for a 20-line
// ease-out curve.
export function AnimatedNumber({
  value,
  format,
  duration = 0.4,
}: {
  value: number;
  format: (n: number) => string;
  duration?: number;
}) {
  const [display, setDisplay] = useState(value);
  // Per-frame value so an interrupted tween resumes from where the number
  // actually is; else rapid changes (slider drag) snap backwards.
  const displayRef = useRef(value);
  // CSS prefers-reduced-motion can't reach a JS rAF tween — snap here.
  const reduce = useMediaQuery("(prefers-reduced-motion: reduce)");

  useEffect(() => {
    const from = displayRef.current;
    const to = value;
    if (from === to) return;
    if (reduce) {
      displayRef.current = to;
      setDisplay(to);
      return;
    }
    const durationMs = duration * 1000;
    const start = performance.now();
    let frame = 0;

    const tick = (now: number) => {
      const t = clamp01((now - start) / durationMs);
      const current = lerp(from, to, easeOutCubic(t));
      displayRef.current = current;
      setDisplay(current);
      if (t < 1) {
        frame = requestAnimationFrame(tick);
      } else {
        displayRef.current = to;
      }
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration, reduce]);

  // tabular figures so the tween never reflows the digit column frame-to-frame.
  return <span style={{ fontVariantNumeric: "tabular-nums" }}>{format(display)}</span>;
}
