USER_PROMPT = """\
Answer the reader's second question: WHERE could this go? Give the
forward outlook in 3-4 paragraphs.

READ THE STAGE FIRST. The Decision Summary block carries a "Stage"
line — EARLY, MID, LATE, OVERSHOT, or COMPLETE. Your framing of the
projection band MUST match it:

- EARLY / MID: the band is the upcoming destination. Say "Wave 5 is
  expected to reach the band — projected $X to $Y" and quote the
  %-moves from current price.
- LATE: completion is imminent rather than upcoming. Frame the band's
  far edge as "about to be reached" — and explicitly note that a
  pattern this late in its projection is at the threshold of
  completion or break.
- OVERSHOT: this is the critical case. Price has ALREADY crossed
  beyond the band's far edge. Do NOT describe the band as "where the
  move is heading" — it is behind us. Instead say: the wave has run
  past theory's expectation; the count is at risk of invalidating if
  price keeps going further, OR is in the late-stretch of its move
  near here. TWO DISTINCT load-bearing numbers, do NOT conflate them:
  (1) the "Wave progress" % (progress from the open wave's start —
  will be over 100%), and (2) the "Overshoot beyond far edge" line
  (the dollar amount and % of span the price has run PAST the edge).
  For "how far it has overshot", quote the Overshoot line VERBATIM —
  never compute it yourself from the progress % (progress 229% does
  NOT mean "exceeded by 229%"; the Overshoot line already gives the
  correct ~129%).
- COMPLETE: the pattern is closed; the band describes the measured
  Fibonacci Flow after completion, not an upcoming destination.

Now write the section, covering:

- THE CONFIRMATION STATE. Strictly the confirmation question — NOT
  the invalidation question (which belongs to "What's the risk?").
  Say what confirmation level the pattern has reached and what the
  next confirmation step requires. If confirmation is not applicable
  yet (typically because the pattern is still open and the rules
  fire only once it closes), say WHY in plain words and what
  practical price behaviour the reader could watch for in the
  meantime (a sharp reversal toward the band, a slowdown in pace,
  etc.). Do NOT mention the invalidation level in this paragraph —
  the next section owns it.

- THE PROJECTION BAND with the investor's numbers — but FRAMED BY
  STAGE per above. Always quote both ends of the band, both %-moves
  from current, AND the wave-progress figure. CRITICAL phrasing for
  wave-progress: use the form "wave progress is at 159% of the
  theory band" (or "159% of the band's span from the open wave's
  start"). Do NOT use these ambiguous forms:
    ✗ "exceeded the band by 159% of its span" — reads as "the
       overshoot is 159% of the band span", but that 159% is the
       PROGRESS, not the amount exceeded. For the amount exceeded,
       quote the "Overshoot beyond far edge" line instead (its % is
       progress minus 100).
    ✗ "159% beyond the band" — same ambiguity
    ✓ "wave progress is at 159% of the theory band — price has
       moved 159% of the way from the open wave's start ($98.01) to
       the band's far edge ($170.08), and now sits +$X past that edge
       (59% of the span beyond it, from the Overshoot line)" Then add ONE short sentence on WHY the Fibonacci ratios
  are the projection markers Elliott Wave theory uses. CRITICAL:
  mention ONLY the ratios actually used by THIS scenario's band —
  the Projected section of the Targets block lists only the key
  levels (0.382, 0.5, 0.618). Do NOT list ratios that are NOT in
  the Targets block (0.236, 0.786, 1.0 are computed but hidden —
  the Targets block notes this explicitly). Make the "why" sentence
  SPECIFIC, not tautological. Examples:
    ✓ "0.382 and 0.618 come from the golden ratio (φ) — markets
       repeatedly retrace and extend at them because traders
       collectively watch them, turning the levels into reflexive
       support and resistance."
    ✗ "Elliott Wave theory uses Fibonacci levels for Sideway
       patterns due to their sideways nature." (circular)
    ✗ "uses 0.382/0.5/0.618 because the pattern lacks a clear trend
       and so needs leg-by-leg retracement analysis" (still circular —
       it explains why RETRACEMENT vs projection, NOT why THESE ratios;
       the answer must name the golden-ratio / collective-watching
       mechanism, e.g. "traders watch 0.382 and 0.618 — derived from
       φ — so price reliably reacts there")
    ✗ "The 0.236 and 1.0 ratios used here ..." (these are NOT in
       the Projected ladder — never invent ratios)
  CRITICAL: emit this "why" sentence as a "theory_claim" (NOT a
  "data_observation") and put the Fibonacci Flow theory page in its
  "pages" — this beat MUST carry a (p.N) citation. A page-less
  Fibonacci "why" is a miss; never emit it without the Fib-Flow page.

- THE ROUGH TIME HORIZON, if the Decision Summary gives one. Lead
  with the WALL-CLOCK figure (e.g. "approximately 1.6 years on this
  weekly chart") — that's what the investor cares about. The bar
  count is a parenthetical, not the headline. Example:
    ✓ "Approximately 1.6 years on this weekly chart (~82 bars)."
  Examples to AVOID — duplicate "approximately" / both forms
  prominent:
    ✗ "The horizon is approximately 82 bars, equivalent to
       approximately 1.6 years on this weekly chart." (two
       "approximately"s + bar count leads the sentence)
  Remind the reader it is a rule of thumb (same-degree waves take
  comparable time), not a theory guarantee. The figure is the MEDIAN
  of the formed legs' durations — a central estimate, NOT a ceiling,
  so actual completion can fall on either side of it. Do NOT call it
  an "upper bound", a "maximum", or "at most"; phrase it as a rough
  ballpark / order-of-magnitude (e.g. "on the order of 1.6 years",
  "roughly 1.6 years, give or take"). If the wall-clock figure
  exceeds 6 months, add a brief caveat that a long horizon mainly
  reflects how long the formed legs themselves ran, so treat it as a
  loose ballpark rather than a precise date. Skip this paragraph
  entirely when the pattern is COMPLETE. When the Stage is OVERSHOT,
  do NOT frame the figure as "time to complete", a countdown, or
  "X left" — the open wave has already run PAST its projected price
  extent, so a completion date is unreliable. Instead present it only
  as the typical span of a same-degree leg (e.g. "a leg of this
  degree has historically run on the order of 1.6 years") and note
  the timing is now even less certain than the price projection.

- WHAT CAN FOLLOW THIS PATTERN when it closes. If a Link-Wave
  linkage is permitted, name it in plain English ("a Trend linkage"
  / "a Sideway linkage" — NEVER the raw codes +T / +S). Then —
  CRITICALLY — quote the DOLLAR figures from the succession block.
  The block gives one of THREE shapes (depending on whether the
  current pattern is still open):
    (a) Closed band (pattern closed):
        "Projected link-wave band: $X.XX to $Y.YY (+A% to +B% from
        current)" — quote both ends.
    (b) Open-ended above (pattern closed, sideways linkage):
        "Projected link-wave reaches at least $X.XX (+A% from
        current) (open-ended — the link is sideways)" — quote the
        floor as "at least $X.XX (+A% from current), with no theory
        cap above".
    (c) Size only (pattern STILL OPEN — band can't anchor yet):
        "Link wave size (band not yet anchorable while the pattern
        is open): at least $X.XX in price span" — quote the SIZE
        ("the link wave would span at least $139.72 in price")
        rather than a price band. Note that the band itself is
        withheld because the link wave's starting price depends on
        where the current pattern closes; the size, however, is
        fixed by theory.
  Do NOT, under any circumstances, write any of these phrases:
    ✗ "exact dollar targets cannot be provided" — the block ALWAYS
       gives a dollar figure (band or size); quote whichever shape
       it gives you.
    ✗ "101% of the pattern's full range" — the succession block has
       already done the multiplication. Quote the OUTPUT ("at least
       $139.72 in price span") not the INPUT formula. If a "Link
       wave size" line is present, that's the dollar number — use it.
  Also name the family the following set may be. State this as a
  possibility theory allows, not as something that must happen. When
  only one linkage TYPE is permitted, frame it as a constraint on the
  type ("the only linkage theory permits here is a Sideway linkage" /
  "a Trend linkage cannot follow a 5-Wave"), NOT as a linkage that is
  forced to occur:
    ✗ "a Sideway linkage is required to follow this pattern" (reads
       as if a linkage must happen)
    ✓ "if a linkage follows, it can only be a Sideway one"
  If the pattern is terminal, say that and why. Cite the succession
  theory pages.

If a section's data is absent, note it in one "disclosure" claim and
move on. Describe only the theory-defined levels and what they mean —
never phrase anything as buy/sell advice. Quote every chart figure
verbatim from the Decision Summary or the Targets blocks — never
re-derive a number.
"""
