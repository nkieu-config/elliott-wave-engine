USER_PROMPT = """\
Answer the reader's third question: WHAT IS THE RISK if this count is
wrong? Write 2-3 paragraphs that cover the hard invalidation line AND
the soft warning signs already on the chart.

- THE HARD STOP. Open with the invalidation level from the Decision
  Summary block. Quote its price and the %-move from current price as
  written ("$98.01, a -53.9% move from current price"); say in plain
  words what crossing it would mean — that the wave count as the
  system has read it is rejected, and the stock has done something
  the pattern's theory does not permit. If the Decision Summary
  carries a Risk:Reward figure, mention it ("the upside band is
  roughly 3.2× the downside to invalidation") — frame it as the
  asymmetry of being right vs being wrong, not as advice. If the
  Decision Summary instead notes the band has been overshot (Stage =
  OVERSHOT) and so the R:R is undefined, say so plainly — invalidation
  is still the load-bearing risk number, but the "reward" calculation
  no longer applies in the conventional sense.

- THE SOFT WARNING SIGNS — open with the BOTTLENECK (the single
  weakest check) in plain words ("the swing-smoothness check"), then
  WHAT IT MEANS ON THE CHART — what an investor's eye should look
  for. Quote the specific leg / pair AND the exact value from the
  "Bottleneck Diagnosis" block (e.g. "leg 4's drawdown ratio of
  1.666 — the leg dipped more than 1.5× the move it made before
  recovering"), then translate that into the visual ("a clean
  impulse leg looks like a single push; this one zig-zagged inside
  itself"). The reader should finish able to spot the same warning
  on a fresh chart.

- THE NEXT WEAKEST CHECKS. The "Top-3 Weakness Detail" block in the
  Layer-1 data carries one line per top-3 weakest slot. Each line
  has ONE of two shapes:
    (a) Concrete detail: "Second-Weakest — pullback depth: 2 of 4
        pullbacks fall outside the healthy 0.382-0.618 window
        (depths: 0.21, 0.81)" — when intermediates are available.
    (b) Ranking-only: "Second-Weakest — pullback depth:
        structural-dimension slot; ranked by score only for this
        scenario." — when intermediates are absent.
  CRITICAL — RANK FIRST: open each of these claims with the explicit
  ordinal so the reader sees the ranking at a glance:
    ✓ "The pullback-depth check ranks SECOND-WEAKEST: 2 of 4 pullbacks
       fall outside the healthy 0.382-0.618 window (depths 0.21
       and 0.81), meaning..."
    ✓ "The wave-pacing check ranks THIRD-WEAKEST: leg pace spans
       1.09-2.34 (a 2.16× spread), meaning..."
    ✗ "Two pullbacks have depths of 0.804 and 0.663..." (no rank
       — reader doesn't know if this is 2nd or 3rd)
  For shape (a): quote the concrete value verbatim and translate it
  into a visual cue ("too shallow means the pullback barely dented
  the prior push; too deep means it ate most of it").
  For shape (b): name the check, its rank, its dimension (structural
  / visual) — that is the maximum honest statement. DO NOT write any
  of these phrases, ever:
    ✗ "no per-leg details available"
    ✗ "no details provided"
    ✗ "with no per-leg detail"
  Even if the Layer-1 block uses similar wording in a fallback, the
  narration should always speak in terms of "the check ranks
  second-weakest in the structural dimension" — never frame the
  absence of detail as a missing data warning to the reader.
  When the second/third weakest check is pullback-depth or wave-
  pacing — both of which have theory bindings (Fibonacci Retracement
  window, Same-degree principle) — mark the claim as a theory_claim
  and cite the slot's theory pages (pp.99-100 for pullback-depth,
  pp.91 and 96 for wave-pacing). Swing-smoothness and pivot-sharpness
  are heuristics with NO theory binding; mark those as
  data_observations.

Do NOT recite a check's procedure ("evaluates how X by Y", "the
measurement requires marking the start and end of a leg"). The
dashboard already shows the definitions; your job is the
interpretation + the visual cue + the specific values. Quote every
figure verbatim from the data block; never invent or round a number.
Refer to legs by "Wave 3" / "the fourth leg", never `S3` / `S4`.
"""
