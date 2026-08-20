from pathlib import Path
from typing import Annotated

import typer

from extract_frames.discovery import find_videos
from extract_frames.extraction import extract_video_frames
from extract_frames.flatten import flatten_images
from extract_frames.image_cleanup import (
    cleanup_grouped_output,
    write_cleaned_output,
    write_grouped_output,
)
from extract_frames.image_discovery import find_images
from extract_frames.perceptual_hashing import hash_images
from extract_frames.progress import console, progress_track
from extract_frames.similarity_groups import group_similar_images

app = typer.Typer(add_completion=False, invoke_without_command=True)


@app.callback()
def main(
    context: typer.Context,
    input_dir: Annotated[
        Path | None,
        typer.Option("--input", help="Directory to scan for videos."),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output", help="Directory where extracted frames are saved."),
    ] = None,
    percent: Annotated[
        float | None,
        typer.Option("--percent", help="Percentage of frames to extract from each video."),
    ] = None,
    flatten_output: Annotated[
        bool,
        typer.Option("--flatten", help="Flatten extracted images into the output folder."),
    ] = False,
) -> None:
    if context.invoked_subcommand is not None:
        return
    if input_dir is None or output_dir is None or percent is None:
        console.print(context.get_help())
        raise typer.Exit(code=0)

    run_extraction(input_dir, output_dir, percent, flatten_output=flatten_output)


def run_extraction(
    input_dir: Path,
    output_dir: Path,
    percent: float,
    flatten_output: bool = False,
) -> None:
    if not input_dir.exists():
        console.print(f"Input directory does not exist: {input_dir}")
        raise typer.Exit(code=1)
    if not input_dir.is_dir():
        console.print(f"Input path is not a directory: {input_dir}")
        raise typer.Exit(code=1)
    if output_dir.exists() and not output_dir.is_dir():
        console.print(f"Output path exists and is not a directory: {output_dir}")
        raise typer.Exit(code=1)
    if percent <= 0 or percent > 100:
        console.print("Percent must be greater than 0 and less than or equal to 100.")
        raise typer.Exit(code=1)

    videos = find_videos(input_dir, show_progress=True)
    console.print(f"Discovered {len(videos)} video file(s).")
    if not videos:
        console.print("No supported video files were found.")
        raise typer.Exit(code=1)

    output_dir.mkdir(parents=True, exist_ok=True)
    successful_videos = 0
    total_frames_written = 0

    for video_path in progress_track(videos, description="Extracting videos", total=len(videos)):
        result = extract_video_frames(input_dir, output_dir, video_path, percent)
        total_frames_written += result.frames_written
        if result.success:
            successful_videos += 1
        elif result.warning:
            console.print(f"Warning: {video_path}: {result.warning}")

    console.print(
        f"Finished: {successful_videos}/{len(videos)} video(s), "
        f"{total_frames_written} frame(s) written."
    )
    if successful_videos == 0:
        raise typer.Exit(code=1)

    if flatten_output:
        flatten_result = flatten_images(output_dir, show_progress=True)
        console.print(
            f"Flattened {flatten_result.images_moved} image(s) into {output_dir}. "
            f"Renamed {flatten_result.collisions_renamed} collision(s)."
        )


@app.command()
def flatten(
    folder: Annotated[
        Path,
        typer.Argument(help="Root output folder containing nested extracted image folders."),
    ],
) -> None:
    if not folder.exists():
        console.print(f"Folder does not exist: {folder}")
        raise typer.Exit(code=1)
    if not folder.is_dir():
        console.print(f"Folder path is not a directory: {folder}")
        raise typer.Exit(code=1)

    result = flatten_images(folder, show_progress=True)
    console.print(
        f"Flattened {result.images_moved} image(s) into {folder}. "
        f"Renamed {result.collisions_renamed} collision(s)."
    )


@app.command("hash")
def hash_directory(
    input_dir: Annotated[
        Path,
        typer.Option("--input", help="Image directory to scan for similar images."),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output", help="Directory where grouped or cleaned images are written."),
    ],
    threshold: Annotated[
        int,
        typer.Option("--threshold", help="Maximum perceptual hash distance for similarity."),
    ] = 5,
    group: Annotated[
        bool,
        typer.Option("--group", help="Copy similar images into deterministic group folders."),
    ] = False,
    cleanup: Annotated[
        bool,
        typer.Option("--cleanup", help="Copy a cleaned dataset with similar images removed."),
    ] = False,
) -> None:
    if not input_dir.exists():
        console.print(f"Input directory does not exist: {input_dir}")
        raise typer.Exit(code=1)
    if not input_dir.is_dir():
        console.print(f"Input path is not a directory: {input_dir}")
        raise typer.Exit(code=1)
    if output_dir.exists() and not output_dir.is_dir():
        console.print(f"Output path exists and is not a directory: {output_dir}")
        raise typer.Exit(code=1)
    if threshold < 0:
        console.print("Threshold must be greater than or equal to 0.")
        raise typer.Exit(code=1)
    if group and cleanup:
        console.print("Choose either --group or --cleanup, not both.")
        raise typer.Exit(code=1)
    if not group and not cleanup:
        group = True

    image_paths = find_images(input_dir)
    console.print(f"Discovered {len(image_paths)} image file(s).")
    if not image_paths:
        console.print("No supported image files were found.")
        raise typer.Exit(code=1)

    hash_records = hash_images(image_paths, show_progress=True)
    warnings = [record.warning for record in hash_records if record.warning is not None]
    successful_hashes = [record for record in hash_records if record.success]
    if not successful_hashes:
        console.print("No images could be hashed.")
        raise typer.Exit(code=1)

    groups = group_similar_images(hash_records, threshold=threshold)
    if group:
        result = write_grouped_output(
            input_dir,
            output_dir,
            groups,
            warnings,
            show_progress=True,
        )
        console.print(
            f"Grouped {result.images_copied} image(s) into {result.groups_found} "
            f"similar group(s) under {output_dir}."
        )
    else:
        result = write_cleaned_output(
            input_dir,
            output_dir,
            image_paths,
            groups,
            warnings,
            show_progress=True,
        )
        console.print(
            f"Wrote {result.images_copied} cleaned image(s) to {output_dir}. "
            f"Removed {result.images_removed} similar image(s)."
        )

    if warnings:
        console.print(f"Completed with {len(warnings)} warning(s).")


@app.command("cleanup-similar")
def cleanup_similar(
    folder: Annotated[
        Path,
        typer.Argument(help="Grouped output folder created by `extract-frames hash --group`."),
    ],
) -> None:
    if not folder.exists():
        console.print(f"Folder does not exist: {folder}")
        raise typer.Exit(code=1)
    if not folder.is_dir():
        console.print(f"Folder path is not a directory: {folder}")
        raise typer.Exit(code=1)

    result = cleanup_grouped_output(folder, show_progress=True)
    console.print(
        f"Cleaned {folder}: kept {result.kept_images} image(s), "
        f"removed {result.removed_images} similar image(s), "
        f"skipped {result.skipped_images} empty group(s)."
    )
    if result.warnings:
        console.print(f"Completed with {len(result.warnings)} warning(s).")
