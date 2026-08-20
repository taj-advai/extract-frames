from pathlib import Path
from typing import Annotated

import typer

from extract_frames.discovery import find_videos
from extract_frames.extraction import extract_video_frames
from extract_frames.flatten import flatten_images
from extract_frames.progress import console, progress_track

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
