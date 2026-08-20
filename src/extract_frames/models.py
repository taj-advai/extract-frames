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


@dataclass(frozen=True)
class ImageHashRecord:
    image_path: Path
    hash_value: object | None
    success: bool
    warning: str | None = None


@dataclass(frozen=True)
class SimilarityGroup:
    group_id: int
    representative_path: Path
    image_paths: tuple[Path, ...]


@dataclass(frozen=True)
class HashProcessResult:
    images_discovered: int
    images_hashed: int
    groups_found: int
    images_copied: int
    images_removed: int
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class CleanupResult:
    kept_images: int
    removed_images: int
    skipped_images: int
    warnings: tuple[str, ...] = ()
