import uuid
import json
import pathlib
from flask import Flask, request, jsonify

from ollama_client import OllamaClient
from validator import validate_config

# --- Initialization ---
app = Flask(__name__)
ollama = OllamaClient()

# --- Directory Setup ---
BASE_DIR = pathlib.Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
INBOX_DIR = JOBS_DIR / "inbox"
PROCESSING_DIR = JOBS_DIR / "processing"
COMPLETED_DIR = JOBS_DIR / "completed"
FAILED_DIR = JOBS_DIR / "failed"

# Ensure directories exist
for d in [INBOX_DIR, PROCESSING_DIR, COMPLETED_DIR, FAILED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- Helper Functions ---
def get_job_path(job_id, dir):
    """Constructs a path to a job file."""
    return dir / f"{job_id}.json"

# --- API Endpoints ---
@app.route("/job", methods=["POST"])
def create_job():
    """
    Receives a prompt, generates a config using Ollama, validates it,
    and saves it as a new job in the inbox.
    """
    data = request.get_json()
    if not data or "prompt" not in data:
        return jsonify({"error": "Prompt is required"}), 400

    prompt = data["prompt"]

    # 1. Generate config from Ollama
    config = ollama.generate_config(prompt)

    if not config:
        return jsonify({"error": "Failed to generate config from Ollama"}), 500

    # 2. Validate the generated config
    is_valid, error_msg = validate_config(config)
    if not is_valid:
        return jsonify({"error": "Generated config failed validation", "details": error_msg}), 500

    # 3. Save the job to the inbox
    job_id = uuid.uuid4().hex
    job_path = get_job_path(job_id, INBOX_DIR)
    try:
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except IOError as e:
        return jsonify({"error": f"Failed to save job file: {e}"}), 500

    return jsonify({"jobId": job_id, "message": "Job created successfully"}), 201


@app.route("/job/next", methods=["GET"])
def get_next_job():
    """
    Finds the oldest job in the inbox, moves it to processing,
    and returns its content.
    """
    try:
        # Find the oldest file in the inbox
        files = sorted(INBOX_DIR.iterdir(), key=lambda f: f.stat().st_mtime)
        if not files:
            return jsonify({"message": "No pending jobs"}), 404

        oldest_job_path = files[0]
        job_id = oldest_job_path.stem

        processing_path = get_job_path(job_id, PROCESSING_DIR)
        oldest_job_path.rename(processing_path)

        with open(processing_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        return jsonify({"jobId": job_id, "config": content}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500


@app.route("/job/<string:job_id>/result", methods=["POST"])
def report_job_result(job_id):
    """
    Reports the result of a job. Moves the job from processing to
    completed or failed directory.
    """
    data = request.get_json()
    status = data.get("status")

    if status not in ["success", "failure"]:
        return jsonify({"error": "Status must be 'success' or 'failure'"}), 400

    processing_path = get_job_path(job_id, PROCESSING_DIR)

    if not processing_path.exists():
        return jsonify({"error": "Job not found in processing queue"}), 404

    try:
        if status == "success":
            destination_path = get_job_path(job_id, COMPLETED_DIR)
        else:
            destination_path = get_job_path(job_id, FAILED_DIR)

        processing_path.rename(destination_path)

        # Optionally, log the reason for failure
        if status == "failure" and "reason" in data:
            with open(destination_path.with_suffix('.log'), 'w') as f:
                f.write(data["reason"])

        return jsonify({"message": f"Job '{job_id}' marked as {status}"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to move job file: {e}"}), 500

# --- Main Execution ---
if __name__ == "__main__":
    app.run(debug=True, port=5100)
