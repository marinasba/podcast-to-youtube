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
    webbrowser.open("http://localhost:5050")
    app.run(debug=False, port=5050)
