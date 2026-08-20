from pathlib import Path

from extract_frames import FlattenResult
from extract_frames.flatten import flatten_images


def write_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"image")


def test_flatten_images_moves_nested_images_into_root_folder(tmp_path: Path) -> None:
    root_dir = tmp_path / "frames"
    write_image(root_dir / "session-a" / "frame_000001.jpg")
    write_image(root_dir / "session-a" / "frame_000002.jpeg")
    write_image(root_dir / "session-b" / "nested" / "frame_000003.png")

    result = flatten_images(root_dir)

    assert result.images_moved == 3
    assert result.collisions_renamed == 0
    assert sorted(path.name for path in root_dir.iterdir() if path.is_file()) == [
        "session-a_frame_000001.jpg",
        "session-a_frame_000002.jpeg",
        "session-b_nested_frame_000003.png",
    ]
    assert not (root_dir / "session-a").exists()
    assert not (root_dir / "session-b").exists()


def test_flatten_images_leaves_non_image_files_in_place(tmp_path: Path) -> None:
    root_dir = tmp_path / "frames"
    notes_path = root_dir / "session-a" / "notes.txt"
    notes_path.parent.mkdir(parents=True)
    notes_path.write_text("not an image", encoding="utf-8")

    result = flatten_images(root_dir)

    assert result.images_moved == 0
    assert notes_path.is_file()


def test_flatten_images_preserves_existing_root_images_and_renames_collisions(
    tmp_path: Path,
) -> None:
    root_dir = tmp_path / "frames"
    write_image(root_dir / "frame_000001.jpg")
    write_image(root_dir / "video-a" / "frame_000001.jpg")
    write_image(root_dir / "video-a_frame_000001.jpg")

    result = flatten_images(root_dir)

    assert result.images_moved == 1
    assert result.collisions_renamed == 1
    assert (root_dir / "frame_000001.jpg").is_file()
    assert (root_dir / "video-a_frame_000001.jpg").is_file()
    assert (root_dir / "video-a_frame_000001_001.jpg").is_file()


def test_flatten_images_reports_zero_when_no_nested_images_exist(tmp_path: Path) -> None:
    root_dir = tmp_path / "frames"
    root_dir.mkdir()
    (root_dir / "notes.txt").write_text("not an image", encoding="utf-8")

    result = flatten_images(root_dir)

    assert result.images_moved == 0
    assert result.collisions_renamed == 0


def test_flatten_result_is_exported_for_standalone_use() -> None:
    assert FlattenResult.__name__ == "FlattenResult"
