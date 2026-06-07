from __future__ import annotations

from analyst.schemas.citation import CitationReport


def build_repair_prompt(
    base_prompt: str, prior_answer: str, report: CitationReport,
    *, mode: str = "analysis",
) -> str:
    issues: list[str] = []
    if report.malformed_json:
        issues.append(
            "- Your previous answer was not valid JSON and could not be "
            "parsed. Return ONLY a single well-formed JSON object of the "
            'shape {"paragraphs": [[<claim>, ...], ...]} — no markdown '
            "fences, no preamble, every bracket and brace balanced."
        )
    if report.too_short:
        # QA answers may be a single sentence; narration wants 2-3 paragraphs.
        if mode == "qa":
            issues.append(
                "- Your previous answer was empty or far too short. Produce a "
                "complete answer that directly addresses the question; a single "
                "clear sentence is sufficient for a simple question."
            )
        else:
            issues.append(
                "- Your previous answer was empty or far too short. Produce a "
                "complete narration (2-3 short paragraphs) that addresses the "
                "mode's question in full."
            )
    if report.disallowed_pages:
        cited = ", ".join(f"(p.{p})" for p in sorted(report.disallowed_pages))
        allowed = (
            ", ".join(f"(p.{p})" for p in sorted(report.allowed_pages))
            or "(no pages are citeable here)"
        )
        issues.append(
            f"- You cited {cited}, which are NOT in the allowed set. "
            f"Cite only these pages: {allowed}. Remove or correct every "
            f"disallowed citation."
        )
    if report.unsourced_claims:
        listed = "\n".join(f"    • {s}" for s in report.unsourced_claims)
        issues.append(
            '- These claims are typed "theory_claim" but their "pages" field '
            f"is empty:\n{listed}\n"
            '  For each one: list one or more allowed pages in "pages", OR '
            'retype it as "data_observation" / "disclosure".'
        )
    if report.raw_identifier_claims:
        listed = "\n".join(f"    • {s}" for s in report.raw_identifier_claims)
        issues.append(
            "- These claims leak a raw code identifier (a code-style token "
            'such as "pull_depth_discipline" or "5W_SIDEWAY") instead of '
            f"plain words:\n{listed}\n"
            '  Rewrite each in plain language — e.g. "the pullback-depth '
            'check", or "a five-wave sideways pattern".'
        )
    if report.arithmetic_chain_claims:
        listed = "\n".join(f"    • {s}" for s in report.arithmetic_chain_claims)
        issues.append(
            "- These claims narrate an arithmetic chain — a calculation "
            f'such as "X times Y":\n{listed}\n'
            "  Rewrite each to state what the numbers MEAN for the wave "
            "count, not how they combine. Drop the explicit "
            "multiplication / division."
        )
    if report.prose_page_claims:
        listed = "\n".join(f"    • {s}" for s in report.prose_page_claims)
        issues.append(
            "- These claims write a page reference inside the prose — a "
            'phrase such as "page 103" or "p.91":\n' + listed + "\n"
            "  Remove the page reference from the text entirely; put the "
            'page number(s) ONLY in the claim\'s "pages" field. The (p.N) '
            "citation is formatted for you — never write one in the text."
        )
    if report.ungrounded_citation_claims:
        listed = "\n".join(f"    • {s}" for s in report.ungrounded_citation_claims)
        issues.append(
            "- These claims are typed \"theory_claim\" but their cited page "
            f"does NOT actually state what the claim asserts:\n{listed}\n"
            "  For each one: either cite the page that genuinely contains "
            "this theory, or — if no provided page supports it — rewrite it "
            'as a "data_observation" / "disclosure". Do not state Elliott-Wave '
            "theory the cited page does not contain."
        )
    if report.meta_system_claims:
        listed = "\n".join(f"    • {s}" for s in report.meta_system_claims)
        issues.append(
            "- These claims name an internal system component (a phrase such "
            "as \"the verifier\", \"Layer-1\", \"the gate\", or \"bottleneck "
            f"diagnosis\") instead of describing the underlying fact:\n"
            f"{listed}\n"
            "  Rewrite each in user-facing terms — say what the fact IS, not "
            "which subsystem produced it. For example, \"the verifier has "
            "not evaluated this scenario\" → \"the rule check waits until "
            "the pattern completes\"; \"the Layer-1 data shows\" → \"the "
            "chart shows\"."
        )
    if report.procedural_recitation_claims:
        listed = "\n".join(
            f"    • {s}" for s in report.procedural_recitation_claims
        )
        issues.append(
            "- These claims recite a check's GENERAL procedure (e.g. "
            "\"evaluates how X by Y\", \"the measurement requires marking "
            "the start and end of a leg\") instead of saying what THIS "
            f"chart's values MEAN:\n{listed}\n"
            "  Rewrite each so it reads as an interpretation of this "
            "scenario's specific numbers: which leg / pair, what value, "
            "and what that value implies for the reader's confidence. The "
            "dashboard already shows the definitions; the model's job is "
            "the interpretation."
        )
    if report.fabricated_number_claims:
        listed = "\n".join(f"    • {s}" for s in report.fabricated_number_claims)
        issues.append(
            "- These claims state a numeric figure that is NOT present in "
            f"the Layer-1 data block (a rule-4 violation):\n{listed}\n"
            "  For each one: either drop the figure entirely, or replace it "
            "with the exact value as written in the Layer-1 block. Never "
            "round, recompute, or invent a number. Standard Fibonacci ratios "
            "(0.382 / 0.5 / 0.618 …) are fine without grounding; chart "
            "figures (prices, ratios, percentages) are not."
        )
    if report.fragment_claims:
        listed = "\n".join(f"    • {s}" for s in report.fragment_claims)
        issues.append(
            "- These claims read as SENTENCE FRAGMENTS — they open with "
            "\"And \", \"With \", \"Meaning \", \"Which \", \"That \" etc., "
            f"or otherwise lack a self-contained subject + verb:\n{listed}\n"
            "  Rewrite each as a complete sentence (subject + verb + "
            "complete predicate), OR merge it into the prior claim so the "
            "two together form one grammatical sentence. The narration is "
            "rendered as plain prose; fragments read as broken writing."
        )
    issues_md = "\n".join(issues) if issues else "- (no specific issue recorded)"
    return (
        f"{base_prompt}\n\n"
        "[REVISION REQUEST]\n"
        "Your previous answer needs the revisions below before it can be "
        "shown.\n\n"
        f"--- previous answer ---\n{prior_answer}\n"
        "--- end of previous answer ---\n\n"
        f"Problems to fix:\n{issues_md}\n\n"
        "Rewrite the answer as a valid JSON NarrationDraft with the same "
        "content, facts, and mode scope — change only what is needed to fix "
        "the problems above. Output the JSON object only, with no preamble."
    )
