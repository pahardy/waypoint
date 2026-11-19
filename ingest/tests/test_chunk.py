from waypoint_ingest.chunk import pack, token_count
from waypoint_ingest.normalize import Paragraph
from waypoint_ingest.pipeline import build_chunks, pdf_sections
from waypoint_ingest.sources import Source


def source(jurisdiction="CA"):
    return Source(
        id="aim",
        title="Test manual",
        publisher="Transport Canada",
        edition="2026-2",
        published="2026-10",
        url="https://example.org/aim.pdf",
        jurisdiction=jurisdiction,
        format="pdf",
        priority=1,
        exams=["PSTAR"],
        licence="test",
    )


def test_token_count_counts_words_and_punctuation():
    assert token_count("Report: 3 000 ft.") == 6


def test_small_paragraphs_are_packed_together():
    pieces = pack([Paragraph(1, "one two"), Paragraph(2, "three")], max_tokens=10)
    assert [(p.page, p.text) for p in pieces] == [(1, "one two\n\nthree")]


def test_pieces_stay_within_the_size_limit():
    paragraphs = [Paragraph(1, "word " * 6), Paragraph(1, "word " * 6)]
    assert [token_count(p.text) for p in pack(paragraphs, max_tokens=10)] == [6, 6]


def test_long_paragraph_is_split():
    pieces = pack([Paragraph(3, " ".join(["word"] * 25))], max_tokens=10)
    assert [token_count(p.text) for p in pieces] == [10, 10, 5]
    assert {p.page for p in pieces} == {3}


def test_chunks_carry_citation_fields(outlined_pdf):
    _, chunks = build_chunks(source(), pdf_sections(outlined_pdf)[0])
    chunk = next(c for c in chunks if c.section_ref == "GEN 2.0")
    assert chunk.id == "aim:GEN 2.0:0"
    assert (chunk.source_id, chunk.edition, chunk.page) == ("aim", "2026-2", 2)
    assert chunk.heading_path[-1] == "2.0 Safety"


def test_chunks_never_cross_a_section_boundary(outlined_pdf):
    _, chunks = build_chunks(source(), pdf_sections(outlined_pdf)[0])
    texts = {c.section_ref: c.text for c in chunks}
    assert texts["GEN 1.1"].endswith("(a) A list item.")
    assert texts["GEN 1.2"] == "Units text in the right column."


def test_empty_parent_sections_have_no_chunks(outlined_pdf):
    _, chunks = build_chunks(source(), pdf_sections(outlined_pdf)[0])
    assert "GEN 1.0" not in {c.section_ref for c in chunks}


def test_non_canadian_sources_tag_their_chunks(outlined_pdf):
    _, chunks = build_chunks(source("non-CA"), pdf_sections(outlined_pdf)[0])
    assert {c.jurisdiction for c in chunks} == {"non-CA"}
