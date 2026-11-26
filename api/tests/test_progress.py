from waypoint_api.progress import (
    ObjectiveCounts,
    mastery,
    percent,
    recommend,
    subjects,
    weak,
)


def counts(objective_id, correct, seen, subject="air-law", confidence=None):
    return ObjectiveCounts(
        objective_id, subject, f"Topic {objective_id}", correct, seen, confidence
    )


def test_an_unseen_objective_has_no_mastery():
    assert mastery(0, 0) is None


def test_all_correct_is_full_mastery():
    assert mastery(5, 5) == 1.0


def test_all_wrong_is_no_mastery():
    assert mastery(0, 5) == 0.0


def test_percent_rounds_down_below_the_mark():
    assert percent(599, 1000) == 59
    assert percent(0, 0) is None


def test_seen_four_times_is_not_weak():
    assert weak([counts("a", 0, 4)], 60) == []


def test_at_the_mark_exactly_is_not_weak():
    assert weak([counts("a", 3, 5)], 60) == []


def test_below_the_mark_is_weak_with_the_numbers():
    (found,) = weak([counts("a", 3, 6)], 90)
    assert (found.correct, found.seen, found.percent) == (3, 6, 50)
    assert found.reason == "3 of 6 correct (50%), below the 90% pass mark"


def test_weakest_first_and_ties_by_id():
    found = weak([counts("c", 2, 5), counts("b", 1, 5), counts("a", 2, 5)], 60)
    assert [o.objective_id for o in found] == ["b", "a", "c"]


def test_subjects_total_their_objectives_in_order():
    found = subjects(
        [
            counts("a", 1, 2, "navigation"),
            counts("b", 3, 4, "air-law"),
            counts("c", 0, 0, "navigation"),
        ]
    )
    assert [(s.subject, s.correct, s.seen, s.percent) for s in found] == [
        ("air-law", 3, 4, 75),
        ("navigation", 1, 2, 50),
    ]


def test_recommendations_are_the_five_weakest_in_order():
    found = weak([counts(f"o{n}", n, 10) for n in range(7)], 60)
    recommended = recommend(found)
    assert [o.objective_id for o in recommended] == ["o0", "o1", "o2", "o3", "o4"]
    assert all(o.reason for o in recommended)


def test_fewer_weak_objectives_give_fewer_recommendations():
    found = weak([counts("a", 1, 5), counts("b", 5, 5), counts("c", 0, 4)], 60)
    assert [o.objective_id for o in recommend(found)] == ["a"]


def test_a_low_self_rating_is_flagged_whatever_the_counts():
    (found,) = weak([counts("a", 4, 4, confidence="low")], 90)
    assert found.reason == "4 of 4 correct (100%); rated low confidence"


def test_medium_or_high_ratings_change_nothing():
    rated = [
        counts("a", 4, 4, confidence="medium"),
        counts("b", 5, 5, confidence="high"),
    ]
    assert weak(rated, 90) == []


def test_low_and_below_the_mark_gives_both_reasons():
    (found,) = weak([counts("a", 2, 5, confidence="low")], 90)
    assert (
        found.reason
        == "2 of 5 correct (40%), below the 90% pass mark; rated low confidence"
    )


def test_a_low_rating_without_answers_has_its_own_reason():
    (found,) = weak([counts("a", 0, 0, confidence="low")], 90)
    assert (found.percent, found.reason) == (None, "Rated low confidence")


def test_low_ratings_keep_the_mastery_order():
    found = weak([counts("a", 4, 4, confidence="low"), counts("b", 1, 5)], 90)
    assert [o.objective_id for o in found] == ["b", "a"]
