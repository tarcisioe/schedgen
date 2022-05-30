from schedgen.cli import allocate_y_and_heights


def test_allocate_y_and_heights_one_entry():
    """allocate_y_and_heights should use all space available when there is plenty."""
    result = allocate_y_and_heights(
        total_height=500,
        max_entry_height=100,
        n_entries=1,
        min_spacing=100
    )

    assert list(result) == [
        (200, 100),
    ]


def test_allocate_y_and_heights_boundary_case():
    """allocate_y_and_heights should leave space before and after blocks if possible."""
    result = allocate_y_and_heights(
        total_height=500,
        max_entry_height=100,
        n_entries=3,
        min_spacing=100
    )

    assert list(result) == [
        (50, 100),
        (200, 100),
        (350, 100),
    ]


def test_allocate_y_and_heights_not_enough_space_available():
    """allocate_y_and_heights should leave space before and after blocks if possible."""
    result = allocate_y_and_heights(
        total_height=500,
        max_entry_height=100,
        n_entries=3,
        min_spacing=130
    )

    assert list(result) == [
        (0, 80),
        (210, 80),
        (420, 80),
    ]
