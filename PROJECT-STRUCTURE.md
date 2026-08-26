# Project Plan: Extract Frames CLI

Build a Python command-line application named `extract-frames`. The tool recursively finds `.mp4` and `.MP4` videos inside a user-provided directory, extracts a user-defined percentage of frames from each video at the original resolution, and saves the images into a clean output directory ready for dataset labelling. The project should also include focused image-directory utilities that help users inspect, group, and clean extracted frames after manual edits.

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
11. Provide post-extraction image utilities for grouping and removing perceptually similar images.
12. Keep perceptual-hash grouping and removal logic test-driven, deterministic, and reusable outside the CLI.

## Recommended Dependencies

Runtime dependencies:

- `typer`: CLI argument parsing, validation, help text, and command structure.
- `rich`: progress bars, readable status messages, warnings, and summary output.
- `opencv-python`: video metadata, frame seeking, frame reading, and image writing.
- `imagehash`: perceptual image hashing based on the Johannes Buchner Python ImageHash implementation.
- `pillow`: image loading used by perceptual hashing utilities.

Development dependencies:

- `pytest`: unit and CLI tests.
- `ruff`: fast linting and formatting.

Add dependencies only with `uv`:

```bash
uv add typer rich opencv-python imagehash pillow
uv add --dev pytest ruff
```

Run project commands only with `uv`:

```bash
uv run extract-frames --input ./videos --output ./frames --percent 10
uv run extract-frames group-similar --input ./frames --threshold 5 --report ./similar-groups.json
uv run extract-frames remove-similar --input ./frames --threshold 5 --dry-run
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
			image_discovery.py
			perceptual_hashing.py
			similarity_groups.py
			image_cleanup.py
			progress.py
			models.py
	tests/
		test_discovery.py
		test_frame_selection.py
		test_output_paths.py
		test_image_discovery.py
		test_perceptual_hashing.py
		test_similarity_groups.py
		test_image_cleanup.py
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
- Expose post-extraction utility commands for perceptual-hash grouping and duplicate removal.
- Exit with a non-zero status code for invalid input, no videos found, or complete extraction failure.

Recommended command:

```bash
uv run extract-frames --input ./videos --output ./frames --percent 10
uv run extract-frames group-similar --input ./frames --threshold 5 --report ./similar-groups.json
uv run extract-frames remove-similar --input ./frames --threshold 5 --dry-run
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

### `image_discovery.py`

Finds extracted image files recursively for post-processing utilities.

Responsibilities:

- Use `pathlib` recursion to scan an image directory.
- Match supported image extensions such as `.jpg`, `.jpeg`, and `.png`, including uppercase variants.
- Return stable, sorted paths for deterministic grouping and deletion behavior.
- Ignore directories, unsupported files, generated reports, and hidden housekeeping files.

### `perceptual_hashing.py`

Computes perceptual hashes for extracted images.

Responsibilities:

- Use the `imagehash` package, which implements Johannes Buchner's Python perceptual image hashing algorithms.
- Default to a well-established perceptual hash such as `imagehash.phash` unless tests or requirements justify another algorithm.
- Load images with `PIL.Image` without modifying or rewriting the source files.
- Return structured hash records containing the image path and hash value.
- Continue processing other images when a single image is unreadable, while returning a warning for the failed image.
- Keep the hashing function pure enough to test with temporary image fixtures.

### `similarity_groups.py`

Groups perceptually similar images from hash records.

Responsibilities:

- Compare perceptual hashes using Hamming distance.
- Accept a configurable similarity threshold, where lower values are stricter and `0` means identical hashes only.
- Produce deterministic groups of similar images sorted by path.
- Avoid duplicate group membership where possible by using a clear grouping strategy, such as connected components over hash-distance matches.
- Return single-image groups only when explicitly requested; default reports should focus on groups with at least two similar images.
- Preserve enough metadata for reports, summaries, and tests, including group id, image paths, representative image, and pairwise distances when practical.

### `image_cleanup.py`

Removes perceptually similar images after grouping.

Responsibilities:

- Accept similarity groups produced by `similarity_groups.py`.
- Keep one deterministic representative image per group by default, such as the lexicographically first path.
- Remove only non-representative images from each group.
- Support a dry-run mode that reports what would be deleted without modifying files.
- Return structured cleanup results listing kept images, removed images, skipped images, and warnings.
- Never delete files outside the user-provided image directory.

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
- `ImageHashRecord`: image path, perceptual hash value, success flag, warning message.
- `SimilarityGroup`: group id, representative image path, similar image paths, optional pairwise distances.
- `CleanupResult`: kept images, removed images, skipped images, dry-run flag, warning messages.

## CLI Validation Rules

The CLI should fail early with a clear message when:

- The input path does not exist.
- The input path is not a directory.
- The output path exists but is not a directory.
- `percent <= 0`.
- `percent > 100`.
- No supported videos are discovered.
- The image utility input path does not exist.
- The image utility input path is not a directory.
- The perceptual-hash threshold is less than `0`.
- No supported images are discovered for a post-extraction utility command.

The CLI should continue with a warning when:

- A specific video cannot be opened.
- A video reports zero frames.
- A selected frame cannot be read.
- A frame image cannot be written.
- A specific image cannot be opened or hashed.
- A similar image selected for removal no longer exists.

## Post-Extraction Image Utility Rules

The image utilities operate on image directories after extraction and after any user edits to the resulting dataset folder.

### Perceptual Similarity Grouping

For each image directory:

1. Recursively discover supported images in deterministic path order.
2. Open each image with Pillow and compute a perceptual hash with `imagehash`.
3. Compare hashes using Hamming distance.
4. Treat two images as similar when their distance is less than or equal to the configured threshold.
5. Build deterministic groups of related images.
6. Write an optional machine-readable report, such as JSON, containing the grouped image paths and distances.
7. Print a readable summary showing total images scanned, images hashed, groups found, and images with warnings.

Recommended command:

```bash
uv run extract-frames group-similar --input ./dataset-frames --threshold 5 --report ./similar-groups.json
```

### Perceptual Similarity Removal

For each image directory:

1. Reuse the same discovery, hashing, and grouping behavior as `group-similar`.
2. Keep one deterministic representative image per group.
3. Remove only the remaining images in each group.
4. Default to `--dry-run` behavior for first-time usage if practical, or strongly expose `--dry-run` in help text.
5. Print a readable summary showing images kept, images removed, images skipped, and warnings.
6. Return a non-zero exit code only when the command cannot complete at all, not when individual unreadable images are skipped with warnings.

Recommended command:

```bash
uv run extract-frames remove-similar --input ./dataset-frames --threshold 5 --dry-run
```

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
- Image discovery finds supported images recursively and ignores unsupported files.
- Perceptual hashing returns stable hash records for generated test images.
- Similarity grouping groups identical or near-identical images under a configured threshold.
- Similarity grouping leaves distinct images ungrouped when their hash distance exceeds the threshold.
- Cleanup keeps one deterministic representative per group.
- Cleanup dry-run reports removals without deleting files.
- Cleanup never removes files outside the requested image directory.
- CLI rejects invalid image utility inputs and invalid thresholds.

Optional integration test:

- Generate a tiny synthetic video with OpenCV inside a temporary directory, run extraction, and assert that expected image files are written.
- Generate a small image directory with duplicate and distinct images, run `group-similar`, and assert that the report contains the expected group.
- Generate a small image directory with duplicate images, run `remove-similar --dry-run`, and assert that no files are deleted.

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
10. Add image discovery tests and implementation for extracted image directories.
11. Add perceptual hashing tests and implementation using `imagehash` and Pillow.
12. Add similarity grouping tests and implementation with configurable Hamming-distance thresholds.
13. Add cleanup tests and implementation for dry-run and deletion behavior.
14. Add CLI tests and commands for `group-similar` and `remove-similar`.
15. Update `README.md` with UV-only usage examples for extraction, grouping, and removal.

## Expected User Workflow

```bash
uv sync
uv run extract-frames --input ./raw-videos --output ./dataset-frames --percent 10
uv run extract-frames group-similar --input ./dataset-frames --threshold 5 --report ./similar-groups.json
uv run extract-frames remove-similar --input ./dataset-frames --threshold 5 --dry-run
uv run pytest
```

The final output should be a deterministic image dataset folder that can be opened directly in an image labelling tool, plus optional reports and cleanup utilities for reducing perceptually similar frames after extraction or manual review.
