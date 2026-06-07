"use client";

import * as RadixSlider from "@radix-ui/react-slider";
import * as React from "react";
import { cn } from "@/lib/cn";

interface SliderProps extends React.ComponentPropsWithRef<typeof RadixSlider.Root> {
  /** Label for each thumb (used as aria-label when there's more than one). */
  thumbAriaLabels?: string[];
}

export function Slider({
  className,
  value,
  defaultValue,
  thumbAriaLabels,
  ref,
  ...props
}: SliderProps) {
  // Fall the thumb back to the Root's aria-label so a single thumb isn't unnamed.
  const rootLabel = props["aria-label"];
  // One thumb per value — mirror the controlled/default array count.
  const values =
    (Array.isArray(value) ? value : Array.isArray(defaultValue) ? defaultValue : [0]);
  return (
    <RadixSlider.Root
      ref={ref}
      value={value}
      defaultValue={defaultValue}
      className={cn(
        "relative flex w-full touch-none select-none items-center group/slider",
        className,
      )}
      {...props}
    >
      <RadixSlider.Track className="relative h-[5px] w-full grow overflow-hidden rounded-full bg-border">
        <RadixSlider.Range
          className="absolute h-full rounded-full"
          style={{
            background:
              "linear-gradient(90deg, var(--color-accent) 0%, var(--color-cyan) 100%)",
          }}
        />
      </RadixSlider.Track>
      {values.map((_, i) => (
        <RadixSlider.Thumb
          key={i}
          className="block h-4 w-4 rounded-full bg-text shadow-[0_0_0_2px_var(--color-accent),0_0_0_6px_var(--color-accent-soft)] transition-shadow hover:shadow-[0_0_0_2px_var(--color-accent-bright),0_0_0_8px_var(--color-accent-soft)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:pointer-events-none disabled:opacity-50"
          aria-label={thumbAriaLabels?.[i] ?? rootLabel ?? "Value"}
        />
      ))}
    </RadixSlider.Root>
  );
}
