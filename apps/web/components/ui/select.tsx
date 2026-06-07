"use client";

import * as RadixSelect from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
import * as React from "react";
import { cn } from "@/lib/cn";

export const Select = RadixSelect.Root;
export const SelectValue = RadixSelect.Value;

export function SelectTrigger({
  className,
  children,
  ref,
  ...props
}: React.ComponentPropsWithRef<typeof RadixSelect.Trigger>) {
  return (
    <RadixSelect.Trigger
      ref={ref}
      className={cn(
        "flex h-9 w-full items-center justify-between rounded-md border border-border bg-bg px-3 py-1 text-sm text-text transition-colors hover:border-border-hi focus-visible:outline-none focus-visible:border-border-glow focus-visible:ring-2 focus-visible:ring-accent-soft data-[placeholder]:text-faint",
        className,
      )}
      {...props}
    >
      {children}
      <RadixSelect.Icon asChild>
        <ChevronDown className="h-3.5 w-3.5 text-muted" />
      </RadixSelect.Icon>
    </RadixSelect.Trigger>
  );
}

export function SelectContent({
  className,
  children,
  position = "popper",
  ref,
  ...props
}: React.ComponentPropsWithRef<typeof RadixSelect.Content>) {
  return (
    <RadixSelect.Portal>
      <RadixSelect.Content
        ref={ref}
        position={position}
        className={cn(
          "relative z-50 min-w-[8rem] overflow-hidden rounded-md border border-border-hi bg-panel text-text shadow-[var(--shadow-elev)]",
          "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0 data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95",
          position === "popper" && "data-[side=bottom]:translate-y-1",
          className,
        )}
        {...props}
      >
        <RadixSelect.Viewport className="p-1">{children}</RadixSelect.Viewport>
      </RadixSelect.Content>
    </RadixSelect.Portal>
  );
}

export function SelectItem({
  className,
  children,
  ref,
  ...props
}: React.ComponentPropsWithRef<typeof RadixSelect.Item>) {
  return (
    <RadixSelect.Item
      ref={ref}
      className={cn(
        "relative flex w-full cursor-default select-none items-center rounded-sm py-2 pl-8 pr-2 text-sm transition-colors outline-none",
        // Radix moves a roving highlight via data-highlighted, not DOM focus —
        // focus-visible: never fires, so style the highlighted state directly.
        "data-[highlighted]:bg-panel-elev data-[highlighted]:text-text",
        "data-[state=checked]:text-accent-bright",
        "data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className,
      )}
      {...props}
    >
      <span className="absolute left-2.5 flex h-3 w-3 items-center justify-center">
        <RadixSelect.ItemIndicator>
          <Check className="h-3 w-3 text-accent" />
        </RadixSelect.ItemIndicator>
      </span>
      <RadixSelect.ItemText>{children}</RadixSelect.ItemText>
    </RadixSelect.Item>
  );
}
