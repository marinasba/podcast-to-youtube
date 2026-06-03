import pytest
from ffmpeg_worker import build_ffmpeg_command, validate_files


def test_build_ffmpeg_command():
    cmd = build_ffmpeg_command("/tmp/video.mp4", "/tmp/audio.wav", "/tmp/output.mp4")
    assert cmd == [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", "/tmp/video.mp4",
        "-i", "/tmp/audio.wav",
        "-shortest",
        "-c:v", "h264_videotoolbox",
        "-c:a", "aac",
        "-b:a", "192k",
        "/tmp/output.mp4",
    ]


def test_validate_files_accepts_mp4_wav():
    errors = validate_files("episode.mp4", "podcast.wav")
    assert errors == []


def test_validate_files_accepts_mp4_mp3():
    errors = validate_files("episode.mp4", "podcast.mp3")
    assert errors == []


def test_validate_files_rejects_bad_video():
    errors = validate_files("episode.avi", "podcast.wav")
    assert len(errors) == 1
    assert "vidéo" in errors[0].lower()


def test_validate_files_rejects_bad_audio():
    errors = validate_files("episode.mp4", "podcast.ogg")
    assert len(errors) == 1
    assert "audio" in errors[0].lower()


def test_validate_files_rejects_both_bad():
    errors = validate_files("episode.avi", "podcast.ogg")
    assert len(errors) == 2
