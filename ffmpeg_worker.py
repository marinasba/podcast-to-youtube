import subprocess
import os
import re


def validate_files(video_filename: str, audio_filename: str) -> list[str]:
    """Validate file extensions. Returns list of error messages (empty = valid)."""
    errors = []
    video_ext = os.path.splitext(video_filename)[1].lower()
    audio_ext = os.path.splitext(audio_filename)[1].lower()

    if video_ext != ".mp4":
        errors.append("La vidéo doit être au format MP4")
    if audio_ext not in (".wav", ".mp3"):
        errors.append("L'audio doit être au format WAV ou MP3")

    return errors


def build_ffmpeg_command(video_path: str, audio_path: str, output_path: str) -> list[str]:
    """Build the FFmpeg command to loop video over audio duration."""
    return [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", video_path,
        "-i", audio_path,
        "-shortest",
        "-c:v", "h264_videotoolbox",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path,
    ]


def get_audio_duration(audio_path: str) -> float | None:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except (ValueError, subprocess.SubprocessError):
        return None


def run_ffmpeg(video_path: str, audio_path: str, output_path: str,
               progress_callback=None) -> dict:
    """
    Run FFmpeg to create the looped video.
    progress_callback(percent: float) is called with 0-100 progress.
    Returns {"success": True/False, "error": str|None}.
    """
    duration = get_audio_duration(audio_path)
    cmd = build_ffmpeg_command(video_path, audio_path, output_path)

    process = subprocess.Popen(
        cmd, stderr=subprocess.PIPE, text=True, bufsize=1
    )

    time_pattern = re.compile(r"time=(\d+):(\d+):(\d+)\.(\d+)")

    for line in process.stderr:
        if duration and progress_callback:
            match = time_pattern.search(line)
            if match:
                h, m, s, cs = match.groups()
                current = int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100
                percent = min((current / duration) * 100, 99.0)
                progress_callback(percent)

    process.wait()

    if process.returncode == 0:
        if progress_callback:
            progress_callback(100.0)
        return {"success": True, "error": None}
    else:
        return {"success": False, "error": "FFmpeg a échoué. Vérifie tes fichiers."}
