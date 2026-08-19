# extract-frames

`extract-frames` is a Python CLI for building image-labelling datasets from video folders. It recursively finds `.mp4` and `.MP4` files, extracts a user-selected percentage of frames from each video at the original resolution, and writes the images to a deterministic output folder.

## Requirements

- Python `>=3.12`
- `uv`

This project uses `uv` only for dependency management and command execution.

## Setup

Install and sync the project dependencies:

```bash
uv sync
```

## Usage

Run the CLI with an input directory, output directory, and frame percentage:

```bash
uv run extract-frames --input ./raw-videos --output ./dataset-frames --percent 10
```

This command:

- Recursively scans `./raw-videos` for `.mp4` and `.MP4` files.
- Prints the number of discovered videos.
- Extracts approximately `10%` of frames from each video.
- Preserves the original frame resolution.
- Saves frames as `.jpg` files under `./dataset-frames`.
- Shows console progress while scanning files, processing videos, and extracting frames.

## Output Layout

Frames are saved into one folder per source video. Folder names are derived from each video's relative path so same-named videos in different folders do not collide.

Example:

```text
dataset-frames/
	session-a_clip/
		frame_000001.jpg
		frame_000002.jpg
	session-b_clip/
		frame_000001.jpg
		frame_000002.jpg
```

Frame filenames are zero-padded so they sort naturally in labelling tools and file explorers.

## CLI Options

```text
--input    Directory to scan for videos.
--output   Directory where extracted frames are saved.
--percent  Percentage of frames to extract from each video. Must be > 0 and <= 100.
```

Show help:

```bash
uv run extract-frames --help
```

## Validation And Errors

The CLI exits with a non-zero status code when:

- The input path does not exist.
- The input path is not a directory.
- The output path exists but is not a directory.
- `--percent` is outside the valid range.
- No supported videos are found.
- No frames can be extracted from any discovered video.

If one video cannot be opened or processed, the CLI prints a warning and continues with the remaining videos.

## Development

Run tests:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
```

Format code:

```bash
uv run ruff format .
```