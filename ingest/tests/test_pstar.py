from waypoint_ingest.curriculum import load_objectives
from waypoint_ingest.pstar import (
    Row,
    load_questions,
    parse_questions,
    parse_references,
    stem_text,
)


def row(*cells, bold=False):
    """A row with cells given as (x, text) pairs, or one text at x=72."""
    if isinstance(cells[0], str):
        cells = ((72.0, cells[0]),)
    return Row(page=7, y=0, bold=bold, size=11, cells=list(cells))


def choice(number, text):
    return row((100.8, f"({number}) {text}"))


# Parsing


def test_question_with_wrapped_stem_and_choice():
    drafts = parse_questions(
        [
            row("1.0 COLLISION AVOIDANCE", bold=True),
            row("1.07 When two aircraft are converging at the same"),
            row((102.0, "altitude,")),
            choice(1, "the one on the left has"),
            row((126.0, "the right of way.")),
            choice(2, "b."),
            choice(3, "c."),
            choice(4, "d."),
        ]
    )
    assert len(drafts) == 1
    assert drafts[0].number == "1.07"
    assert stem_text(drafts[0].stem) == (
        "When two aircraft are converging at the same altitude,"
    )
    assert drafts[0].choices[0] == ["the one on the left has the right of way."]


def test_table_choices_keep_their_columns():
    drafts = parse_questions(
        [
            row("2.02 A steady red light means"),
            row((142.2, "in flight"), (347.5, "on the ground")),
            row(
                (118.2, "(1)"),
                (143.4, "give way and"),
                (347.5, "stop."),
            ),
            row((143.4, "continue circling;")),
        ]
    )
    assert drafts[0].choices == [["give way and continue circling;", "stop."]]


def test_question_number_with_trailing_dot():
    drafts = parse_questions([row("3.21. A departing flight will remain until")])
    assert drafts[0].number == "3.21"


def test_lettered_items_and_sentences_start_new_lines():
    lines = [
        "Which documents? Items A, B and",
        "A. Flight Authority.",
        "B. Registration.",
    ]
    assert stem_text(lines) == (
        "Which documents? Items A, B and\nA. Flight Authority.\nB. Registration."
    )


def reference(*cells):
    return Row(page=50, y=0, bold=False, size=12, cells=list(cells))


def test_references_follow_their_question_number():
    references = parse_references(
        [
            reference((72.0, "9.07 CARs 602.70 – Flight Plans, Interpretation,")),
            reference((126.0, "TC AIM-RAC– Filing")),
            reference(
                (72.0, "9.08 CARs 602.77 – Requirement to file an Arrival Report")
            ),
        ]
    )
    assert references == {
        "9.07": ["CARs 602.70 – Flight Plans, Interpretation", "TC AIM-RAC – Filing"],
        "9.08": ["CARs 602.77 – Requirement to file an Arrival Report"],
    }


# Repository file


def test_repository_questions_match_tp11919():
    questions = load_questions()
    assert len(questions) == 185  # 186 in the guide; 7.07 was withdrawn
    assert len({q.id for q in questions}) == len(questions)
    assert "pstar-7.07" not in {q.id for q in questions}


def test_every_question_has_four_choices_and_one_answer():
    for question in load_questions():
        assert len(question.choices) == 4, question.number
        assert all(question.choices), question.number
        assert question.answer_index in range(4), question.number


def test_every_question_maps_to_a_pstar_objective():
    objective_ids = {o.id for o in load_objectives() if o.exam == "PSTAR"}
    assert {q.objective_id for q in load_questions()} == objective_ids


def test_every_question_has_its_tp11919_references():
    questions = {q.number: q for q in load_questions()}
    assert all(q.references for q in questions.values())
    assert questions["1.01"].references == [
        "TC AIM-RAC – Collision Avoidance – Right of Way",
        "CARs 602.19 – Right of Way",
    ]
    assert questions["9.08"].references == [
        "CARs 602.77 – Requirement to file an Arrival Report",
        "TC AIM-RAC – Closing a Flight Plan",
    ]
    assert questions["3.18"].references[-1] == "RTORC – Distress Communications"
