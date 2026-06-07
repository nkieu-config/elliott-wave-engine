import { cn } from "@/lib/cn";
import { useDisclosure } from "@/lib/hooks/use-disclosure";
import { patternSubtype, prettyFamily } from "@/lib/scenario-format";
import type { Scenario } from "@/lib/types";
import {
  ChevronDownGlyph,
  FamilyDot,
  RankBadge,
  ScenarioStatusPill,
} from "@/components/scenarios/scenario-bits";
import {
  ConvictionReadout,
  MeasurementsBreakdown,
  ScoreChainRow,
  WeakLinkRow,
} from "@/components/scenarios/score-breakdown";

export function ScenarioInspector({
  scenario,
  rank,
  medalRank,
  topScore,
  totalScenarios,
}: {
  scenario: Scenario;
  rank: number | null;
  medalRank: 1 | 2 | 3 | null;
  topScore: number;
  totalScenarios: number;
}) {
  // Collapsed by default so the leaderboard keeps its height.
  const { open, triggerProps, contentProps } = useDisclosure();
  const waveCount = scenario.root.children.length;

  return (
    <section
      className={cn(
        "shrink-0 flex flex-col min-h-0 border-b border-border bg-panel-elev/40",
        open && "max-h-[58%]",
      )}
      // Left rail is the only accent so the tier-coloured figures don't fight an
      // emerald wash.
      style={{ boxShadow: "inset 2px 0 0 0 var(--color-accent)" }}
      aria-label="Selected scenario inspector"
    >
      <div className="shrink-0 px-5 pt-3.5 pb-3.5 space-y-3.5">
        <div className="flex items-center gap-3">
          <RankBadge scoreRank={rank ?? 0} medalRank={medalRank} selected />
          {/* Keyed on id so switching re-triggers the spring-in. */}
          <div key={scenario.id} className="ewl-spring-in flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <FamilyDot family={scenario.family} />
              <span className="text-[13px] font-bold uppercase tracking-[0.1em] text-text">
                {prettyFamily(scenario.family)}
              </span>
              {scenario.pattern_label && (
                <span className="text-[12px] text-muted truncate">
                  {patternSubtype(scenario.pattern_label)}
                </span>
              )}
            </div>
            <div className="mt-0.5 text-[12px] ewl-num text-faint">
              {waveCount} {waveCount === 1 ? "wave" : "waves"}
            </div>
          </div>
          <ScenarioStatusPill scenario={scenario} />
        </div>

        <ConvictionReadout
          scenario={scenario}
          topScore={topScore}
          rank={rank}
          totalScenarios={totalScenarios}
        />
        <WeakLinkRow scenario={scenario} />
      </div>

      <button
        type="button"
        {...triggerProps}
        className={cn(
          "shrink-0 w-full flex items-center gap-2 px-5 py-2",
          "text-[12px] uppercase tracking-[0.14em] font-semibold text-text-dim",
          "border-t border-border hover:bg-panel-elev/60 transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset",
        )}
      >
        <ChevronDownGlyph open={open} />
        Score detail
      </button>
      {open && (
        <div
          {...contentProps}
          aria-label="Score detail"
          className="flex-1 min-h-0 overflow-y-auto overscroll-contain px-5 py-3.5 space-y-3.5"
        >
          <ScoreChainRow scenario={scenario} />
          <MeasurementsBreakdown scenario={scenario} />
        </div>
      )}
    </section>
  );
}
