# extract-frames

`extract-frames` is a Python CLI for building image-labelling datasets from video folders. It recursively finds `.mp4`,`.MP4` and `.mpeg` files, extracts a user-selected percentage of frames from each video at the original resolution, and writes the images to a deterministic output folder.

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

To extract frames and then flatten the output into a single folder in one command, add `--flatten`:

```bash
uv run extract-frames --input ./raw-videos --output ./dataset-frames --percent 10 --flatten
```

This command:

- Recursively scans `./raw-videos` for `.mp4` and `.MP4` files.
- Prints the number of discovered videos.
- Extracts approximately `10%` of frames from each video.
- Preserves the original frame resolution.
- Saves frames as `.jpg` files under `./dataset-frames`.
- Shows console progress while scanning files, processing videos, and extracting frames.
- Optionally flattens the extracted images into `./dataset-frames` when `--flatten` is provided.

## Group Or Clean Similar Images

After extraction or manual edits, run perceptual hashing on an image directory to find visually similar images. Group mode copies similar images into deterministic group folders and writes a `similar-groups.json` report:

```bash
uv run extract-frames hash --input ./dataset-frames --output ./similar-frame-groups --group
```

Cleanup mode copies a cleaned version of the image directory to a new output folder while omitting non-representative similar images:

```bash
uv run extract-frames hash --input ./dataset-frames --output ./dataset-frames-cleaned --cleanup
```

Both modes accept a perceptual-hash distance threshold. Lower values are stricter; `0` only matches identical perceptual hashes:

```bash
uv run extract-frames hash --input ./dataset-frames --output ./similar-frame-groups --group --threshold 3
```

If you first created grouped output, you can later delete similar images inside those group folders while keeping the first image in each group:

```bash
uv run extract-frames cleanup-similar ./similar-frame-groups
```

The original input directory is not modified by `hash --group` or `hash --cleanup`. The standalone `cleanup-similar` command modifies the grouped output folder passed to it.

## Flatten Extracted Images

The default extraction layout stores frames in one subfolder per source video. To move all extracted images from nested folders into a single root folder, run:

```bash
uv run extract-frames flatten ./dataset-frames
```

This command:

- Recursively finds image files inside subfolders of `./dataset-frames`.
- Moves those images into `./dataset-frames`.
- Prefixes filenames with their original relative folder path to avoid collisions.
- Adds a numeric suffix when a filename still already exists.
- Removes empty subfolders after images are moved.
- Leaves non-image files in place.

Supported image extensions for flattening are `.jpg`, `.jpeg`, `.png`, `.bmp`, and `.webp`.

The same flattening logic is also available as a standalone Python function:

```python
from pathlib import Path

from extract_frames import flatten_images

result = flatten_images(Path("./dataset-frames"))
print(result.images_moved, result.collisions_renamed)
```

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

After flattening, the same output may look like this:

```text
dataset-frames/
	session-a_clip_frame_000001.jpg
	session-a_clip_frame_000002.jpg
	session-b_clip_frame_000001.jpg
	session-b_clip_frame_000002.jpg
```

## CLI Options

```text
--input    Directory to scan for videos.
--output   Directory where extracted frames are saved.
--percent  Percentage of frames to extract from each video. Must be > 0 and <= 100.
--flatten  Flatten extracted images into the output folder after extraction.
```

Show help:

```bash
uv run extract-frames --help
```

Show help for the flatten command:

```bash
uv run extract-frames flatten --help
```

Show help for perceptual hashing commands:

```bash
uv run extract-frames hash --help
uv run extract-frames cleanup-similar --help
```

## Validation And Errors

The CLI exits with a non-zero status code when:

- The input path does not exist.
- The input path is not a directory.
- The output path exists but is not a directory.
- `--percent` is outside the valid range.
- No supported videos are found.
- No frames can be extracted from any discovered video.
- The hashing input path does not exist or is not a directory.
- The hashing output path exists but is not a directory.
- The perceptual-hash threshold is less than `0`.
- No supported images are found for hashing.

If one video cannot be opened or processed, the CLI prints a warning and continues with the remaining videos. If one image cannot be opened or hashed, the hashing command prints a warning and continues with the remaining images.

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