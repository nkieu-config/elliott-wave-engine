from __future__ import annotations

import json

from analyst.schemas.citation import CitationRef
from analyst.schemas.narration import (
    Claim,
    NarrationDraft,
    citations_from_draft,
    format_pages,
    narration_json_schema,
    parse_narration_draft,
    render_narration,
)


def test_json_schema_pages_items_enum_carries_allowed_pages():
    schema = narration_json_schema([100, 99, 99])
    pages = schema["properties"]["paragraphs"]["items"]["items"][
        "properties"
    ]["pages"]
    assert pages == {"type": "array", "items": {"enum": [99, 100]}}


def test_json_schema_empty_allowed_pages_pins_pages_to_length_zero():
    schema = narration_json_schema([])
    pages = schema["properties"]["paragraphs"]["items"]["items"][
        "properties"
    ]["pages"]
    assert pages == {"type": "array", "maxItems": 0}


def test_json_schema_type_enum_is_the_three_claim_types():
    schema = narration_json_schema([1])
    type_enum = schema["properties"]["paragraphs"]["items"]["items"][
        "properties"
    ]["type"]["enum"]
    assert set(type_enum) == {"data_observation", "theory_claim", "disclosure"}


def _wire(*paragraphs: list[dict]) -> str:
    return json.dumps({"paragraphs": list(paragraphs)})


def test_parse_valid_draft():
    raw = _wire(
        [
            {"text": "Score is 0.5.", "type": "data_observation"},
            {"text": "Wave 3 must exceed wave 2.", "type": "theory_claim",
             "pages": [99, 100]},
        ],
        [{"text": "No targets to cite here.", "type": "disclosure"}],
    )
    draft = parse_narration_draft(raw)
    assert draft is not None
    assert len(draft.paragraphs) == 2
    assert draft.paragraphs[0][1] == Claim(
        text="Wave 3 must exceed wave 2.", type="theory_claim",
        pages=[99, 100],
    )
    assert draft.paragraphs[0][0].pages == []
    assert len(draft.all_claims) == 3


def test_parse_tolerates_markdown_fence():
    inner = _wire([{"text": "A claim here.", "type": "data_observation"}])
    raw = f"```json\n{inner}\n```"
    draft = parse_narration_draft(raw)
    assert draft is not None
    assert draft.all_claims[0].text == "A claim here."


def test_parse_tolerates_single_line_fence():
    # ```json {...}``` with no newline after the fence used to parse as empty → None.
    inner = _wire([{"text": "A claim here.", "type": "data_observation"}])
    draft = parse_narration_draft(f"```json {inner}```")
    assert draft is not None
    assert draft.all_claims[0].text == "A claim here."


def test_parse_returns_none_on_malformed_json():
    assert parse_narration_draft("not json at all") is None
    assert parse_narration_draft("") is None
    assert parse_narration_draft(None) is None


def test_parse_returns_none_when_paragraphs_missing():
    assert parse_narration_draft(json.dumps({"foo": []})) is None


def test_parse_returns_none_on_unknown_claim_type():
    raw = _wire([{"text": "x", "type": "opinion"}])
    assert parse_narration_draft(raw) is None


def test_parse_returns_none_on_non_int_page():
    raw = _wire([{"text": "x", "type": "theory_claim", "pages": ["ninety"]}])
    assert parse_narration_draft(raw) is None


def test_parse_returns_none_when_pages_not_a_list():
    raw = _wire([{"text": "x", "type": "theory_claim", "pages": 99}])
    assert parse_narration_draft(raw) is None


def test_parse_returns_none_when_all_paragraphs_empty():
    assert parse_narration_draft(_wire([], [])) is None


def test_format_pages_contiguous_run_renders_as_range():
    assert format_pages([99, 100]) == "(p.99-100)"
    assert format_pages([101, 102, 103]) == "(p.101-103)"


def test_format_pages_non_contiguous_renders_as_list():
    assert format_pages([99, 103]) == "(p.99, p.103)"


def test_format_pages_single_and_empty():
    assert format_pages([91]) == "(p.91)"
    assert format_pages([]) == ""


def test_render_appends_page_range_to_a_theory_claim():
    draft = NarrationDraft(paragraphs=[[
        Claim(text="The score is low.", type="data_observation"),
        Claim(text="The pullback-depth window applies.", type="theory_claim",
              pages=[99, 100]),
    ]])
    rendered = render_narration(draft)
    assert rendered == (
        "The score is low. The pullback-depth window applies (p.99-100)."
    )
    assert rendered.count("The pullback-depth window applies") == 1


def test_render_joins_paragraphs_with_blank_line():
    draft = NarrationDraft(paragraphs=[
        [Claim(text="First para.", type="data_observation")],
        [Claim(text="Second para.", type="disclosure")],
    ])
    assert render_narration(draft) == "First para.\n\nSecond para."


def test_render_theory_claim_without_pages_gets_no_citation():
    draft = NarrationDraft(paragraphs=[[
        Claim(text="An unsourced claim.", type="theory_claim", pages=[]),
    ]])
    assert render_narration(draft) == "An unsourced claim."


def test_citations_expand_one_ref_per_page_of_a_theory_claim():
    draft = NarrationDraft(paragraphs=[[
        Claim(text="data", type="data_observation"),
        Claim(text="sourced theory", type="theory_claim", pages=[99, 100]),
        Claim(text="unsourced theory", type="theory_claim", pages=[]),
        Claim(text="disclosure", type="disclosure"),
    ]])
    cites = citations_from_draft(draft)
    assert cites == (
        CitationRef(page=99, claim_sentence="sourced theory"),
        CitationRef(page=100, claim_sentence="sourced theory"),
    )
