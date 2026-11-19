import pymupdf
import pytest


def text(page, x, y, value, size=10, bold=False):
    """Place text with its top edge at y (insert_text takes the baseline)."""
    font = "hebo" if bold else "helv"
    page.insert_text((x, y + size), value, fontname=font, fontsize=size)


@pytest.fixture
def outlined_pdf(tmp_path):
    """A two-page, two-column PDF laid out like the TC AIM, with bookmarks."""
    doc = pymupdf.open()
    for number in (1, 2):
        page = doc.new_page(width=612, height=792)
        text(page, 62, 22, "TC AIM", size=9)
        text(page, 511, 22, "October 1, 2026", size=9)
        text(page, 587, 765, str(number), size=10)

    first, second = doc[0], doc[1]
    text(first, 62, 50, "1.0 General Information", size=14, bold=True)
    text(first, 62, 80, "1.1 Aeronautical", size=12, bold=True)
    text(first, 98, 94, "Information Services", size=12, bold=True)
    text(first, 62, 112, "The first paragraph wraps onto a")
    text(first, 62, 124, "second line about pre-")
    text(first, 62, 136, "flight checks.")
    text(first, 62, 160, "A second paragraph starts after a gap.")
    text(first, 62, 172, "(a) A list item.")
    text(first, 322, 380, "1.2 Units", size=12, bold=True)
    text(first, 576, 380, "GEN", size=31, bold=True)
    text(first, 322, 400, "Units text in the right column.")
    text(second, 62, 50, "2.0 Safety", size=14, bold=True)
    text(second, 62, 70, "Safety text on page two.")

    doc.set_toc(
        [
            [1, "GEN—General", 1],
            [2, "1.0\tGeneral Information", 1],
            [3, "1.1\tAeronautical Information Services", 1],
            [3, "1.2\tUnits", 1],
            [2, "2.0\tSafety", 2],
            [3, "2.1\tNot In The Text", 2],
        ]
    )
    path = tmp_path / "outlined.pdf"
    doc.save(path)
    return path
