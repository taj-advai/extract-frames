from extract_frames.frame_selection import calculate_requested_frame_count, select_frame_indexes


def test_calculate_requested_frame_count_uses_percentage_with_bounds() -> None:
    assert calculate_requested_frame_count(total_frames=1000, percent=10) == 100
    assert calculate_requested_frame_count(total_frames=24, percent=50) == 12
    assert calculate_requested_frame_count(total_frames=3, percent=1) == 1
    assert calculate_requested_frame_count(total_frames=0, percent=10) == 0


def test_calculate_requested_frame_count_never_exceeds_total_frames() -> None:
    assert calculate_requested_frame_count(total_frames=7, percent=100) == 7


def test_select_frame_indexes_are_sorted_unique_and_in_range() -> None:
    frame_indexes = select_frame_indexes(total_frames=1000, percent=10)

    assert len(frame_indexes) == 100
    assert frame_indexes == sorted(frame_indexes)
    assert len(frame_indexes) == len(set(frame_indexes))
    assert frame_indexes[0] == 0
    assert frame_indexes[-1] == 999
    assert all(0 <= frame_index < 1000 for frame_index in frame_indexes)


def test_select_frame_indexes_distributes_frames_across_full_video() -> None:
    assert select_frame_indexes(total_frames=10, percent=50) == [0, 2, 4, 7, 9]


def test_select_frame_indexes_clamps_low_percentages_to_one_frame() -> None:
    assert select_frame_indexes(total_frames=3, percent=1) == [0]
    assert select_frame_indexes(total_frames=1, percent=10) == [0]
    assert select_frame_indexes(total_frames=0, percent=10) == []
