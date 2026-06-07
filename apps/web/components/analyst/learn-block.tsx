"use client";

import { Check, ChevronDown, Eye, Ruler } from "lucide-react";
import { useEducation } from "@/lib/query";
import { useDisclosure } from "@/lib/hooks/use-disclosure";
import { cn } from "@/lib/cn";
import { familyColor } from "@/lib/scenario-format";

// Deterministic (no-LLM) pattern education. `rules` are Elliott's hard laws;
// `visual_cues` are soft observations.
export function LearnBlock({ family }: { family: string | null }) {
  const { open, triggerProps, contentProps } = useDisclosure();
  const education = useEducation(family);

  if (!family) return null;

  const color = familyColor(family);

  return (
    <section
      className={cn(
        "rounded-md border bg-panel-elev/30 transition-colors",
        open
          ? "border-border-hi bg-panel-elev/50"
          : "border-border",
      )}
    >
      <button
        type="button"
        {...triggerProps}
        className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-md"
      >
        <span
          aria-hidden="true"
          className="h-3 w-[3px] rounded-[2px] shrink-0 bg-gradient-to-b from-accent to-cyan"
        />
        <span className="text-[12px] uppercase tracking-[0.14em] font-semibold text-text-dim shrink-0">
          Learn this pattern
        </span>
        {education.data && (
          <span className="text-[13px] text-text font-medium truncate min-w-0">
            · {education.data.title}
          </span>
        )}
        <ChevronDown
          className={cn(
            "h-3 w-3 ml-auto shrink-0 transition-transform text-muted",
            open && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>
      {open && (
        <div
          {...contentProps}
          aria-label={
            education.data ? `${education.data.title} — pattern education` : "Pattern education"
          }
          className="px-3.5 pb-3.5 pt-1"
        >
          {education.isLoading && <LearnSkeleton />}
          {education.isError && (
            <p className="text-[13px] text-down">
              Couldn’t load education content:{" "}
              {education.error instanceof Error
                ? education.error.message
                : String(education.error)}
            </p>
          )}
          {education.data && (
            <div className="space-y-3.5">
              <p
                className="text-[15px] font-medium text-text-dim leading-relaxed pl-3 border-l-2"
                style={{ borderColor: color }}
              >
                {education.data.one_line}
              </p>
              <LearnList
                heading="Structural rules"
                hint="must hold"
                icon={<Ruler className="h-3 w-3" aria-hidden="true" />}
                items={education.data.rules}
                variant="rule"
                color={color}
              />
              <LearnList
                heading="What to look for on the chart"
                hint="tends to show"
                icon={<Eye className="h-3 w-3" aria-hidden="true" />}
                items={education.data.visual_cues}
                variant="cue"
                color={color}
              />
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function LearnList({
  heading,
  hint,
  icon,
  items,
  variant,
  color,
}: {
  heading: string;
  hint: string;
  icon: React.ReactNode;
  items: string[];
  variant: "rule" | "cue";
  color: string;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline gap-1.5 text-[12px] uppercase tracking-[0.12em] font-semibold text-muted">
        <span style={{ color }}>{icon}</span>
        {heading}
        <span className="text-[10px] tracking-[0.1em] text-faint font-medium normal-case">
          · {hint}
        </span>
      </div>
      <ul className="space-y-2">
        {items.map((it, i) =>
          variant === "rule" ? (
            <li key={i} className="flex items-start gap-2">
              <Check
                className="h-3.5 w-3.5 mt-0.5 shrink-0"
                style={{ color }}
                aria-hidden="true"
              />
              <span className="text-[15px] text-text-dim leading-relaxed">
                {it}
              </span>
            </li>
          ) : (
            <li
              key={i}
              className="ml-4 text-[15px] text-text-dim leading-relaxed list-disc marker:text-faint"
            >
              {it}
            </li>
          ),
        )}
      </ul>
    </div>
  );
}

function LearnSkeleton() {
  return (
    <div className="space-y-3.5" aria-label="Loading pattern education…">
      <div className="space-y-1.5 pl-3 border-l-2 border-border-hi">
        <div className="ewl-skeleton h-3.5 w-full" />
        <div className="ewl-skeleton h-3.5 w-[88%]" />
      </div>
      <div className="space-y-2">
        <div className="ewl-skeleton h-3 w-32" />
        <div className="ewl-skeleton h-3.5 w-[94%]" />
        <div className="ewl-skeleton h-3.5 w-[80%]" />
      </div>
      <div className="space-y-2">
        <div className="ewl-skeleton h-3 w-40" />
        <div className="ewl-skeleton h-3.5 w-[90%]" />
        <div className="ewl-skeleton h-3.5 w-[72%]" />
      </div>
    </div>
  );
}
