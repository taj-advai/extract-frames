import struct
import zlib
from pathlib import Path

from extract_frames.perceptual_hashing import hash_images


def write_png(path: Path, pixels: list[list[tuple[int, int, int]]]) -> None:
    height = len(pixels)
    width = len(pixels[0])
    raw_rows = b"".join(
        b"\x00" + b"".join(bytes(pixel) for pixel in row) for row in pixels
    )

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    image_data = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(
                b"IHDR",
                struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0),
            ),
            chunk(b"IDAT", zlib.compress(raw_rows)),
            chunk(b"IEND", b""),
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_data)


def checkerboard_pixels(size: int = 32) -> list[list[tuple[int, int, int]]]:
    return [
        [
            (240, 240, 240) if (row + column) % 2 == 0 else (20, 20, 20)
            for column in range(size)
        ]
        for row in range(size)
    ]


def test_hash_images_returns_stable_hash_records_for_generated_images(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "frame_000001.png"
    write_png(image_path, checkerboard_pixels())

    first_record = hash_images([image_path])[0]
    second_record = hash_images([image_path])[0]

    assert first_record.image_path == image_path
    assert first_record.success is True
    assert first_record.warning is None
    assert first_record.hash_value is not None
    assert first_record.hash_value == second_record.hash_value


def test_hash_images_produces_matching_hashes_for_duplicate_images(
    tmp_path: Path,
) -> None:
    first_image = tmp_path / "clip-a" / "frame_000001.png"
    second_image = tmp_path / "clip-b" / "frame_000001.png"
    pixels = checkerboard_pixels()
    write_png(first_image, pixels)
    write_png(second_image, pixels)

    records = hash_images([first_image, second_image])

    assert [record.image_path for record in records] == [first_image, second_image]
    assert all(record.success for record in records)
    assert records[0].hash_value == records[1].hash_value


def test_hash_images_returns_warning_records_for_unreadable_images(
    tmp_path: Path,
) -> None:
    unreadable_image = tmp_path / "broken.jpg"
    unreadable_image.write_text("not image data", encoding="utf-8")

    record = hash_images([unreadable_image])[0]

    assert record.image_path == unreadable_image
    assert record.success is False
    assert record.hash_value is None
    assert record.warning is not None
    assert "broken.jpg" in record.warning