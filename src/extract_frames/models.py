from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoInfo:
    source_path: Path
    relative_path: Path
    output_dir: Path


@dataclass(frozen=True)
class ExtractionResult:
    source_path: Path
    frames_requested: int
    frames_written: int
    success: bool
    warning: str | None = None
