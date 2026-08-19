# Project Plan: Extract Frames CLI

Build a Python command-line application named `extract-frames`. The tool recursively finds `.mp4` and `.MP4` videos inside a user-provided directory, extracts a user-defined percentage of frames from each video at the original resolution, and saves the images into a clean output directory ready for dataset labelling.

## Non-Negotiable Requirements

1. Use `uv` only for dependency management, installation, running, locking, and project commands.
2. Do not use or recommend `pip` anywhere in project documentation, scripts, examples, or setup steps.
3. Provide a CLI entry point named `extract-frames`.
4. Recursively scan folders and unevenly nested subfolders for `.mp4` and `.MP4` files.
5. Print the total number of discovered videos before extraction begins.
6. Extract frames at the source video's original resolution.
7. Let the user choose the extraction percentage.
8. Select frames at regular intervals across each full video.
9. Save extracted frames into a new labelling-ready directory.
10. Show console progress bars while scanning and extracting.

## Recommended Dependencies

Runtime dependencies:

- `typer`: CLI argument parsing, validation, help text, and command structure.
- `rich`: progress bars, readable status messages, warnings, and summary output.
- `opencv-python`: video metadata, frame seeking, frame reading, and image writing.

Development dependencies:

- `pytest`: unit and CLI tests.
- `ruff`: fast linting and formatting.

Add dependencies only with `uv`:

```bash
uv add typer rich opencv-python
uv add --dev pytest ruff
```

Run project commands only with `uv`:

```bash
uv run extract-frames --input ./videos --output ./frames --percent 10
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Project Structure

Use a `src` layout so the installed CLI behaves the same in development and packaged usage.

```text
extract-frames/
	pyproject.toml
	README.md
	PROJECT-STRUCTURE.md
	src/
		extract_frames/
			__init__.py
			__main__.py
			cli.py
			discovery.py
			extraction.py
			frame_selection.py
			output_paths.py
			progress.py
			models.py
	tests/
		test_discovery.py
		test_frame_selection.py
		test_output_paths.py
		test_cli.py
```

## Package Configuration

`pyproject.toml` should define:

- Project name: `extract-frames`.
- Package import name: `extract_frames`.
- Python version: `>=3.11`.
- CLI script entry point: `extract-frames = "extract_frames.cli:app"`.
- Runtime dependencies managed by `uv`.
- Development dependencies managed by `uv`.
- Ruff configuration for linting and formatting.
- Pytest configuration with `tests` as the test path.

## Module Responsibilities

### `cli.py`

Owns the Typer application and user-facing CLI contract.

Responsibilities:

- Parse `--input`, `--output`, and `--percent` options.
- Validate that the input directory exists.
- Validate that `percent` is greater than `0` and less than or equal to `100`.
- Create the output directory if needed.
- Print the discovered video count.
- Coordinate discovery, extraction, progress reporting, and final summary.
- Exit with a non-zero status code for invalid input, no videos found, or complete extraction failure.

Recommended command:

```bash
uv run extract-frames --input ./videos --output ./frames --percent 10
```

### `discovery.py`

Finds supported video files recursively.

Responsibilities:

- Use `pathlib.Path.rglob` or equivalent pathlib-based recursion.
- Match `.mp4` and `.MP4` files.
- Return stable, sorted paths for deterministic processing.
- Ignore directories and non-video files.

### `frame_selection.py`

Contains pure, easily tested frame calculation logic.

Responsibilities:

- Calculate requested frame count from `total_frames` and `percent`.
- Use predictable rounding. Recommended behavior: `round(total_frames * percent / 100)` with a minimum of `1` when `total_frames > 0`.
- Generate unique frame indexes distributed evenly across the full frame range.
- Avoid duplicate frame indexes caused by rounding.
- Never return indexes outside `0` to `total_frames - 1`.

Example:

- `total_frames = 1000`
- `percent = 10`
- requested count is approximately `100`
- selected indexes are evenly spaced from the start to the end of the video

### `extraction.py`

Reads videos and writes extracted frames.

Responsibilities:

- Open videos with OpenCV.
- Read `CAP_PROP_FRAME_COUNT` to determine total frames.
- Seek to selected frame indexes.
- Save frames without resizing so original resolution is preserved.
- Continue processing other videos if one video is unreadable or corrupt.
- Return structured extraction results for summaries and tests.

### `output_paths.py`

Creates deterministic output locations and prevents filename collisions.

Responsibilities:

- Create a per-video output folder derived from the video's relative path.
- Sanitize path parts for Windows-safe directory names.
- Avoid collisions when different folders contain videos with the same filename.
- Generate zero-padded frame names such as `frame_000001.jpg`.

Recommended output shape:

```text
frames/
	camera-a_clip-001/
		frame_000001.jpg
		frame_000002.jpg
	nested_session-camera-a_clip-001/
		frame_000001.jpg
		frame_000002.jpg
```

### `progress.py`

Centralizes Rich console and progress-bar helpers.

Responsibilities:

- Provide scan progress when practical.
- Provide overall video extraction progress.
- Provide per-video frame extraction progress for longer videos.
- Keep console output readable on Windows terminals.

### `models.py`

Defines small dataclasses or typed structures shared across modules.

Suggested models:

- `VideoInfo`: source path, relative path, output directory.
- `ExtractionResult`: source path, frames requested, frames written, success flag, warning message.

## CLI Validation Rules

The CLI should fail early with a clear message when:

- The input path does not exist.
- The input path is not a directory.
- The output path exists but is not a directory.
- `percent <= 0`.
- `percent > 100`.
- No supported videos are discovered.

The CLI should continue with a warning when:

- A specific video cannot be opened.
- A video reports zero frames.
- A selected frame cannot be read.
- A frame image cannot be written.

## Frame Extraction Rules

For each video:

1. Get `total_frames` from OpenCV.
2. Compute `requested_frames = round(total_frames * percent / 100)`.
3. Clamp requested frames to at least `1` and no more than `total_frames`.
4. Generate evenly distributed indexes across `0` to `total_frames - 1`.
5. Seek to each selected frame index.
6. Write the frame to disk as an image without resizing.

Use `.jpg` as the default image format unless a future CLI option adds format selection.

## Testing Plan

Prioritize pure unit tests first, then add CLI tests.

Required tests:

- Recursive discovery finds `.mp4` and `.MP4` files in nested folders.
- Discovery ignores non-video files.
- Frame count calculation handles common percentages.
- Frame index selection is evenly distributed, unique, sorted, and in range.
- Frame selection clamps correctly for very small videos and very low percentages.
- Output path generation avoids collisions for same-named videos in different folders.
- CLI rejects missing input directories.
- CLI rejects invalid percentages.
- CLI exits non-zero when no videos are found.

Optional integration test:

- Generate a tiny synthetic video with OpenCV inside a temporary directory, run extraction, and assert that expected image files are written.

## Implementation Milestones

1. Initialize the `uv` Python project and package metadata.
2. Add runtime and development dependencies with `uv`.
3. Create the `src/extract_frames` package and CLI entry point.
4. Implement recursive video discovery.
5. Implement pure frame percentage and index-selection logic.
6. Implement output path generation.
7. Implement OpenCV frame extraction.
8. Add Rich progress bars and console summaries.
9. Add focused tests for discovery, frame selection, output paths, and CLI validation.
10. Update `README.md` with UV-only usage examples.

## Expected User Workflow

```bash
uv sync
uv run extract-frames --input ./raw-videos --output ./dataset-frames --percent 10
uv run pytest
```

The final output should be a deterministic image dataset folder that can be opened directly in an image labelling tool.
