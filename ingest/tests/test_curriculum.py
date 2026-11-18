import pytest
import yaml

from waypoint_ingest.curriculum import (
    Objective,
    OutlineParser,
    finish_flight_test,
    load_objectives,
    parse_ppaer_line,
)
from waypoint_ingest.pdf_lines import Line


def line(text, size=12, bold=False, bullet=False, x=94.0):
    return Line(
        page=1, column=0, x=x, y=0, text=text, size=size, bold=bold, bullet=bullet
    )


def parse(*lines):
    parser = OutlineParser("PPAER", "tp12880", "ppaer")
    parser.subject = "navigation"
    for each in lines:
        parse_ppaer_line(parser, each)
    return parser


def objective(id, detail=None):
    return Objective(
        id=id,
        exam="FLIGHT_TEST",
        subject="flight-test",
        area="Flight Test Items",
        topic="Ex. 18",
        text=id,
        detail=detail,
        source="tp13723",
        page=1,
    )


# Repository file


def test_repository_objectives_are_valid():
    objectives = load_objectives()
    assert {o.exam for o in objectives} == {"PSTAR", "PPAER", "FLIGHT_TEST"}
    ppaer_subjects = {o.subject for o in objectives if o.exam == "PPAER"}
    assert ppaer_subjects == {"air-law", "navigation", "meteorology", "aeronautics"}
    assert all(o.text and o.source and o.page for o in objectives)


def test_duplicate_objective_ids_are_rejected(tmp_path):
    item = objective("flight-test.ex09").model_dump()
    path = tmp_path / "objectives.yaml"
    path.write_text(yaml.safe_dump([item, item]))
    with pytest.raises(ValueError, match="duplicate"):
        load_objectives(path)


# TP 12880 outline parsing


def test_numbered_items_under_a_topic():
    parser = parse(
        line("Definitions", size=14, bold=True),
        line("1 Meridian"),
        line("2 Prime Meridian", bullet=True),
    )
    first, second = parser.objectives
    assert (first.topic, first.text, first.essential) == (
        "Definitions",
        "Meridian",
        False,
    )
    assert (second.text, second.essential) == ("Prime Meridian", True)
    assert [o.id for o in parser.objectives] == [
        "ppaer.navigation.001",
        "ppaer.navigation.002",
    ]
    assert parser.problems == []


def test_heading_wrapped_over_two_lines_is_joined():
    parser = parse(
        line("Meteorological Aspects of", size=14, bold=True),
        line("Altimetry", size=14, bold=True),
        line("1 Altimeter settings"),
    )
    assert parser.objectives[0].topic == "Meteorological Aspects of Altimetry"


def test_indented_line_continues_the_item():
    parser = parse(
        line("Maps", size=14, bold=True),
        line("7 Locating position by latitude and", x=94),
        line("longitude", x=107),
    )
    assert parser.objectives[0].text == "Locating position by latitude and longitude"


def test_numbering_gap_is_reported():
    parser = parse(line("Wind", size=14, bold=True), line("1 Shear"), line("3 Gusts"))
    assert len(parser.problems) == 1
    assert "expected 2, got 3" in parser.problems[0]


def test_car_sections_get_references_and_subheadings_do_not_chain():
    parser = parse(
        line("602 – Operating and Flight Rules"),
        line("602.01.1 Reckless or Negligent Operation of Aircraft"),
        line("Visual Flight Rules", x=72),
        line("602.114 Minimum Visual Meteorological Conditions"),
        line("Radiocommunications", x=72),
        line("602.136 Radio Communication"),
    )
    reckless, vmc, radio = parser.objectives
    assert reckless.ref == "CAR 602.01.1"
    assert vmc.topic == "CAR 602 Operating and Flight Rules (Visual Flight Rules)"
    assert radio.topic == "CAR 602 Operating and Flight Rules (Radiocommunications)"


def test_aim_reference_in_topic_note_applies_to_items():
    parser = parse(
        line("Air Traffic Services and Procedures", size=14, bold=True),
        line("Refer to TC-AIM RAC 1.0 and 4.0.", x=72),
        line("1 ATC clearances"),
    )
    assert parser.objectives[0].ref == "TC AIM RAC 1.0 and 4.0"


# TP 13723 items


def test_parent_item_is_replaced_by_sub_items_that_inherit_its_aim():
    exercise = objective("flight-test.ex18", detail=None)
    items = [
        objective("flight-test.ex18a", "Land normally"),
        objective("flight-test.ex18b", "Land short or soft"),
        objective("flight-test.ex18b1"),
        objective("flight-test.ex18b2"),
    ]
    leaves, _ = finish_flight_test(items, [exercise])
    assert [o.id for o in leaves] == [
        "flight-test.ex18a",
        "flight-test.ex18b1",
        "flight-test.ex18b2",
    ]
    assert leaves[1].detail == "Land short or soft"


def test_items_without_aim_inherit_the_exercise_aim():
    exercise = objective("flight-test.ex22", "Forced landing")
    items = [objective("flight-test.ex22a"), objective("flight-test.ex22b")]
    leaves, _ = finish_flight_test(items, [exercise])
    assert [o.detail for o in leaves] == ["Forced landing", "Forced landing"]
