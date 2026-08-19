from pathlib import Path

from extract_frames.output_paths import build_video_output_dir, frame_output_path


def test_build_video_output_dir_uses_relative_path_to_avoid_collisions(tmp_path: Path) -> None:
    input_dir = tmp_path / "videos"
    output_dir = tmp_path / "frames"
    first_video = input_dir / "session-a" / "clip.mp4"
    second_video = input_dir / "session-b" / "clip.mp4"

    first_output_dir = build_video_output_dir(output_dir, input_dir, first_video)
    second_output_dir = build_video_output_dir(output_dir, input_dir, second_video)

    assert first_output_dir != second_output_dir
    assert first_output_dir.parent == output_dir
    assert second_output_dir.parent == output_dir
    assert "session-a" in first_output_dir.name
    assert "session-b" in second_output_dir.name
    assert "clip" in first_output_dir.name
    assert "clip" in second_output_dir.name


def test_build_video_output_dir_sanitizes_windows_reserved_filename_characters(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "videos"
    output_dir = tmp_path / "frames"
    video_path = input_dir / "camera:one" / "clip name.mp4"

    video_output_dir = build_video_output_dir(output_dir, input_dir, video_path)

    assert video_output_dir.parent == output_dir
    assert ":" not in video_output_dir.name
    assert "camera" in video_output_dir.name
    assert "clip-name" in video_output_dir.name


def test_frame_output_path_uses_zero_padded_sortable_jpg_names(tmp_path: Path) -> None:
    video_output_dir = tmp_path / "frames" / "clip"

    assert frame_output_path(video_output_dir, frame_number=1).name == "frame_000001.jpg"
    assert frame_output_path(video_output_dir, frame_number=42).name == "frame_000042.jpg"
    assert frame_output_path(video_output_dir, frame_number=1000).name == "frame_001000.jpg"
