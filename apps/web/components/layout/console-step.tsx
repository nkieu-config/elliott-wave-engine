"use client";

import { ChevronRight } from "lucide-react";
import { type ReactNode } from "react";
import { useDisclosure } from "@/lib/hooks/use-disclosure";
import { cn } from "@/lib/cn";

// `collapsible=false` renders a static (always-open) summary.
export function ConsoleStep({
  num,
  title,
  dirty,
  defaultOpen = false,
  collapsible = true,
  last = false,
  children,
}: {
  num: number;
  title: string;
  dirty?: boolean;
  defaultOpen?: boolean;
  collapsible?: boolean;
  last?: boolean;
  children: ReactNode;
}) {
  const { open, triggerProps, contentProps } = useDisclosure(defaultOpen);
  const isOpen = collapsible ? open : true;
  return (
    <section
      className="ewl-console-step"
      data-open={isOpen}
      data-dirty={dirty || undefined}
    >
      <div className="ewl-console-rail">
        <span className="ewl-console-node" aria-hidden="true">
          {num}
        </span>
        {!last && <span className="ewl-console-line" aria-hidden="true" />}
      </div>
      <div className="ewl-console-card">
        {collapsible ? (
          <button type="button" className="ewl-console-summary" {...triggerProps}>
            <span className="flex items-center gap-2 min-w-0">
              <span className="truncate">{title}</span>
              {dirty && <span className="sr-only">(has non-default values)</span>}
            </span>
            <ChevronRight
              className={cn(
                "h-3.5 w-3.5 transition-transform shrink-0",
                isOpen && "rotate-90",
              )}
              aria-hidden="true"
            />
          </button>
        ) : (
          <div className="ewl-console-summary ewl-console-summary-static">
            <span className="truncate">{title}</span>
          </div>
        )}
        {isOpen && (
          <div
            {...contentProps}
            aria-label={title}
            className="ewl-console-body space-y-3.5"
          >
            {children}
          </div>
        )}
      </div>
    </section>
  );
}
