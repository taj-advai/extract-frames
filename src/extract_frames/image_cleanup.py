import json
from pathlib import Path
from shutil import copy2

from extract_frames.image_discovery import find_images
from extract_frames.models import CleanupResult, HashProcessResult, SimilarityGroup
from extract_frames.output_paths import sanitize_path_part
from extract_frames.progress import progress_track


def write_grouped_output(
    input_dir: Path,
    output_dir: Path,
    groups: list[SimilarityGroup],
    warnings: list[str],
    show_progress: bool = False,
) -> HashProcessResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    images_copied = 0
    iterable = progress_track(groups, description="Writing groups", total=len(groups)) if show_progress else groups

    for group in iterable:
        group_dir = output_dir / f"group_{group.group_id:04d}"
        group_dir.mkdir(parents=True, exist_ok=True)
        for image_path in group.image_paths:
            copy2(image_path, group_dir / _grouped_image_name(input_dir, image_path))
            images_copied += 1

    _write_report(output_dir, groups, warnings)
    return HashProcessResult(
        images_discovered=0,
        images_hashed=0,
        groups_found=len(groups),
        images_copied=images_copied,
        images_removed=0,
        warnings=tuple(warnings),
    )


def write_cleaned_output(
    input_dir: Path,
    output_dir: Path,
    all_images: list[Path],
    groups: list[SimilarityGroup],
    warnings: list[str],
    show_progress: bool = False,
) -> HashProcessResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    removed_paths = {
        image_path
        for group in groups
        for image_path in group.image_paths
        if image_path != group.representative_path
    }
    images_to_copy = [image_path for image_path in all_images if image_path not in removed_paths]
    iterable = (
        progress_track(images_to_copy, description="Writing cleaned images", total=len(images_to_copy))
        if show_progress
        else images_to_copy
    )

    images_copied = 0
    for image_path in iterable:
        destination_path = output_dir / image_path.relative_to(input_dir)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(image_path, destination_path)
        images_copied += 1

    _write_report(output_dir, groups, warnings)
    return HashProcessResult(
        images_discovered=len(all_images),
        images_hashed=len(all_images) - len(warnings),
        groups_found=len(groups),
        images_copied=images_copied,
        images_removed=len(removed_paths),
        warnings=tuple(warnings),
    )


def cleanup_grouped_output(grouped_dir: Path, show_progress: bool = False) -> CleanupResult:
    group_dirs = sorted(path for path in grouped_dir.iterdir() if path.is_dir())
    iterable = (
        progress_track(group_dirs, description="Cleaning groups", total=len(group_dirs))
        if show_progress
        else group_dirs
    )

    kept_images = 0
    removed_images = 0
    skipped_images = 0
    warnings: list[str] = []
    for group_dir in iterable:
        images = find_images(group_dir)
        if not images:
            skipped_images += 1
            continue
        kept_images += 1
        for image_path in images[1:]:
            try:
                image_path.unlink()
                removed_images += 1
            except OSError as error:
                warnings.append(f"{image_path}: {error}")

    return CleanupResult(
        kept_images=kept_images,
        removed_images=removed_images,
        skipped_images=skipped_images,
        warnings=tuple(warnings),
    )


def _grouped_image_name(input_dir: Path, image_path: Path) -> str:
    relative_path = image_path.relative_to(input_dir)
    safe_parts = [sanitize_path_part(part) for part in relative_path.parts]
    return "__".join(safe_parts)


def _write_report(output_dir: Path, groups: list[SimilarityGroup], warnings: list[str]) -> None:
    report = {
        "groups": [
            {
                "group_id": group.group_id,
                "representative": group.representative_path.as_posix(),
                "images": [image_path.as_posix() for image_path in group.image_paths],
            }
            for group in groups
        ],
        "warnings": warnings,
    }
    (output_dir / "similar-groups.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )