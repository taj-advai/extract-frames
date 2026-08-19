from pathlib import Path

from extract_frames.frame_selection import select_frame_indexes
from extract_frames.models import ExtractionResult
from extract_frames.output_paths import build_video_output_dir, frame_output_path
from extract_frames.progress import progress_track


def extract_video_frames(
    input_dir: Path, output_dir: Path, video_path: Path, percent: float
) -> ExtractionResult:
    import cv2

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return ExtractionResult(video_path, 0, 0, False, "Could not open video")

    try:
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_indexes = select_frame_indexes(total_frames, percent)
        if not frame_indexes:
            return ExtractionResult(video_path, 0, 0, False, "Video reports zero frames")

        video_output_dir = build_video_output_dir(output_dir, input_dir, video_path)
        video_output_dir.mkdir(parents=True, exist_ok=True)

        frames_written = 0
        progress_description = f"Extracting {video_path.name}"
        frame_progress = progress_track(
            frame_indexes, description=progress_description, total=len(frame_indexes)
        )
        for frame_number, frame_index in enumerate(frame_progress, start=1):
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            frame_was_read, frame = capture.read()
            if not frame_was_read:
                continue

            image_path = frame_output_path(video_output_dir, frame_number)
            if cv2.imwrite(str(image_path), frame):
                frames_written += 1

        return ExtractionResult(
            source_path=video_path,
            frames_requested=len(frame_indexes),
            frames_written=frames_written,
            success=frames_written > 0,
            warning=None if frames_written > 0 else "No selected frames could be written",
        )
    finally:
        capture.release()
