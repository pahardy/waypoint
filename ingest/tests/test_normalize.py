from waypoint_ingest.normalize import paragraphs
from waypoint_ingest.pdf_lines import Line


def line(text, y, page=1, column=0, bullet=False):
    return Line(
        page=page,
        column=column,
        x=62,
        y=y,
        text=text,
        size=10,
        bold=False,
        bullet=bullet,
    )


def texts(lines):
    return [p.text for p in paragraphs(lines)]


def test_wrapped_lines_join_into_one_paragraph():
    assert texts([line("Pilots shall", 100), line("report.", 112)]) == [
        "Pilots shall report."
    ]


def test_vertical_gap_starts_a_paragraph():
    assert texts([line("One.", 100), line("Two.", 130)]) == ["One.", "Two."]


def test_line_end_hyphen_is_kept_without_a_space():
    assert texts([line("a radio-", 100), line("equipped aircraft", 112)]) == [
        "a radio-equipped aircraft"
    ]


def test_list_items_and_notes_start_paragraphs():
    lines = [
        line("as follows:", 100),
        line("(a) first;", 112),
        line("NOTE: see MAP 3.0.", 124),
    ]
    assert texts(lines) == ["as follows:", "(a) first;", "NOTE: see MAP 3.0."]


def test_paragraph_continues_into_the_next_column():
    lines = [line("The pilot shall", 700), line("report the position.", 48, column=1)]
    assert texts(lines) == ["The pilot shall report the position."]


def test_finished_sentence_ends_the_paragraph_at_a_column_break():
    lines = [line("Report the position.", 700), line("Next topic.", 48, page=2)]
    paragraph = paragraphs(lines)[1]
    assert (paragraph.text, paragraph.page) == ("Next topic.", 2)
