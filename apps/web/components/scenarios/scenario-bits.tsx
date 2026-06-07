import { CheckCircle2, Hourglass } from "lucide-react";
import { cn } from "@/lib/cn";
import { familyColor, roleShort } from "@/lib/scenario-format";
import type { Scenario } from "@/lib/types";

const MEDAL_BG: Record<number, string> = {
  1: "linear-gradient(135deg, #fde047 0%, #f59e0b 100%)",
  2: "linear-gradient(135deg, #e5e7eb 0%, #9ca3af 100%)",
  3: "linear-gradient(135deg, #fdba74 0%, #b45309 100%)",
};

export function RankBadge({
  scoreRank,
  medalRank,
  selected,
}: {
  scoreRank: number;
  medalRank: 1 | 2 | 3 | null;
  selected: boolean;
}) {
  const medal = medalRank !== null;
  return (
    <span
      className={cn(
        "grid place-items-center h-7 w-7 rounded shrink-0 text-[11px] font-bold ewl-num",
        medal
          ? "text-[#1c1206] shadow-[0_2px_8px_-2px_rgba(0,0,0,0.4)]"
          : selected
            ? "bg-accent-soft text-accent-bright border border-border-glow"
            : "bg-bg text-muted border border-border",
      )}
      style={medal && medalRank ? { background: MEDAL_BG[medalRank] } : undefined}
      aria-label={medal ? `Medal rank ${medalRank}` : `Rank ${scoreRank}`}
    >
      {medal ? (medalRank === 1 ? "🥇" : medalRank === 2 ? "🥈" : "🥉") : `#${scoreRank}`}
    </span>
  );
}

// The single carrier of family colour in text rows.
export function FamilyDot({ family }: { family: string }) {
  return (
    <span
      className="h-2 w-2 shrink-0 rounded-full"
      style={{ background: familyColor(family) }}
      aria-hidden="true"
    />
  );
}

export function ScenarioStatusPill({ scenario }: { scenario: Scenario }) {
  const formingRole =
    !scenario.is_complete && scenario.open_subtree ? scenario.open_subtree.role : null;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.1em] font-semibold ewl-num px-1.5 py-0.5 rounded shrink-0",
        scenario.is_complete ? "bg-up/10 text-up" : "bg-warn/10 text-warn",
      )}
    >
      {scenario.is_complete ? (
        <>
          <CheckCircle2 className="h-2.5 w-2.5" />
          Complete
        </>
      ) : (
        <>
          <Hourglass className="h-2.5 w-2.5" />
          {formingRole ? roleShort(formingRole) : "Open"}
        </>
      )}
    </span>
  );
}

export function ChevronDownGlyph({ open }: { open: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={cn("h-3 w-3 transition-transform", open ? "rotate-0" : "-rotate-90")}
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}
