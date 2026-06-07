USER_PROMPT = """\
Answer the reader's fourth question: WHAT IF the system has read the
wrong pattern? Help the reader understand the alternative reading and
how to tell the two apart as the chart unfolds. Write 2-3 paragraphs.

- WHERE THIS SCENARIO SITS in the ranked table and how its relative
  PROBABILITY compares with the other scenarios. For the clear-vs-
  close call, use the "Lead strength" line in the Scenario Comparison
  block — do NOT judge it yourself. In particular never call a rank-1
  that is under 50% a "clear leader": if the line says "moderate
  lead", say it leads but is not decisive. Probabilities are
  percentages of the scenario pool — name them as such.

- THE ALTERNATIVE READING and WHAT IT WOULD MEAN for the investor.
  The Layer-1 data carries an "Alternative Scenario" block — quote
  the rank-2 family name in plain English (e.g. "a 3-Wave
  correction" instead of "5-Wave Sideway") AND its key dollar
  numbers from that block: projection band with %-moves from
  current, invalidation with %-move, implied direction. If the
  projection band sits in the OPPOSITE direction to the primary
  scenario's, say so plainly — that is the investor's load-bearing
  insight.
  When introducing each scenario's invalidation level, state BOTH in
  ONE comparative sentence (not two back-to-back), using the compact
  "+A% above" / "-B% below" form so the reader gets the asymmetry in
  a single glance. CRITICAL on the qualifier "only": it means "near"
  — attach it ONLY to a level that is genuinely close (roughly within
  15% of current price). A large distance is NOT "only": writing
  "only -62.8% below" misleads, because a 60%+ drop is far, not near.
  Apply this test to each level independently — when both are far,
  use neither "only"; when one is close and one far, mark just the
  close one:
    ✓ (one near) "The primary's invalidation sits -53.9% below current
       while the alternative's is only +3.7% above — a small upward
       move would settle the question immediately." (the near level
       gets "only"; the far one does not)
    ✓ (both far) "The primary's invalidation sits -62.8% below current
       and the alternative's -69.0% below — both are distant, so a
       near-term break is unlikely to decide between them." (no "only"
       on either; both are far)
    ✗ "sits only -62.8% below ... only -69.0% below" ("only" on a
       60%+ drop reads as if the level were close — it is not)
    ✗ two back-to-back sentences both quoting the primary (the first
       is redundant)
  CRITICAL on the figures: quote percentages VERBATIM from the
  Decision Summary block (e.g. "-53.9%", "+3.7%"). Do NOT round
  "-53.9%" to "-54%" — that is a rule-4 violation.
  Avoid the wordier "a rise of A% from current" form. If the
  Alternative Scenario block is absent (only one scenario found),
  emit a "disclosure" claim noting that and skip the rest of this
  beat.

- WHAT SEPARATES THEM. For the top two scenarios, name each one's
  weakest check, then describe the largest gap between them. The
  gap is in CHECK-SCORE units (a 0-1 internal grade), not in
  probability percentages — so phrase it as "score points" or "0-1
  score" rather than "percentage points":
    ✓ "the wave-pacing check is 19 score points stronger on this
       reading"
    ✓ "the wave-pacing check is 0.19 higher on the 0-1 check
       score for this reading"
    ✗ "19 percentage points stronger" (percentage points = a
       difference between two percentages; the check score is a
       0-1 grade, not a percentage)
    ✗ "+19% in favor of this scenario" (probability units, not
       score units)
  Then give the reader an EDUCATIONAL BEAT —
  the visual cue that distinguishes the two patterns when both fit
  the same data. CRITICAL: read the "Open wave direction" line in
  the Decision Summary block before writing this. If the open wave
  is UP, the distinguishing cue is "watch for a fifth leg upward to
  confirm the 5-Wave; failure to form one supports the 3-Wave";
  if DOWN, mirror. Do NOT pick the direction by guess.
  In THIS paragraph (not as a dangling fourth paragraph), also
  state in one short clause whether this scenario's lead is driven
  by shape-and-proportion quality or by visual appearance. The
  whole "what separates them" beat is ONE paragraph — do NOT split
  the lead-driver sentence into its own paragraph; that reads as a
  dangling afterthought.

If only one scenario was found, say so in one "disclosure" claim and
instead characterise this scenario's own mix of strengths and
weaknesses — do not write a long apology.

Help the reader understand WHY this count is the more credible reading
of the chart — and how they would notice if the chart starts telling a
different story.
"""
