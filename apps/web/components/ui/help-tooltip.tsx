"use client";

import * as Tooltip from "@radix-ui/react-tooltip";
import { cn } from "@/lib/cn";

export function HelpTooltip({
  text,
  label = "What this controls",
}: {
  text: string;
  label?: string;
}) {
  // Provider is app-wide (app/providers.tsx) so all tooltips share one timer.
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <button
          type="button"
          aria-label={label}
          className={cn("ewl-help-icon")}
        >
          ?
        </button>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          side="right"
          align="center"
          sideOffset={6}
          collisionPadding={12}
          className={cn(
            "z-50 max-w-xs px-3 py-2 rounded-md text-[11px] leading-relaxed",
            "bg-panel-deep border border-border-hi shadow-[0_16px_36px_-16px_rgba(0,0,0,0.7)]",
            "text-text-dim",
            "data-[state=delayed-open]:animate-in data-[state=delayed-open]:fade-in-0",
          )}
        >
          {text}
          <Tooltip.Arrow className="fill-border-hi" />
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
