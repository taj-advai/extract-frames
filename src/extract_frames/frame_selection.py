def calculate_requested_frame_count(total_frames: int, percent: float) -> int:
    if total_frames <= 0:
        return 0

    requested_frames = round(total_frames * percent / 100)
    return min(total_frames, max(1, requested_frames))


def select_frame_indexes(total_frames: int, percent: float) -> list[int]:
    requested_frames = calculate_requested_frame_count(total_frames, percent)
    if requested_frames == 0:
        return []
    if requested_frames == 1:
        return [0]

    last_frame_index = total_frames - 1
    return [
        round(frame_number * last_frame_index / (requested_frames - 1))
        for frame_number in range(requested_frames)
    ]
