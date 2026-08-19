from pathlib import Path
from typing import Annotated

import typer

from extract_frames.discovery import find_videos
from extract_frames.extraction import extract_video_frames
from extract_frames.progress import console, progress_track

app = typer.Typer(add_completion=False)


@app.command()
def main(
    input_dir: Annotated[
        Path,
        typer.Option("--input", help="Directory to scan for videos."),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output", help="Directory where extracted frames are saved."),
    ],
    percent: Annotated[
        float,
        typer.Option("--percent", help="Percentage of frames to extract from each video."),
    ],
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
