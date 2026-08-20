from dataclasses import dataclass
from pathlib import Path
from shutil import move

from extract_frames.output_paths import sanitize_path_part
from extract_frames.progress import progress_track

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass(frozen=True)
class FlattenResult:
    images_moved: int
    collisions_renamed: int


def flatten_images(root_dir: Path, show_progress: bool = False) -> FlattenResult:
    nested_images = sorted(
        path
        for path in root_dir.rglob("*")
        if path.is_file()
        and path.parent != root_dir
        and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    )
    if show_progress:
        nested_images = list(
            progress_track(nested_images, description="Flattening images", total=len(nested_images))
        )

    images_moved = 0
    collisions_renamed = 0
    for image_path in nested_images:
        candidate_path = _destination_path(root_dir, image_path)
        destination_path = _unique_destination_path(candidate_path)
        if destination_path != candidate_path:
            collisions_renamed += 1

        move(str(image_path), str(destination_path))
        images_moved += 1

    _remove_empty_subfolders(root_dir)
    return FlattenResult(images_moved=images_moved, collisions_renamed=collisions_renamed)


def _destination_path(root_dir: Path, image_path: Path) -> Path:
    relative_path = image_path.relative_to(root_dir)
    parent_prefix = "_".join(
        sanitize_path_part(path_part) for path_part in relative_path.parent.parts
    )
    file_stem = sanitize_path_part(image_path.stem)
    return root_dir / f"{parent_prefix}_{file_stem}{image_path.suffix.lower()}"


def _unique_destination_path(candidate_path: Path) -> Path:
    if not candidate_path.exists():
        return candidate_path

    for counter in range(1, 1000):
        renamed_path = candidate_path.with_name(
            f"{candidate_path.stem}_{counter:03d}{candidate_path.suffix}"
        )
        if not renamed_path.exists():
            return renamed_path

    raise RuntimeError(f"Could not create a unique filename for {candidate_path}")


def _remove_empty_subfolders(root_dir: Path) -> None:
    directories = sorted(
        (path for path in root_dir.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            continue
