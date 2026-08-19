from pathlib import Path

from typer.testing import CliRunner

from extract_frames.cli import app

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
