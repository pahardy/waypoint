from waypoint_api.progress import mastery


def test_an_unseen_objective_has_no_mastery():
    assert mastery(0, 0) is None


def test_all_correct_is_full_mastery():
    assert mastery(5, 5) == 1.0


def test_all_wrong_is_no_mastery():
    assert mastery(0, 5) == 0.0
