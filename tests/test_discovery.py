from pathlib import Path

from extract_frames.discovery import find_videos


def touch_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def test_find_videos_recurses_and_matches_supported_mp4_cases(tmp_path: Path) -> None:
    touch_file(tmp_path / "root.MP4")
    touch_file(tmp_path / "level_one" / "clip.mp4")
    touch_file(tmp_path / "level_one" / "level_two" / "deep.MP4")
    touch_file(tmp_path / "level_one" / "ignored.mov")
    touch_file(tmp_path / "notes.txt")

    discovered_videos = find_videos(tmp_path)
    relative_paths = [
        video_path.relative_to(tmp_path).as_posix() for video_path in discovered_videos
    ]

    assert set(relative_paths) == {
        "root.MP4",
        "level_one/clip.mp4",
        "level_one/level_two/deep.MP4",
    }
    assert relative_paths == sorted(relative_paths)


def test_find_videos_returns_empty_list_when_no_supported_videos(tmp_path: Path) -> None:
    touch_file(tmp_path / "nested" / "clip.mov")
    touch_file(tmp_path / "nested" / "image.jpg")

    assert find_videos(tmp_path) == []
