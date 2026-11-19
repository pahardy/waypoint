from datetime import date

import pytest
import yaml
from test_load import CHUNKS, META, SOURCE, StubEmbed

from waypoint_ingest.evaluate import (
    Question,
    evaluate,
    first_rank,
    load_questions,
    mean_reciprocal_rank,
    recall_at,
    report,
    report_path,
    scores,
)
from waypoint_ingest.load import Hit, embedding_text, load_source


def hit(section_ref, document_id="aim"):
    return Hit(f"{document_id}:{section_ref}:0", document_id, section_ref, "1", 0.5, "")


def question(text, expected, subject="air-law"):
    return Question(
        id=text, exam="PPAER", subject=subject, question=text, expected=expected
    )


# Metrics


def test_first_rank_is_one_based():
    hits = [hit("RAC 1.1"), hit("RAC 1.2"), hit("RAC 1.3")]
    assert first_rank(hits, ["aim:RAC 1.2"]) == 2


def test_first_rank_takes_the_earliest_expected_section():
    hits = [hit("RAC 1.1"), hit("RAC 1.2"), hit("RAC 1.3")]
    assert first_rank(hits, ["aim:RAC 1.3", "aim:RAC 1.2"]) == 2


def test_first_rank_matches_the_source_as_well_as_the_section():
    assert first_rank([hit("RAC 1.1", document_id="other")], ["aim:RAC 1.1"]) is None


def test_recall_counts_hits_within_k():
    assert recall_at([1, 5, 6, None], k=5) == 0.5


def test_mrr_averages_reciprocal_ranks_and_scores_misses_as_zero():
    assert mean_reciprocal_rank([1, 2, None, 4], k=10) == pytest.approx(
        (1 + 0.5 + 0 + 0.25) / 4
    )


def test_mrr_ignores_ranks_beyond_k():
    assert mean_reciprocal_rank([11], k=10) == 0


# Eval set


def test_repository_eval_set_is_valid():
    questions = load_questions()
    assert len(questions) >= 60
    subjects = {q.subject for q in questions}
    assert subjects == {
        "pstar",
        "air-law",
        "navigation",
        "meteorology",
        "aeronautics",
        "exam",
    }
    assert all(q.expected and q.question for q in questions)
    assert all(":" in e for q in questions for e in q.expected)


def test_duplicate_question_ids_are_rejected(tmp_path):
    item = question("q", ["aim:RAC 1.1"]).model_dump()
    path = tmp_path / "retrieval.yaml"
    path.write_text(yaml.safe_dump([item, item]))
    with pytest.raises(ValueError, match="duplicate"):
        load_questions(path)


# Against the database


def test_evaluate_ranks_the_expected_section(conn):
    load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub")
    exact = question(embedding_text(CHUNKS[1]), ["aim:RAC 1.2"])
    outcomes = evaluate(conn, [exact], StubEmbed())
    assert outcomes[0].rank == 1
    assert scores(outcomes) == (1.0, 1.0)


def test_evaluate_rejects_sections_that_are_not_loaded(conn):
    load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub")
    with pytest.raises(ValueError, match="aim:RAC 9.9"):
        evaluate(conn, [question("q", ["aim:RAC 9.9"])], StubEmbed())


def test_report_lists_scores_by_subject_and_every_miss(conn):
    load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub")
    found = question(embedding_text(CHUNKS[0]), ["aim:RAC 1.1"], subject="pstar")
    missed = question("unrelated words", ["aim:RAC 1.1"], subject="air-law")
    outcomes = evaluate(conn, [found, missed], StubEmbed())
    outcomes[1].rank = None
    text = report(outcomes, ["aim"], chunk_count=2, run_on=date(2026, 11, 19))
    assert "- Sources: aim (2 chunks)" in text
    assert "| pstar | 1 | 1.00 | 1.00 |" in text
    assert "| air-law | 1 | 0.00 | 0.00 |" in text
    assert "**unrelated words** (not in top 10)" in text


def test_report_path_names_the_date_and_sources():
    path = report_path(["cars", "tc-aim"], date(2026, 11, 19))
    assert path.name == "retrieval-2026-11-19-cars-tc-aim.md"
