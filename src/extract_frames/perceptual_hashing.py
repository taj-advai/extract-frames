from collections.abc import Iterable
from pathlib import Path

import imagehash
from PIL import Image, UnidentifiedImageError

from extract_frames.models import ImageHashRecord
from extract_frames.progress import progress_track


def hash_images(
    image_paths: Iterable[Path],
    show_progress: bool = False,
) -> list[ImageHashRecord]:
    paths = list(image_paths)
    if show_progress:
        iterator = progress_track(paths, description="Hashing images", total=len(paths))
    else:
        iterator = iter(paths)

    records: list[ImageHashRecord] = []
    for image_path in iterator:
        records.append(hash_image(image_path))
    return records


def hash_image(image_path: Path) -> ImageHashRecord:
    try:
        with Image.open(image_path) as image:
            hash_value = imagehash.phash(image)
    except (OSError, UnidentifiedImageError) as error:
        return ImageHashRecord(
            image_path=image_path,
            hash_value=None,
            success=False,
            warning=f"{image_path.name}: {error}",
        )

    return ImageHashRecord(
        image_path=image_path,
        hash_value=hash_value,
        success=True,
    )