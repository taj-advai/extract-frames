from pathlib import Path

WINDOWS_RESERVED_FILENAME_CHARACTERS = '<>:"/\\|?*'


def sanitize_path_part(path_part: str) -> str:
    sanitized_characters = []
    for character in path_part:
        if character in WINDOWS_RESERVED_FILENAME_CHARACTERS or character.isspace():
            sanitized_characters.append("-")
        else:
            sanitized_characters.append(character)

    sanitized = "".join(sanitized_characters).strip("-._")
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")
    return sanitized or "video"


def build_video_output_dir(output_dir: Path, input_dir: Path, video_path: Path) -> Path:
    relative_video_path = video_path.relative_to(input_dir)
    relative_without_suffix = relative_video_path.with_suffix("")
    safe_parts = [sanitize_path_part(path_part) for path_part in relative_without_suffix.parts]
    return output_dir / "_".join(safe_parts)


def frame_output_path(video_output_dir: Path, frame_number: int) -> Path:
    return video_output_dir / f"frame_{frame_number:06d}.jpg"
