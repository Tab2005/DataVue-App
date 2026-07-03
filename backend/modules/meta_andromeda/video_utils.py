"""
Meta Andromeda Module - video keyframe extraction (docs/20 task 3.3a / P2-1).

Extracts a handful of keyframes from a video asset via an ffmpeg subprocess so
the scoring runtime can actually "see" video content instead of scoring on
headline/primary_text alone. Every failure mode (ffmpeg missing, corrupt file,
timeout) degrades to an empty list rather than raising — callers must treat
that as "no visual content available" and fall back to the
video_content_not_inspected risk tag + confidence penalty, not crash the
scoring request over a missing system dependency.
"""

import base64
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

FFMPEG_TIMEOUT_SECONDS = 20
DEFAULT_KEYFRAME_TIMESTAMPS_SEC = (0.0, 2.0, 5.0)


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def extract_video_keyframes_base64(
    video_bytes: bytes,
    timestamps_sec: tuple[float, ...] = DEFAULT_KEYFRAME_TIMESTAMPS_SEC,
) -> list[str]:
    """Extract one JPEG frame per timestamp and return them as
    data:image/jpeg;base64 URIs, in timestamp order. Timestamps past the end
    of a short video simply fail to extract and are skipped (partial results
    are still useful — 1-2 frames beats zero)."""
    if not video_bytes:
        return []
    if not ffmpeg_available():
        logger.warning("[VideoUtils] ffmpeg not found on PATH; skipping keyframe extraction.")
        return []

    data_uris: list[str] = []
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            video_path = tmp_path / "input.mp4"
            video_path.write_bytes(video_bytes)

            for i, ts in enumerate(timestamps_sec):
                frame_path = tmp_path / f"frame_{i}.jpg"
                try:
                    subprocess.run(
                        [
                            "ffmpeg", "-y",
                            "-ss", str(ts),
                            "-i", str(video_path),
                            "-frames:v", "1",
                            "-q:v", "3",
                            str(frame_path),
                        ],
                        capture_output=True,
                        timeout=FFMPEG_TIMEOUT_SECONDS,
                        check=True,
                    )
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                    logger.warning("[VideoUtils] ffmpeg frame extraction failed at t=%ss: %s", ts, exc)
                    continue

                if frame_path.exists() and frame_path.stat().st_size > 0:
                    frame_bytes = frame_path.read_bytes()
                    b64 = base64.b64encode(frame_bytes).decode("utf-8")
                    data_uris.append(f"data:image/jpeg;base64,{b64}")
    except Exception as exc:
        logger.warning("[VideoUtils] Keyframe extraction failed unexpectedly: %s", exc)
        return data_uris

    return data_uris
