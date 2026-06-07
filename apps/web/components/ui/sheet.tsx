"use client";

import * as RadixDialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import * as React from "react";
import { cn } from "@/lib/cn";

export const Sheet = RadixDialog.Root;
export const SheetTrigger = RadixDialog.Trigger;
export const SheetClose = RadixDialog.Close;

const SIDE_CLASSES: Record<"left" | "right" | "bottom", string> = {
  left: "left-0 top-0 h-full w-[88vw] max-w-sm data-[state=open]:animate-in data-[state=open]:slide-in-from-left data-[state=closed]:animate-out data-[state=closed]:slide-out-to-left",
  right:
    "right-0 top-0 h-full w-[88vw] max-w-sm data-[state=open]:animate-in data-[state=open]:slide-in-from-right data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right",
  // 65vh leaves the top third of the chart visible so it reacts to scenario
  // selection without closing the drawer.
  bottom:
    "left-0 right-0 bottom-0 h-[65vh] data-[state=open]:animate-in data-[state=open]:slide-in-from-bottom data-[state=closed]:animate-out data-[state=closed]:slide-out-to-bottom",
};

interface SheetContentProps extends React.ComponentPropsWithRef<typeof RadixDialog.Content> {
  side?: "left" | "right" | "bottom";
  title: string;
  showClose?: boolean;
}

export function SheetContent({
  className,
  side = "right",
  title,
  showClose = true,
  children,
  ref,
  ...props
}: SheetContentProps) {
  return (
    <RadixDialog.Portal>
      <RadixDialog.Overlay
        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0"
      />
      <RadixDialog.Content
        ref={ref}
        // Opt out of Radix's "missing Description" a11y warning (visible Title,
        // no body Description); callers may override via {...props}.
        aria-describedby={undefined}
        className={cn(
          "fixed z-50 flex flex-col ewl-surface-sidebar shadow-[var(--shadow-elev)]",
          "border-border",
          side === "left" && "border-r",
          side === "right" && "border-l",
          side === "bottom" && "border-t rounded-t-2xl",
          SIDE_CLASSES[side],
          "duration-200",
          className,
        )}
        {...props}
      >
        <span
          aria-hidden="true"
          className={cn(
            "pointer-events-none absolute h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent",
            side === "bottom" ? "inset-x-6 top-0" : "inset-x-0 top-0",
          )}
        />
        {side === "bottom" && (
          <div className="flex justify-center pt-2.5 pb-1" aria-hidden="true">
            <span className="h-1 w-9 rounded-full bg-border-hi" />
          </div>
        )}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <RadixDialog.Title className="text-[11px] font-semibold uppercase tracking-[0.14em] text-text-dim">
            {title}
          </RadixDialog.Title>
          {showClose && (
            <RadixDialog.Close
              className="flex items-center justify-center w-9 h-9 rounded-md text-muted hover:bg-panel-elev hover:text-text focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
              aria-label="Close panel"
            >
              <X className="h-4 w-4" />
            </RadixDialog.Close>
          )}
        </div>
        {/* Safe-area pb so the last item clears the iOS home indicator. */}
        <div className="flex-1 min-h-0 overflow-auto overscroll-contain pb-[env(safe-area-inset-bottom)]">
          {children}
        </div>
      </RadixDialog.Content>
    </RadixDialog.Portal>
  );
}
