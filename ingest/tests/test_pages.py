import pymupdf
import pytest
from conftest import text

from waypoint_ingest.pages import has_section_bookmarks, page_sections


@pytest.fixture
def guide_pdf(tmp_path):
    """A two-page guide without bookmarks, page numbers in the footer."""
    doc = pymupdf.open()
    first = doc.new_page(width=612, height=792)
    text(first, 72, 72, "Examinations", size=20, bold=True)
    text(first, 72, 100, "Applicants shall write an")
    text(first, 72, 114, "examination of 100 questions.")
    text(first, 303, 737, "4")
    second = doc.new_page(width=612, height=792)
    text(second, 72, 100, "A page with no heading.")
    text(second, 303, 737, "v")
    path = tmp_path / "guide.pdf"
    doc.save(path)
    return path


def test_one_section_per_page_cited_by_page(guide_pdf):
    sections = page_sections(guide_pdf, "TP 1", "Guide")
    assert [(s.ref, s.page) for s in sections] == [("TP 1 p.1", 1), ("TP 1 p.2", 2)]


def test_heading_path_uses_the_first_bold_line(guide_pdf):
    first, second = page_sections(guide_pdf, "TP 1", "Guide")
    assert first.heading_path == ["Guide", "Examinations", "TP 1 p.1"]
    assert second.heading_path == ["Guide", "TP 1 p.2"]


def test_page_numbers_are_dropped(guide_pdf):
    first, second = page_sections(guide_pdf, "TP 1", "Guide")
    assert [p.text for p in first.paragraphs] == [
        "Examinations",
        "Applicants shall write an examination of 100 questions.",
    ]
    assert [p.text for p in second.paragraphs] == ["A page with no heading."]


def test_section_bookmark_detection(guide_pdf, outlined_pdf):
    assert not has_section_bookmarks(guide_pdf)
    assert has_section_bookmarks(outlined_pdf)


@pytest.fixture
def two_column_pdf(tmp_path):
    """A handbook page whose right column starts higher than its left column
    but comes later in the PDF, as in the FAA handbooks."""
    doc = pymupdf.open()
    page = doc.new_page(width=594, height=792)
    text(page, 40, 40, "Aeromedical Factors", size=16, bold=True)
    text(page, 40, 100, "Left column text comes first.")
    text(page, 320, 70, "Right column text comes second.")
    text(page, 36, 728, "2-22")
    path = tmp_path / "handbook.pdf"
    doc.save(path)
    return path


def test_two_column_pages_follow_the_pdf_block_order(two_column_pdf):
    (section,) = page_sections(two_column_pdf, "PHAK", "Handbook", columns=2)
    assert [p.text for p in section.paragraphs] == [
        "Aeromedical Factors",
        "Left column text comes first.",
        "Right column text comes second.",
    ]
    assert section.heading_path == ["Handbook", "Aeromedical Factors", "PHAK p.1"]
