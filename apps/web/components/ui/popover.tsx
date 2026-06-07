"use client";

import * as RadixPopover from "@radix-ui/react-popover";
import type * as React from "react";
import { cn } from "@/lib/cn";

// Non-modal by default: Radix gives Escape-to-close, outside-click dismissal, and
// focus-restore to the trigger — without trapping Tab inside (right for menus).
export const Popover = RadixPopover.Root;
export const PopoverTrigger = RadixPopover.Trigger;
export const PopoverClose = RadixPopover.Close;

export function PopoverContent({
  className,
  align = "start",
  side = "bottom",
  sideOffset = 6,
  children,
  ...props
}: React.ComponentPropsWithRef<typeof RadixPopover.Content>) {
  return (
    <RadixPopover.Portal>
      <RadixPopover.Content
        align={align}
        side={side}
        sideOffset={sideOffset}
        className={cn(
          "z-50 rounded-md border border-border-hi bg-panel p-1.5",
          "shadow-[0_16px_36px_-16px_rgba(0,0,0,0.7)] focus:outline-none",
          "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
          className,
        )}
        {...props}
      >
        {children}
      </RadixPopover.Content>
    </RadixPopover.Portal>
  );
}
