from pathlib import Path

from extract_frames.progress import progress_track

SUPPORTED_VIDEO_SUFFIXES = {".mp4"}


def find_videos(input_dir: Path, show_progress: bool = False) -> list[Path]:
    paths = sorted(input_dir.rglob("*"))
    if show_progress:
        paths = list(progress_track(paths, description="Scanning files", total=len(paths)))

    return sorted(
        path for path in paths if path.is_file() and path.suffix.lower() in SUPPORTED_VIDEO_SUFFIXES
    )
