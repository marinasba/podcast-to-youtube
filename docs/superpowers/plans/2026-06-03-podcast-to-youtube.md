# Podcast → YouTube — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web app that loops a short video over a podcast audio track and outputs a YouTube-ready MP4.

**Architecture:** Python Flask serves a single-page HTML frontend. User uploads a video (MP4) and audio (WAV/MP3). The server spawns FFmpeg in a background thread to loop the video for the audio's duration, tracks progress via log parsing, and serves the result for download.

**Tech Stack:** Python 3, Flask, FFmpeg, HTML/CSS/JS

---

## File Map

| File | Responsibility |
|------|---------------|
| `app.py` | Flask server, routes, FFmpeg subprocess management, progress tracking |
| `ffmpeg_worker.py` | FFmpeg command builder and runner, log parsing for progress |
| `templates/index.html` | Single-page UI: upload forms, progress bar, download button |
| `static/style.css` | Minimal styling |
| `requirements.txt` | Python dependencies |
| `tests/test_ffmpeg_worker.py` | Unit tests for FFmpeg command building and validation |
| `tests/test_app.py` | Integration tests for Flask routes |

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
flask==3.1.1
pytest==8.3.5
```

- [ ] **Step 2: Install dependencies**

Run: `cd ~/Projects/podcast-to-youtube && python3 -m pip install -r requirements.txt`
Expected: Successfully installed flask, pytest

- [ ] **Step 3: Verify FFmpeg is installed**

Run: `ffmpeg -version`
Expected: Output starts with `ffmpeg version`. If not installed, run `brew install ffmpeg`.

- [ ] **Step 4: Create test init file**

Create empty `tests/__init__.py`.

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/podcast-to-youtube
git init
git add requirements.txt tests/__init__.py
git commit -m "chore: project setup with dependencies"
```

---

### Task 2: FFmpeg Worker — Command Builder & Validation

**Files:**
- Create: `tests/test_ffmpeg_worker.py`
- Create: `ffmpeg_worker.py`

- [ ] **Step 1: Write failing tests for command builder and file validation**

```python
# tests/test_ffmpeg_worker.py
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
        "-c:v", "libx264",
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/Projects/podcast-to-youtube && python3 -m pytest tests/test_ffmpeg_worker.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ffmpeg_worker'`

- [ ] **Step 3: Implement ffmpeg_worker.py**

```python
# ffmpeg_worker.py
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
        "-c:v", "libx264",
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/Projects/podcast-to-youtube && python3 -m pytest tests/test_ffmpeg_worker.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/podcast-to-youtube
git add ffmpeg_worker.py tests/test_ffmpeg_worker.py
git commit -m "feat: ffmpeg worker with command builder, validation, and progress tracking"
```

---

### Task 3: Flask Server

**Files:**
- Create: `tests/test_app.py`
- Create: `app.py`

- [ ] **Step 1: Write failing tests for Flask routes**

```python
# tests/test_app.py
import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Podcast" in response.data


def test_generate_without_files(client):
    response = client.post("/generate")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_generate_with_wrong_format(client):
    from io import BytesIO
    response = client.post("/generate", data={
        "video": (BytesIO(b"fake"), "test.avi"),
        "audio": (BytesIO(b"fake"), "test.ogg"),
    }, content_type="multipart/form-data")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "errors" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/Projects/podcast-to-youtube && python3 -m pytest tests/test_app.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Implement app.py**

```python
# app.py
import os
import uuid
import shutil
import threading
import webbrowser
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from ffmpeg_worker import validate_files, run_ffmpeg

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# In-memory job tracking: {job_id: {"progress": float, "status": str, "error": str|None}}
jobs = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if "video" not in request.files or "audio" not in request.files:
        return jsonify({"error": "Fichiers manquants"}), 400

    video = request.files["video"]
    audio = request.files["audio"]

    if not video.filename or not audio.filename:
        return jsonify({"error": "Fichiers manquants"}), 400

    errors = validate_files(video.filename, audio.filename)
    if errors:
        return jsonify({"errors": errors}), 400

    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    video_path = os.path.join(job_dir, "video.mp4")
    audio_path = os.path.join(job_dir, "audio" + os.path.splitext(audio.filename)[1])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"podcast_{timestamp}.mp4")

    video.save(video_path)
    audio.save(audio_path)

    jobs[job_id] = {"progress": 0.0, "status": "processing", "error": None, "output": output_path}

    def process():
        def on_progress(percent):
            jobs[job_id]["progress"] = round(percent, 1)

        result = run_ffmpeg(video_path, audio_path, output_path, progress_callback=on_progress)

        if result["success"]:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["progress"] = 100.0
        else:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = result["error"]

        # Cleanup uploaded files
        shutil.rmtree(job_dir, ignore_errors=True)

    thread = threading.Thread(target=process)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job introuvable"}), 404
    job = jobs[job_id]
    return jsonify({
        "progress": job["progress"],
        "status": job["status"],
        "error": job["error"],
    })


@app.route("/download/<job_id>")
def download(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job introuvable"}), 404
    job = jobs[job_id]
    if job["status"] != "done":
        return jsonify({"error": "Vidéo pas encore prête"}), 400
    return send_file(job["output"], as_attachment=True)


if __name__ == "__main__":
    webbrowser.open("http://localhost:5000")
    app.run(debug=False, port=5000)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/Projects/podcast-to-youtube && python3 -m pytest tests/test_app.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/podcast-to-youtube
git add app.py tests/test_app.py
git commit -m "feat: flask server with upload, generate, status, and download routes"
```

---

### Task 4: Frontend — HTML & CSS

**Files:**
- Create: `templates/index.html`
- Create: `static/style.css`

- [ ] **Step 1: Create index.html**

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Podcast → YouTube</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>Podcast → YouTube</h1>
        <p class="subtitle">Combine ta mini vidéo en boucle avec ton audio podcast</p>

        <div id="upload-section">
            <div class="file-input">
                <label for="video">Mini vidéo (MP4)</label>
                <input type="file" id="video" accept=".mp4">
                <span class="file-name" id="video-name">Aucun fichier</span>
            </div>

            <div class="file-input">
                <label for="audio">Piste audio (WAV, MP3)</label>
                <input type="file" id="audio" accept=".wav,.mp3">
                <span class="file-name" id="audio-name">Aucun fichier</span>
            </div>

            <button id="generate-btn" disabled>Générer la vidéo</button>
        </div>

        <div id="progress-section" style="display:none;">
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <p id="progress-text">0%</p>
        </div>

        <div id="done-section" style="display:none;">
            <p class="success">Vidéo prête !</p>
            <button id="download-btn">Télécharger</button>
            <button id="reset-btn" class="secondary">Nouvelle vidéo</button>
        </div>

        <div id="error-section" style="display:none;">
            <p class="error" id="error-text"></p>
            <button id="retry-btn" class="secondary">Réessayer</button>
        </div>
    </div>

    <script>
        const videoInput = document.getElementById("video");
        const audioInput = document.getElementById("audio");
        const videoName = document.getElementById("video-name");
        const audioName = document.getElementById("audio-name");
        const generateBtn = document.getElementById("generate-btn");
        const progressSection = document.getElementById("progress-section");
        const progressFill = document.getElementById("progress-fill");
        const progressText = document.getElementById("progress-text");
        const uploadSection = document.getElementById("upload-section");
        const doneSection = document.getElementById("done-section");
        const errorSection = document.getElementById("error-section");
        const errorText = document.getElementById("error-text");
        const downloadBtn = document.getElementById("download-btn");
        const resetBtn = document.getElementById("reset-btn");
        const retryBtn = document.getElementById("retry-btn");

        let currentJobId = null;

        function updateButtonState() {
            generateBtn.disabled = !(videoInput.files.length && audioInput.files.length);
        }

        videoInput.addEventListener("change", () => {
            videoName.textContent = videoInput.files[0]?.name || "Aucun fichier";
            updateButtonState();
        });

        audioInput.addEventListener("change", () => {
            audioName.textContent = audioInput.files[0]?.name || "Aucun fichier";
            updateButtonState();
        });

        function showSection(section) {
            uploadSection.style.display = "none";
            progressSection.style.display = "none";
            doneSection.style.display = "none";
            errorSection.style.display = "none";
            section.style.display = "block";
        }

        function resetUI() {
            videoInput.value = "";
            audioInput.value = "";
            videoName.textContent = "Aucun fichier";
            audioName.textContent = "Aucun fichier";
            generateBtn.disabled = true;
            progressFill.style.width = "0%";
            progressText.textContent = "0%";
            showSection(uploadSection);
        }

        generateBtn.addEventListener("click", async () => {
            const formData = new FormData();
            formData.append("video", videoInput.files[0]);
            formData.append("audio", audioInput.files[0]);

            showSection(progressSection);

            try {
                const response = await fetch("/generate", { method: "POST", body: formData });
                const data = await response.json();

                if (!response.ok) {
                    const msg = data.errors ? data.errors.join(", ") : data.error;
                    throw new Error(msg);
                }

                currentJobId = data.job_id;
                pollProgress();
            } catch (e) {
                errorText.textContent = e.message;
                showSection(errorSection);
            }
        });

        async function pollProgress() {
            try {
                const response = await fetch(`/status/${currentJobId}`);
                const data = await response.json();

                if (data.status === "processing") {
                    progressFill.style.width = data.progress + "%";
                    progressText.textContent = Math.round(data.progress) + "%";
                    setTimeout(pollProgress, 1000);
                } else if (data.status === "done") {
                    progressFill.style.width = "100%";
                    progressText.textContent = "100%";
                    showSection(doneSection);
                } else if (data.status === "error") {
                    errorText.textContent = data.error;
                    showSection(errorSection);
                }
            } catch (e) {
                errorText.textContent = "Erreur de connexion";
                showSection(errorSection);
            }
        }

        downloadBtn.addEventListener("click", () => {
            window.location.href = `/download/${currentJobId}`;
        });

        resetBtn.addEventListener("click", resetUI);
        retryBtn.addEventListener("click", resetUI);
    </script>
</body>
</html>
```

- [ ] **Step 2: Create style.css**

```css
/* static/style.css */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f5f7;
    color: #1d1d1f;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.container {
    background: white;
    border-radius: 16px;
    padding: 48px;
    max-width: 480px;
    width: 100%;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
    text-align: center;
}

h1 {
    font-size: 28px;
    margin-bottom: 8px;
}

.subtitle {
    color: #6e6e73;
    margin-bottom: 32px;
    font-size: 15px;
}

.file-input {
    margin-bottom: 20px;
    text-align: left;
}

.file-input label {
    display: block;
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 8px;
}

.file-input input[type="file"] {
    width: 100%;
    padding: 12px;
    border: 2px dashed #d2d2d7;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
}

.file-input input[type="file"]:hover {
    border-color: #0071e3;
}

.file-name {
    display: block;
    font-size: 13px;
    color: #6e6e73;
    margin-top: 4px;
}

button {
    background: #0071e3;
    color: white;
    border: none;
    padding: 14px 32px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 16px;
    width: 100%;
    transition: background 0.2s;
}

button:hover:not(:disabled) {
    background: #0077ed;
}

button:disabled {
    background: #d2d2d7;
    cursor: not-allowed;
}

button.secondary {
    background: #f5f5f7;
    color: #1d1d1f;
    margin-top: 8px;
}

button.secondary:hover {
    background: #e8e8ed;
}

.progress-bar {
    background: #e8e8ed;
    border-radius: 8px;
    height: 24px;
    overflow: hidden;
    margin-bottom: 12px;
}

.progress-fill {
    background: #0071e3;
    height: 100%;
    width: 0%;
    border-radius: 8px;
    transition: width 0.5s ease;
}

#progress-text {
    font-size: 14px;
    color: #6e6e73;
}

.success {
    color: #28a745;
    font-weight: 600;
    font-size: 18px;
    margin-bottom: 16px;
}

.error {
    color: #dc3545;
    font-weight: 600;
    margin-bottom: 16px;
}
```

- [ ] **Step 3: Verify the index page test still passes**

Run: `cd ~/Projects/podcast-to-youtube && python3 -m pytest tests/test_app.py::test_index_page -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd ~/Projects/podcast-to-youtube
git add templates/index.html static/style.css
git commit -m "feat: frontend with upload UI, progress bar, and download"
```

---

### Task 5: Manual End-to-End Verification

- [ ] **Step 1: Run all tests**

Run: `cd ~/Projects/podcast-to-youtube && python3 -m pytest -v`
Expected: All 9 tests PASS

- [ ] **Step 2: Start the server**

Run: `cd ~/Projects/podcast-to-youtube && python3 app.py`
Expected: Browser opens at http://localhost:5000, page displays correctly.

- [ ] **Step 3: Test with real files**

1. Upload a mini video (MP4) and an audio file (WAV)
2. Click "Générer la vidéo"
3. Watch the progress bar advance
4. Click "Télécharger" when done
5. Verify the output video plays correctly and loops the video over the full audio

- [ ] **Step 4: Final commit**

```bash
cd ~/Projects/podcast-to-youtube
git add -A
git commit -m "chore: project ready for use"
```
