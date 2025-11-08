import uuid
import json
import pathlib
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify

from ollama_client import OllamaClient
from validator import validate_config

# --- Initialization ---
app = Flask(__name__)
ollama = OllamaClient()

# --- Logging Setup ---
# Configure structured logging to a rotating file.
log_file = pathlib.Path(__file__).parent / "local_bridge.log"
handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

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
app.logger.info("Job directories initialized.")

# --- Helper Functions ---
def get_job_path(job_id, dir_path):
    """Constructs a path to a job file."""
    return dir_path / f"{job_id}.json"

# --- API Endpoints ---
@app.route("/job", methods=["POST"])
def create_job():
    """
    Receives a prompt, generates a config using Ollama, validates it,
    and saves it as a new job in the inbox.
    """
    app.logger.info("Received request to /job endpoint.")
    data = request.get_json()
    if not data or "prompt" not in data:
        app.logger.warning("Request to /job failed: 'prompt' not in request body.")
        return jsonify({"error": "Prompt is required"}), 400

    prompt = data["prompt"]
    app.logger.info(f"Generating config for prompt: '{prompt[:80]}...'")

    # 1. Generate config from Ollama
    config = ollama.generate_config(prompt)

    if not config:
        app.logger.error("Failed to generate config from Ollama.")
        return jsonify({"error": "Failed to generate config from Ollama"}), 500
    app.logger.info("Successfully generated config from Ollama.")

    # 2. Validate the generated config
    is_valid, error_msg = validate_config(config)
    if not is_valid:
        app.logger.error(f"Generated config failed validation: {error_msg}")
        app.logger.debug(f"Invalid config data: {json.dumps(config, indent=2)}")
        return jsonify({"error": "Generated config failed validation", "details": error_msg}), 500
    app.logger.info("Config validation successful.")

    # 3. Save the job to the inbox
    job_id = uuid.uuid4().hex
    job_path = get_job_path(job_id, INBOX_DIR)
    try:
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        app.logger.info(f"Successfully created and saved job {job_id}.")
    except IOError as e:
        app.logger.exception(f"Failed to save job file for job {job_id}: {e}")
        return jsonify({"error": f"Failed to save job file: {e}"}), 500

    return jsonify({"jobId": job_id, "message": "Job created successfully"}), 201


@app.route("/job/next", methods=["GET"])
def get_next_job():
    """
    Finds the oldest job in the inbox, moves it to processing,
    and returns its content.
    """
    app.logger.info("Received request for the next job.")
    try:
        files = sorted(INBOX_DIR.iterdir(), key=lambda f: f.stat().st_mtime)
        if not files:
            app.logger.info("No pending jobs found in inbox.")
            return jsonify({"message": "No pending jobs"}), 404

        oldest_job_path = files[0]
        job_id = oldest_job_path.stem

        processing_path = get_job_path(job_id, PROCESSING_DIR)
        oldest_job_path.rename(processing_path)

        with open(processing_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        app.logger.info(f"Moved job {job_id} to 'processing' and returned its content.")
        return jsonify({"jobId": job_id, "config": content}), 200

    except Exception as e:
        app.logger.exception(f"An error occurred in /job/next: {e}")
        return jsonify({"error": f"An error occurred: {e}"}), 500


@app.route("/job/<string:job_id>/result", methods=["POST"])
def report_job_result(job_id):
    """
    Reports the result of a job. Moves the job from processing to
    completed or failed directory.
    """
    app.logger.info(f"Received result for job {job_id}.")
    data = request.get_json()
    status = data.get("status")

    if status not in ["success", "failure"]:
        app.logger.warning(f"Invalid status '{status}' for job {job_id}.")
        return jsonify({"error": "Status must be 'success' or 'failure'"}), 400

    processing_path = get_job_path(job_id, PROCESSING_DIR)

    if not processing_path.exists():
        app.logger.error(f"Job {job_id} not found in processing queue for result reporting.")
        return jsonify({"error": "Job not found in processing queue"}), 404

    try:
        destination_dir = COMPLETED_DIR if status == "success" else FAILED_DIR
        destination_path = get_job_path(job_id, destination_dir)

        processing_path.rename(destination_path)
        app.logger.info(f"Moved job {job_id} to '{destination_dir.name}'.")

        if status == "failure" and "reason" in data:
            reason = data.get("reason", "No reason provided.")
            with open(destination_path.with_suffix('.log'), 'w', encoding='utf-8') as f:
                f.write(reason)
            app.logger.warning(f"Job {job_id} failed. Reason: {reason}")

        return jsonify({"message": f"Job '{job_id}' marked as {status}"}), 200
    except Exception as e:
        app.logger.exception(f"Failed to move job file for job {job_id}: {e}")
        return jsonify({"error": f"Failed to move job file: {e}"}), 500

# --- Main Execution ---
if __name__ == "__main__":
    app.logger.info("Starting Junmai AutoDev Bridge Server...")
    app.run(debug=True, port=5100)
