"use client";

import * as RadixLabel from "@radix-ui/react-label";
import * as React from "react";
import { cn } from "@/lib/cn";

export function Label({
  className,
  ref,
  ...props
}: React.ComponentPropsWithRef<typeof RadixLabel.Root>) {
  return (
    <RadixLabel.Root
      ref={ref}
      className={cn(
        "text-[10px] font-semibold uppercase tracking-[0.1em] text-muted",
        className,
      )}
      {...props}
    />
  );
}
