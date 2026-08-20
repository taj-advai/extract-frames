from pathlib import Path

from typer.testing import CliRunner

from extract_frames import cli
from extract_frames.models import ExtractionResult

app = cli.app

runner = CliRunner()


def test_cli_rejects_missing_input_directory(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--input",
            str(tmp_path / "missing"),
            "--output",
            str(tmp_path / "frames"),
            "--percent",
            "10",
        ],
    )

    assert result.exit_code != 0
    assert "input" in result.output.lower()


def test_cli_rejects_invalid_percentages(tmp_path: Path) -> None:
    input_dir = tmp_path / "videos"
    input_dir.mkdir()

    for percent in ("0", "101"):
        result = runner.invoke(
            app,
            [
                "--input",
                str(input_dir),
                "--output",
                str(tmp_path / "frames"),
                "--percent",
                percent,
            ],
        )

        assert result.exit_code != 0
        assert "percent" in result.output.lower()


def test_cli_exits_non_zero_when_no_videos_are_found(tmp_path: Path) -> None:
    input_dir = tmp_path / "videos"
    input_dir.mkdir()
    (input_dir / "notes.txt").write_text("not a video", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "--input",
            str(input_dir),
            "--output",
            str(tmp_path / "frames"),
            "--percent",
            "10",
        ],
    )

    assert result.exit_code != 0
    assert "no" in result.output.lower()
    assert "video" in result.output.lower()


def test_cli_flatten_rejects_missing_folder(tmp_path: Path) -> None:
    result = runner.invoke(app, ["flatten", str(tmp_path / "missing")])

    assert result.exit_code != 0
    assert "folder" in result.output.lower()


def test_cli_flatten_moves_nested_images_into_root_folder(tmp_path: Path) -> None:
    root_dir = tmp_path / "frames"
    nested_image = root_dir / "video-a" / "frame_000001.jpg"
    nested_image.parent.mkdir(parents=True)
    nested_image.write_bytes(b"image")

    result = runner.invoke(app, ["flatten", str(root_dir)])

    assert result.exit_code == 0
    assert "1 image" in result.output.lower()
    assert (root_dir / "video-a_frame_000001.jpg").is_file()
    assert not nested_image.exists()


def test_cli_can_flatten_after_original_extraction_command(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_dir = tmp_path / "videos"
    output_dir = tmp_path / "frames"
    video_path = input_dir / "clip.mp4"
    video_path.parent.mkdir(parents=True)
    video_path.write_bytes(b"video")

    def fake_find_videos(input_path: Path, show_progress: bool = False) -> list[Path]:
        assert input_path == input_dir
        assert show_progress is True
        return [video_path]

    def fake_extract_video_frames(
        input_path: Path,
        output_path: Path,
        source_video: Path,
        percent: float,
    ) -> ExtractionResult:
        assert input_path == input_dir
        assert output_path == output_dir
        assert source_video == video_path
        assert percent == 10
        nested_image = output_path / "clip" / "frame_000001.jpg"
        nested_image.parent.mkdir(parents=True)
        nested_image.write_bytes(b"image")
        return ExtractionResult(video_path, 1, 1, True)

    monkeypatch.setattr(cli, "find_videos", fake_find_videos)
    monkeypatch.setattr(cli, "extract_video_frames", fake_extract_video_frames)

    result = runner.invoke(
        app,
        [
            "--input",
            str(input_dir),
            "--output",
            str(output_dir),
            "--percent",
            "10",
            "--flatten",
        ],
    )

    assert result.exit_code == 0
    assert "flattened" in result.output.lower()
    assert (output_dir / "clip_frame_000001.jpg").is_file()
    assert not (output_dir / "clip" / "frame_000001.jpg").exists()
