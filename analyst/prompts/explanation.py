USER_PROMPT = """\
Answer the reader's first question: WHAT am I looking at on this chart?
Write 2-3 paragraphs that do BOTH jobs at once — orient the investor
and teach how to read this pattern.

Cover:
- WHICH PATTERN, with the wave-by-wave prices. State the family in
  plain English ("a five-wave sideways pattern"), and walk through
  the formed waves in ONE compact sentence with their endpoints,
  directions and the open wave's progress so far. For example:
    ✓ "Waves 1-4 are formed — W1 rose to $199.68, W2 fell to $61.34,
       W3 rose to $170.08, W4 fell to $98.01 — and Wave 5 is open,
       having stretched from $98.01 to the current $212.49."
  CRITICAL — verb consistency: use "rose to" for every up leg and
  "fell to" for every down leg. Do NOT swap synonyms across waves
  ("Wave 2 fell, Wave 4 declined" reads as careless writing):
    ✗ "W1 rose to $199.68, W2 fell to $61.34, W3 climbed to $170.08,
       W4 declined to $98.01" (climbed / rose, declined / fell —
       inconsistent vocabulary)
    ✓ "W1 rose to $199.68, W2 fell to $61.34, W3 rose to $170.08,
       W4 fell to $98.01" (rose / fell repeated)
  Pull the wave endpoints from the Structure block and the current
  price from the Decision Summary. Then use the Decision Summary's
  "Stage" + "Wave progress" to describe WHERE in the open wave price
  sits (EARLY → "has just begun"; MID → "mid-stride"; LATE → "nearly
  complete"; OVERSHOT → "has stretched past where theory projected
  it to stop"). Do NOT say a wave is "opening" or "just beginning"
  when the Wave-progress figure is large.
  CRITICAL: if you mention overshoot, do it ONCE in this section.
  Do NOT add a follow-up sentence repeating the same fact. e.g.:
    ✗ "Wave 5 has overshot the projected target range. Price has
       moved beyond the upper end of the projection band, indicating
       the wave has overshot theoretical expectations." (two
       sentences saying the same thing back-to-back)
    ✓ "Wave 5 has stretched well beyond the projection band's upper
       end ($170.08), reaching $212.49." (one sentence, no repeat)

- THE CHART-RECOGNITION teaching: ONE concrete sentence the reader
  could apply to a fresh chart, in the form "If you see X on a
  chart, you're looking at this family". This is general Elliott
  Wave knowledge — emit it as a "data_observation" (no pages
  needed). Do NOT use a "disclosure" to refuse this beat with
  "the provided theory references do not specify visual chart cues"
  — the prompt is asking YOU to provide the rule from general
  Elliott-Wave knowledge, NOT to find it in the cited pages.
  Examples of useful rules:
    ✓ "If you see five distinct turning points that oscillate back and
       forth without a clear net climb or decline — the swings staying
       broadly range-bound rather than stair-stepping in one
       direction — that's a 5-Wave Sideway."
    ✓ "If you see five legs in one direction with the third leg
       clearly the longest, that's a 5-Wave Trend."
    ✓ "If you see three legs (high → dip → higher high, or low →
       rally → lower low) and the move clearly runs counter to the
       prior trend, that's a 3-Wave correction."
  CRITICAL — keep the Sideway recognition rule SUBTYPE-AGNOSTIC: it
  must hold for ANY 5-Wave Sideway on a fresh chart, and the family
  spans three shapes — contracting (highs step down, lows step up),
  balance (roughly flat boundaries), and expanding (boundaries spread
  apart). So do NOT bake one shape into the rule: never assert the
  boundaries are "horizontal", and equally do NOT assert they are
  "narrowing / converging" — each pins it to a single subtype. Keep
  the cue at the family level (range-bound oscillation, no net trend).
  The THIS-chart specifics — e.g. "here the highs fall while the lows
  rise, a contracting range" — belong in the wave-by-wave structure
  sentence ABOVE, not in the general recognition rule.
  Examples to AVOID (technical definitions, not chart cues):
    ✗ "This pattern is identified by alternating up and down legs
       where each wave's retracement is measured against previous
       legs using Fibonacci retracement levels." (technical, not
       chart-actionable)
    ✗ "The pattern is recognised by its theoretical structure."
       (vacuous)
  Keep it to plain prose; no formulas; one sentence.

- WHAT THE PATTERN MEANS FOR THE STOCK — only what the theory gives.
  This is also general Elliott Wave knowledge — emit it as a
  "data_observation" (no pages needed). Do NOT refuse this beat
  with "the provided theory references do not explicitly state
  the practical implications" — the prompt asks YOU to translate
  the pattern's meaning into investor language; it is well-
  established Elliott Wave general knowledge, not a citation
  question.
  A 5-Wave Sideway means consolidation: phrase it as a practical
  expectation ("expect range-bound action — neither a new high nor a
  new low until the pattern resolves"). A 5-Wave Trend means
  continuation of the structure's starting direction. A 3-Wave means
  a correction against a larger trend. Translate the theory term
  into what it means for the investor's expectations.
  CRITICAL for 5-Wave Sideway: do NOT say it resolves by "resuming /
  continuing the broader trend" or "breaking out to continue the
  trend". This pattern's own succession (the "What can follow" beat
  in the outlook) is a Link-Wave that may be another Sideway or a
  3-Wave correction — NOT a guaranteed trend continuation. Keep the
  meaning to range-bound-until-it-resolves; leave the post-pattern
  direction to the succession, do not assert a trend resumption.
  CRITICAL: do NOT echo the chart-recognition rule's wording. The
  two beats describe the same fact from different angles, so the
  vocabulary must be distinct:
    chart-rec rule    → "without a clear upward or downward trend"
    meaning sentence  → AVOID "no strong directional move" /
                              "no clear directional bias" /
                              "lacks a directional trend"
  Pick a CONSEQUENCE-oriented phrasing instead: "expect range-bound
  trading" / "pause within a larger structure" / "the stock is
  resting between two boundaries". The reader already heard the
  recognition rule; the second beat should add NEW information,
  not re-state the appearance.

- A SHORT RELIABILITY CLOSER — name the weakest check in plain words
  AND state its CONSEQUENCE for the reader's confidence in one
  sentence. Examples:
    ✓ "Its weakest check is swing smoothness — so trust the count's
       overall shape more than its precise wave-by-wave levels."
    ✓ "Wave pacing is the weakest check — the timing across waves
       is uneven, which lowers the count's reliability but does not
       reject it."
    ✗ "weakest check is swing-smoothness check" — do NOT repeat the
       word "check"; the slot name alone ("swing smoothness") follows
       "weakest check is".
  Do NOT end the section with a bare ranking like "the swing-
  smoothness check is the weakest." — that gives the reader nothing
  actionable.

A reader should finish this section understanding (a) the market story
and (b) one rule of thumb for spotting the pattern again. Do not name
"the verifier", "Layer-1", "the gate" or any other system component;
describe what the fact IS, not which subsystem produced it. Refer to
legs as "Wave 1 / Wave 2 / Wave 3" — never `S1` / `S2` / `S3`.
"""
