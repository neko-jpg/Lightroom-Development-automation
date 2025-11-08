import uuid
import json
import pathlib
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, request, jsonify

from ollama_client import OllamaClient
from validator import validate_config
from config_manager import ConfigManager
from logging_system import get_logging_system, PerformanceTimer
from hot_folder_watcher import HotFolderWatcher
from file_import_processor import FileImportProcessor, DuplicateFileError, ImportError as FileImportError
from models.database import init_db, get_session

# --- Initialization ---
app = Flask(__name__)
ollama = OllamaClient()

# Initialize configuration manager
config_manager = ConfigManager()
try:
    system_config = config_manager.load()
    app.logger.info("System configuration loaded successfully")
except Exception as e:
    app.logger.warning(f"Failed to load configuration, using defaults: {e}")
    system_config = config_manager.generate_default()
    config_manager.save()

# --- Logging Setup ---
# Initialize structured logging system
log_level = system_config.get('system', {}).get('log_level', 'INFO')
logging_system = get_logging_system(log_level=log_level)

# Configure Flask app logger to use structured logging
log_file = pathlib.Path(__file__).parent / "local_bridge.log"
handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Log system startup
logging_system.log("INFO", "Junmai AutoDev Bridge Server initializing", 
                   version="2.0", log_level=log_level)

# --- Database Initialization ---
# Initialize database
db_path = pathlib.Path(__file__).parent / "data" / "junmai.db"
db_path.parent.mkdir(parents=True, exist_ok=True)
init_db(f'sqlite:///{db_path}')
logging_system.log("INFO", "Database initialized", db_path=str(db_path))

# --- File Import Processor Setup ---
file_import_processor = None

def initialize_file_import_processor():
    """Initialize file import processor from configuration"""
    global file_import_processor
    
    import_config = system_config.get('import', {})
    
    # Get import settings
    import_mode = import_config.get('mode', 'copy')
    destination_folder = import_config.get('destination_folder')
    
    # If no destination folder configured, use default
    if not destination_folder:
        destination_folder = str(pathlib.Path(__file__).parent / "data" / "imported_photos")
    
    try:
        file_import_processor = FileImportProcessor(
            import_mode=import_mode,
            destination_folder=destination_folder
        )
        logging_system.log("INFO", "File import processor initialized", 
                          mode=import_mode, destination=destination_folder)
    except Exception as e:
        logging_system.log_error("Failed to initialize file import processor", exception=e)

# Initialize file import processor
initialize_file_import_processor()

# --- Hot Folder Watcher Setup ---
hot_folder_watcher = None

def on_new_file_detected(file_path: str):
    """
    Callback function for hot folder watcher
    
    Called when a new image file is detected in monitored folders.
    Automatically imports the file to the database.
    """
    logging_system.log("INFO", "New file detected by hot folder watcher", 
                      file_path=file_path)
    
    if file_import_processor is None:
        logging_system.log_error("File import processor not initialized")
        return
    
    # Check if auto-import is enabled
    auto_import = system_config.get('processing', {}).get('auto_import', True)
    
    if not auto_import:
        logging_system.log("INFO", "Auto-import disabled, skipping file", file_path=file_path)
        return
    
    try:
        # Determine session name from folder structure
        file_path_obj = pathlib.Path(file_path)
        parent_folder = file_path_obj.parent.name
        session_name = f"Auto_{parent_folder}_{datetime.now().strftime('%Y%m%d')}"
        
        # Get or create session
        db_session = get_session()
        try:
            session = file_import_processor.get_or_create_session(
                session_name=session_name,
                import_folder=str(file_path_obj.parent),
                db_session=db_session
            )
            
            # Import file
            photo, final_path = file_import_processor.import_file(
                file_path=file_path,
                session_id=session.id,
                check_duplicates=True,
                db_session=db_session
            )
            
            # Update session statistics
            session.total_photos += 1
            db_session.commit()
            
            logging_system.log("INFO", "File imported successfully", 
                              file_path=file_path,
                              photo_id=photo.id,
                              session_id=session.id,
                              final_path=final_path)
            
            app.logger.info(f"File imported: {file_path} -> photo_id={photo.id}")
            
        finally:
            db_session.close()
            
    except DuplicateFileError as e:
        logging_system.log("WARNING", "Duplicate file detected, skipping import", 
                          file_path=file_path, error=str(e))
        app.logger.warning(f"Duplicate file skipped: {file_path}")
        
    except FileImportError as e:
        logging_system.log_error("Failed to import file", 
                                file_path=file_path, exception=e)
        app.logger.error(f"Failed to import file {file_path}: {e}")
        
    except Exception as e:
        logging_system.log_error("Unexpected error during file import", 
                                file_path=file_path, exception=e)
        app.logger.error(f"Unexpected error importing {file_path}: {e}", exc_info=True)

def initialize_hot_folder_watcher():
    """Initialize hot folder watcher from configuration"""
    global hot_folder_watcher
    
    hot_folders = system_config.get('system', {}).get('hot_folders', [])
    
    if not hot_folders:
        logging_system.log("INFO", "No hot folders configured, watcher not started")
        return
    
    try:
        hot_folder_watcher = HotFolderWatcher(
            folders=hot_folders,
            callback=on_new_file_detected,
            write_complete_delay=2.0
        )
        hot_folder_watcher.start()
        logging_system.log("INFO", "Hot folder watcher started", 
                          folder_count=len(hot_folders))
    except Exception as e:
        logging_system.log_error("Failed to start hot folder watcher", exception=e)

# Initialize hot folder watcher if configured
initialize_hot_folder_watcher()

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
    with PerformanceTimer(logging_system, "create_job"):
        logging_system.log("INFO", "Received request to /job endpoint")
        data = request.get_json()
        if not data or "prompt" not in data:
            logging_system.log("WARNING", "Request to /job failed: 'prompt' not in request body")
            return jsonify({"error": "Prompt is required"}), 400

        prompt = data["prompt"]
        logging_system.log("INFO", "Generating config for prompt", 
                          prompt_length=len(prompt), prompt_preview=prompt[:80])

        # 1. Generate config from Ollama
        config = ollama.generate_config(prompt)

        if not config:
            logging_system.log_error("Failed to generate config from Ollama")
            return jsonify({"error": "Failed to generate config from Ollama"}), 500
        logging_system.log("INFO", "Successfully generated config from Ollama")

        # 2. Validate the generated config
        is_valid, error_msg = validate_config(config)
        if not is_valid:
            logging_system.log_error("Generated config failed validation", 
                                    error_message=error_msg)
            return jsonify({"error": "Generated config failed validation", "details": error_msg}), 500
        logging_system.log("INFO", "Config validation successful")

        # 3. Save the job to the inbox
        job_id = uuid.uuid4().hex
        job_path = get_job_path(job_id, INBOX_DIR)
        try:
            with open(job_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logging_system.log("INFO", "Successfully created and saved job", 
                              job_id=job_id, job_path=str(job_path))
        except IOError as e:
            logging_system.log_error(f"Failed to save job file for job {job_id}", 
                                    exception=e, job_id=job_id)
            return jsonify({"error": f"Failed to save job file: {e}"}), 500

        return jsonify({"jobId": job_id, "message": "Job created successfully"}), 201


@app.route("/job/next", methods=["GET"])
def get_next_job():
    """
    Finds the oldest job in the inbox, moves it to processing,
    and returns its content.
    """
    with PerformanceTimer(logging_system, "get_next_job"):
        logging_system.log("INFO", "Received request for the next job")
        try:
            files = sorted(INBOX_DIR.iterdir(), key=lambda f: f.stat().st_mtime)
            if not files:
                logging_system.log("INFO", "No pending jobs found in inbox")
                return jsonify({"message": "No pending jobs"}), 404

            oldest_job_path = files[0]
            job_id = oldest_job_path.stem

            processing_path = get_job_path(job_id, PROCESSING_DIR)
            oldest_job_path.rename(processing_path)

            with open(processing_path, "r", encoding="utf-8") as f:
                content = json.load(f)

            logging_system.log("INFO", "Moved job to processing and returned content", 
                              job_id=job_id)
            return jsonify({"jobId": job_id, "config": content}), 200

        except Exception as e:
            logging_system.log_error("An error occurred in /job/next", exception=e)
            return jsonify({"error": f"An error occurred: {e}"}), 500


@app.route("/job/<string:job_id>/result", methods=["POST"])
def report_job_result(job_id):
    """
    Reports the result of a job. Moves the job from processing to
    completed or failed directory.
    """
    with PerformanceTimer(logging_system, "report_job_result", job_id=job_id):
        logging_system.log("INFO", "Received result for job", job_id=job_id)
        data = request.get_json()
        status = data.get("status")

        if status not in ["success", "failure"]:
            logging_system.log("WARNING", "Invalid status for job", 
                              job_id=job_id, status=status)
            return jsonify({"error": "Status must be 'success' or 'failure'"}), 400

        processing_path = get_job_path(job_id, PROCESSING_DIR)

        if not processing_path.exists():
            logging_system.log_error("Job not found in processing queue", 
                                    job_id=job_id)
            return jsonify({"error": "Job not found in processing queue"}), 404

        try:
            destination_dir = COMPLETED_DIR if status == "success" else FAILED_DIR
            destination_path = get_job_path(job_id, destination_dir)

            processing_path.rename(destination_path)
            logging_system.log("INFO", f"Moved job to {destination_dir.name}", 
                              job_id=job_id, status=status)

            if status == "failure" and "reason" in data:
                reason = data.get("reason", "No reason provided.")
                with open(destination_path.with_suffix('.log'), 'w', encoding='utf-8') as f:
                    f.write(reason)
                logging_system.log_error("Job failed", job_id=job_id, reason=reason)

            return jsonify({"message": f"Job '{job_id}' marked as {status}"}), 200
        except Exception as e:
            logging_system.log_error("Failed to move job file", 
                                    exception=e, job_id=job_id)
            return jsonify({"error": f"Failed to move job file: {e}"}), 500

@app.route("/config", methods=["GET"])
def get_config():
    """
    Get current system configuration.
    """
    app.logger.info("Received request to get system configuration.")
    try:
        return jsonify(config_manager.config), 200
    except Exception as e:
        app.logger.exception(f"Failed to get configuration: {e}")
        return jsonify({"error": f"Failed to get configuration: {e}"}), 500


@app.route("/config", methods=["PUT"])
def update_config():
    """
    Update system configuration.
    """
    app.logger.info("Received request to update system configuration.")
    data = request.get_json()
    
    if not data:
        app.logger.warning("Request to /config PUT failed: no data provided.")
        return jsonify({"error": "Configuration data is required"}), 400
    
    try:
        # Validate the new configuration
        is_valid, error_msg = config_manager.validate(data)
        if not is_valid:
            app.logger.error(f"Configuration validation failed: {error_msg}")
            return jsonify({"error": "Invalid configuration", "details": error_msg}), 400
        
        # Save the configuration
        config_manager.save(data)
        
        # Update global system_config
        global system_config
        system_config = config_manager.config
        
        app.logger.info("System configuration updated successfully.")
        return jsonify({"message": "Configuration updated successfully"}), 200
        
    except Exception as e:
        app.logger.exception(f"Failed to update configuration: {e}")
        return jsonify({"error": f"Failed to update configuration: {e}"}), 500


@app.route("/config/validate", methods=["POST"])
def validate_config_endpoint():
    """
    Validate a configuration without saving it.
    """
    app.logger.info("Received request to validate configuration.")
    data = request.get_json()
    
    if not data:
        app.logger.warning("Request to /config/validate failed: no data provided.")
        return jsonify({"error": "Configuration data is required"}), 400
    
    try:
        is_valid, error_msg = config_manager.validate(data)
        
        if is_valid:
            app.logger.info("Configuration validation successful.")
            return jsonify({"valid": True, "message": "Configuration is valid"}), 200
        else:
            app.logger.warning(f"Configuration validation failed: {error_msg}")
            return jsonify({"valid": False, "error": error_msg}), 200
            
    except Exception as e:
        app.logger.exception(f"Validation error: {e}")
        return jsonify({"error": f"Validation error: {e}"}), 500


@app.route("/config/reset", methods=["POST"])
def reset_config():
    """
    Reset configuration to default values.
    """
    app.logger.warning("Received request to reset configuration to defaults.")
    
    try:
        default_config = config_manager.reset_to_default()
        config_manager.save()
        
        # Update global system_config
        global system_config
        system_config = config_manager.config
        
        app.logger.info("Configuration reset to defaults successfully.")
        return jsonify({
            "message": "Configuration reset to defaults",
            "config": default_config
        }), 200
        
    except Exception as e:
        app.logger.exception(f"Failed to reset configuration: {e}")
        return jsonify({"error": f"Failed to reset configuration: {e}"}), 500


@app.route("/config/export", methods=["GET"])
def export_config():
    """
    Export current configuration as JSON download.
    """
    app.logger.info("Received request to export configuration.")
    try:
        from flask import make_response
        
        response = make_response(json.dumps(config_manager.config, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = 'attachment; filename=junmai_config_export.json'
        
        app.logger.info("Configuration exported successfully.")
        return response
        
    except Exception as e:
        app.logger.exception(f"Failed to export configuration: {e}")
        return jsonify({"error": f"Failed to export configuration: {e}"}), 500


# --- Log Viewer API Endpoints ---
@app.route("/logs", methods=["GET"])
def get_logs():
    """
    Get log entries with optional filtering.
    
    Query parameters:
    - category: Log category (main, performance, errors) - default: main
    - lines: Number of lines to return - default: 100
    - level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging_system.log("DEBUG", "Received request to /logs endpoint")
    
    try:
        category = request.args.get('category', 'main')
        lines = int(request.args.get('lines', 100))
        level_filter = request.args.get('level')
        
        # Validate category
        if category not in ['main', 'performance', 'errors']:
            logging_system.log("WARNING", f"Invalid log category requested: {category}")
            return jsonify({"error": "Invalid category. Must be 'main', 'performance', or 'errors'"}), 400
        
        # Validate lines
        if lines < 1 or lines > 10000:
            return jsonify({"error": "Lines must be between 1 and 10000"}), 400
        
        # Read logs
        log_entries = logging_system.read_logs(
            category=category,
            lines=lines,
            level_filter=level_filter
        )
        
        logging_system.log("INFO", f"Retrieved {len(log_entries)} log entries",
                          category=category, lines=lines, level_filter=level_filter)
        
        return jsonify({
            "category": category,
            "count": len(log_entries),
            "entries": log_entries
        }), 200
        
    except ValueError as e:
        logging_system.log_error(f"Invalid parameter in /logs request: {e}")
        return jsonify({"error": f"Invalid parameter: {e}"}), 400
    except Exception as e:
        logging_system.log_error(f"Failed to retrieve logs: {e}", exception=e)
        return jsonify({"error": f"Failed to retrieve logs: {e}"}), 500


@app.route("/logs/stats", methods=["GET"])
def get_log_stats():
    """
    Get statistics about log files.
    """
    logging_system.log("DEBUG", "Received request to /logs/stats endpoint")
    
    try:
        stats = logging_system.get_log_stats()
        
        logging_system.log("INFO", "Retrieved log statistics")
        
        return jsonify(stats), 200
        
    except Exception as e:
        logging_system.log_error(f"Failed to get log statistics: {e}", exception=e)
        return jsonify({"error": f"Failed to get log statistics: {e}"}), 500


@app.route("/logs/clear", methods=["POST"])
def clear_logs():
    """
    Clear log files.
    
    Request body:
    - category: Specific category to clear (optional, clears all if not specified)
    """
    logging_system.log("WARNING", "Received request to clear logs")
    
    try:
        data = request.get_json() or {}
        category = data.get('category')
        
        # Validate category if provided
        if category and category not in ['main', 'performance', 'errors']:
            return jsonify({"error": "Invalid category. Must be 'main', 'performance', or 'errors'"}), 400
        
        logging_system.clear_logs(category=category)
        
        message = f"Cleared {category} logs" if category else "Cleared all logs"
        logging_system.log("WARNING", message)
        
        return jsonify({"message": message}), 200
        
    except Exception as e:
        logging_system.log_error(f"Failed to clear logs: {e}", exception=e)
        return jsonify({"error": f"Failed to clear logs: {e}"}), 500


@app.route("/logs/files", methods=["GET"])
def get_log_files():
    """
    Get list of all log files organized by category.
    """
    logging_system.log("DEBUG", "Received request to /logs/files endpoint")
    
    try:
        log_files = logging_system.get_log_files()
        
        # Convert Path objects to strings
        result = {}
        for category, files in log_files.items():
            result[category] = [str(f) for f in files]
        
        logging_system.log("INFO", "Retrieved log file list")
        
        return jsonify(result), 200
        
    except Exception as e:
        logging_system.log_error(f"Failed to get log files: {e}", exception=e)
        return jsonify({"error": f"Failed to get log files: {e}"}), 500


@app.route("/logs/download/<category>", methods=["GET"])
def download_log_file(category: str):
    """
    Download a specific log file.
    
    Path parameters:
    - category: Log category (main, performance, errors)
    """
    logging_system.log("INFO", f"Received request to download {category} log")
    
    try:
        # Validate category
        if category not in ['main', 'performance', 'errors']:
            return jsonify({"error": "Invalid category. Must be 'main', 'performance', or 'errors'"}), 400
        
        log_file = logging_system.log_dir / f"{category}.log"
        
        if not log_file.exists():
            return jsonify({"error": f"Log file not found: {category}.log"}), 404
        
        from flask import send_file
        
        logging_system.log("INFO", f"Downloading {category} log file")
        
        return send_file(
            log_file,
            as_attachment=True,
            download_name=f"junmai_{category}_{pathlib.Path().stem}.log",
            mimetype='text/plain'
        )
        
    except Exception as e:
        logging_system.log_error(f"Failed to download log file: {e}", exception=e)
        return jsonify({"error": f"Failed to download log file: {e}"}), 500


# --- Hot Folder Management API Endpoints ---
@app.route("/hotfolder/status", methods=["GET"])
def get_hotfolder_status():
    """
    Get hot folder watcher status
    
    Returns:
        Status information including running state and monitored folders
    """
    logging_system.log("DEBUG", "Received request to /hotfolder/status")
    
    try:
        if hot_folder_watcher is None:
            return jsonify({
                "running": False,
                "folders": [],
                "message": "Hot folder watcher not initialized"
            }), 200
        
        status = {
            "running": hot_folder_watcher.is_running(),
            "folders": hot_folder_watcher.get_folders(),
            "folder_count": len(hot_folder_watcher.get_folders())
        }
        
        logging_system.log("INFO", "Retrieved hot folder status", **status)
        
        return jsonify(status), 200
        
    except Exception as e:
        logging_system.log_error(f"Failed to get hot folder status: {e}", exception=e)
        return jsonify({"error": f"Failed to get status: {e}"}), 500


@app.route("/hotfolder/add", methods=["POST"])
def add_hotfolder():
    """
    Add a folder to the hot folder watch list
    
    Request body:
    - folder: Path to folder to monitor
    """
    logging_system.log("INFO", "Received request to add hot folder")
    
    data = request.get_json()
    
    if not data or "folder" not in data:
        logging_system.log("WARNING", "Request to /hotfolder/add failed: 'folder' not in request body")
        return jsonify({"error": "Folder path is required"}), 400
    
    folder = data["folder"]
    
    try:
        global hot_folder_watcher
        
        # Initialize watcher if not exists
        if hot_folder_watcher is None:
            hot_folder_watcher = HotFolderWatcher(
                folders=[],
                callback=on_new_file_detected,
                write_complete_delay=2.0
            )
        
        # Add folder
        success = hot_folder_watcher.add_folder(folder)
        
        if not success:
            return jsonify({"error": f"Failed to add folder: {folder}"}), 400
        
        # Update configuration
        hot_folders = system_config.get('system', {}).get('hot_folders', [])
        if folder not in hot_folders:
            hot_folders.append(folder)
            config_manager.set('system.hot_folders', hot_folders)
            config_manager.save()
        
        # Start watcher if not running
        if not hot_folder_watcher.is_running():
            hot_folder_watcher.start()
        
        logging_system.log("INFO", "Successfully added hot folder", folder=folder)
        
        return jsonify({
            "message": "Folder added successfully",
            "folder": folder,
            "folders": hot_folder_watcher.get_folders()
        }), 200
        
    except Exception as e:
        logging_system.log_error(f"Failed to add hot folder: {e}", exception=e)
        return jsonify({"error": f"Failed to add folder: {e}"}), 500


@app.route("/hotfolder/remove", methods=["POST"])
def remove_hotfolder():
    """
    Remove a folder from the hot folder watch list
    
    Request body:
    - folder: Path to folder to remove
    """
    logging_system.log("INFO", "Received request to remove hot folder")
    
    data = request.get_json()
    
    if not data or "folder" not in data:
        logging_system.log("WARNING", "Request to /hotfolder/remove failed: 'folder' not in request body")
        return jsonify({"error": "Folder path is required"}), 400
    
    folder = data["folder"]
    
    try:
        if hot_folder_watcher is None:
            return jsonify({"error": "Hot folder watcher not initialized"}), 400
        
        # Remove folder
        success = hot_folder_watcher.remove_folder(folder)
        
        if not success:
            return jsonify({"error": f"Folder not in watch list: {folder}"}), 400
        
        # Update configuration
        hot_folders = system_config.get('system', {}).get('hot_folders', [])
        if folder in hot_folders:
            hot_folders.remove(folder)
            config_manager.set('system.hot_folders', hot_folders)
            config_manager.save()
        
        logging_system.log("INFO", "Successfully removed hot folder", folder=folder)
        
        return jsonify({
            "message": "Folder removed successfully",
            "folder": folder,
            "folders": hot_folder_watcher.get_folders()
        }), 200
        
    except Exception as e:
        logging_system.log_error(f"Failed to remove hot folder: {e}", exception=e)
        return jsonify({"error": f"Failed to remove folder: {e}"}), 500


@app.route("/hotfolder/start", methods=["POST"])
def start_hotfolder():
    """
    Start hot folder monitoring
    """
    logging_system.log("INFO", "Received request to start hot folder watcher")
    
    try:
        if hot_folder_watcher is None:
            return jsonify({"error": "Hot folder watcher not initialized"}), 400
        
        if hot_folder_watcher.is_running():
            return jsonify({"message": "Hot folder watcher is already running"}), 200
        
        hot_folder_watcher.start()
        
        logging_system.log("INFO", "Hot folder watcher started")
        
        return jsonify({
            "message": "Hot folder watcher started",
            "folders": hot_folder_watcher.get_folders()
        }), 200
        
    except Exception as e:
        logging_system.log_error(f"Failed to start hot folder watcher: {e}", exception=e)
        return jsonify({"error": f"Failed to start watcher: {e}"}), 500


@app.route("/hotfolder/stop", methods=["POST"])
def stop_hotfolder():
    """
    Stop hot folder monitoring
    """
    logging_system.log("INFO", "Received request to stop hot folder watcher")
    
    try:
        if hot_folder_watcher is None:
            return jsonify({"error": "Hot folder watcher not initialized"}), 400
        
        if not hot_folder_watcher.is_running():
            return jsonify({"message": "Hot folder watcher is not running"}), 200
        
        hot_folder_watcher.stop()
        
        logging_system.log("INFO", "Hot folder watcher stopped")
        
        return jsonify({"message": "Hot folder watcher stopped"}), 200
        
    except Exception as e:
        logging_system.log_error(f"Failed to stop hot folder watcher: {e}", exception=e)
        return jsonify({"error": f"Failed to stop watcher: {e}"}), 500


# --- File Import API Endpoints ---
@app.route("/import/file", methods=["POST"])
def import_single_file():
    """
    Import a single file manually
    
    Request body:
    - file_path: Path to file to import
    - session_id: Optional session ID to associate with
    - check_duplicates: Whether to check for duplicates (default: true)
    """
    logging_system.log("INFO", "Received request to import single file")
    
    data = request.get_json()
    
    if not data or "file_path" not in data:
        logging_system.log("WARNING", "Request to /import/file failed: 'file_path' not in request body")
        return jsonify({"error": "File path is required"}), 400
    
    file_path = data["file_path"]
    session_id = data.get("session_id")
    check_duplicates = data.get("check_duplicates", True)
    
    if file_import_processor is None:
        return jsonify({"error": "File import processor not initialized"}), 500
    
    try:
        photo, final_path = file_import_processor.import_file(
            file_path=file_path,
            session_id=session_id,
            check_duplicates=check_duplicates
        )
        
        logging_system.log("INFO", "File imported successfully via API", 
                          file_path=file_path, photo_id=photo.id)
        
        return jsonify({
            "message": "File imported successfully",
            "photo_id": photo.id,
            "file_name": photo.file_name,
            "final_path": final_path
        }), 200
        
    except DuplicateFileError as e:
        logging_system.log("WARNING", "Duplicate file detected", file_path=file_path)
        return jsonify({"error": "Duplicate file detected", "details": str(e)}), 409
        
    except FileImportError as e:
        logging_system.log_error("Failed to import file", file_path=file_path, exception=e)
        return jsonify({"error": "Failed to import file", "details": str(e)}), 500
        
    except Exception as e:
        logging_system.log_error("Unexpected error during file import", exception=e)
        return jsonify({"error": f"Unexpected error: {e}"}), 500


@app.route("/import/batch", methods=["POST"])
def import_batch_files():
    """
    Import multiple files in batch
    
    Request body:
    - file_paths: List of file paths to import
    - session_id: Optional session ID to associate with
    - check_duplicates: Whether to check for duplicates (default: true)
    - skip_on_error: Whether to skip files that fail import (default: true)
    """
    logging_system.log("INFO", "Received request to import batch files")
    
    data = request.get_json()
    
    if not data or "file_paths" not in data:
        logging_system.log("WARNING", "Request to /import/batch failed: 'file_paths' not in request body")
        return jsonify({"error": "File paths list is required"}), 400
    
    file_paths = data["file_paths"]
    session_id = data.get("session_id")
    check_duplicates = data.get("check_duplicates", True)
    skip_on_error = data.get("skip_on_error", True)
    
    if not isinstance(file_paths, list):
        return jsonify({"error": "file_paths must be a list"}), 400
    
    if file_import_processor is None:
        return jsonify({"error": "File import processor not initialized"}), 500
    
    try:
        results = file_import_processor.import_batch(
            file_paths=file_paths,
            session_id=session_id,
            check_duplicates=check_duplicates,
            skip_on_error=skip_on_error
        )
        
        logging_system.log("INFO", "Batch import completed", 
                          total=results['total'],
                          imported=results['imported'],
                          duplicates=len(results['duplicates']),
                          errors=len(results['errors']))
        
        return jsonify({
            "message": f"Batch import completed: {results['imported']}/{results['total']} files imported",
            "results": results
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to import batch", exception=e)
        return jsonify({"error": f"Failed to import batch: {e}"}), 500


@app.route("/import/session", methods=["POST"])
def create_import_session():
    """
    Create a new import session
    
    Request body:
    - name: Session name
    - import_folder: Import folder path
    """
    logging_system.log("INFO", "Received request to create import session")
    
    data = request.get_json()
    
    if not data or "name" not in data or "import_folder" not in data:
        return jsonify({"error": "Session name and import_folder are required"}), 400
    
    session_name = data["name"]
    import_folder = data["import_folder"]
    
    if file_import_processor is None:
        return jsonify({"error": "File import processor not initialized"}), 500
    
    try:
        session = file_import_processor.get_or_create_session(
            session_name=session_name,
            import_folder=import_folder
        )
        
        logging_system.log("INFO", "Import session created", 
                          session_id=session.id, session_name=session_name)
        
        return jsonify({
            "message": "Session created successfully",
            "session_id": session.id,
            "session_name": session.name,
            "import_folder": session.import_folder,
            "status": session.status
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to create import session", exception=e)
        return jsonify({"error": f"Failed to create session: {e}"}), 500


@app.route("/import/sessions", methods=["GET"])
def get_import_sessions():
    """
    Get list of import sessions
    
    Query parameters:
    - status: Filter by status (optional)
    - limit: Maximum number of sessions to return (default: 50)
    """
    logging_system.log("DEBUG", "Received request to get import sessions")
    
    try:
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        db_session = get_session()
        try:
            from models.database import Session
            
            query = db_session.query(Session)
            
            if status_filter:
                query = query.filter(Session.status == status_filter)
            
            sessions = query.order_by(Session.created_at.desc()).limit(limit).all()
            
            sessions_data = []
            for session in sessions:
                sessions_data.append({
                    'id': session.id,
                    'name': session.name,
                    'created_at': session.created_at.isoformat() if session.created_at else None,
                    'import_folder': session.import_folder,
                    'total_photos': session.total_photos,
                    'processed_photos': session.processed_photos,
                    'status': session.status
                })
            
            logging_system.log("INFO", "Retrieved import sessions", count=len(sessions_data))
            
            return jsonify({
                "sessions": sessions_data,
                "count": len(sessions_data)
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get import sessions", exception=e)
        return jsonify({"error": f"Failed to get sessions: {e}"}), 500


@app.route("/import/photos", methods=["GET"])
def get_imported_photos():
    """
    Get list of imported photos
    
    Query parameters:
    - session_id: Filter by session ID (optional)
    - status: Filter by status (optional)
    - limit: Maximum number of photos to return (default: 100)
    """
    logging_system.log("DEBUG", "Received request to get imported photos")
    
    try:
        session_id = request.args.get('session_id', type=int)
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        db_session = get_session()
        try:
            from models.database import Photo
            
            query = db_session.query(Photo)
            
            if session_id:
                query = query.filter(Photo.session_id == session_id)
            
            if status_filter:
                query = query.filter(Photo.status == status_filter)
            
            photos = query.order_by(Photo.import_time.desc()).limit(limit).all()
            
            photos_data = [photo.to_dict() for photo in photos]
            
            logging_system.log("INFO", "Retrieved imported photos", count=len(photos_data))
            
            return jsonify({
                "photos": photos_data,
                "count": len(photos_data)
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get imported photos", exception=e)
        return jsonify({"error": f"Failed to get photos: {e}"}), 500


@app.route("/import/stats", methods=["GET"])
def get_import_stats():
    """
    Get import statistics
    """
    logging_system.log("DEBUG", "Received request to get import statistics")
    
    try:
        db_session = get_session()
        try:
            from models.database import Photo, Session
            from sqlalchemy import func
            
            # Total photos
            total_photos = db_session.query(func.count(Photo.id)).scalar()
            
            # Photos by status
            status_counts = db_session.query(
                Photo.status,
                func.count(Photo.id)
            ).group_by(Photo.status).all()
            
            # Total sessions
            total_sessions = db_session.query(func.count(Session.id)).scalar()
            
            # Sessions by status
            session_status_counts = db_session.query(
                Session.status,
                func.count(Session.id)
            ).group_by(Session.status).all()
            
            # Recent imports (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_imports = db_session.query(func.count(Photo.id)).filter(
                Photo.import_time >= yesterday
            ).scalar()
            
            stats = {
                'total_photos': total_photos,
                'photos_by_status': {status: count for status, count in status_counts},
                'total_sessions': total_sessions,
                'sessions_by_status': {status: count for status, count in session_status_counts},
                'recent_imports_24h': recent_imports
            }
            
            logging_system.log("INFO", "Retrieved import statistics", **stats)
            
            return jsonify(stats), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get import statistics", exception=e)
        return jsonify({"error": f"Failed to get statistics: {e}"}), 500


# --- Job Queue API Endpoints ---
from job_queue_manager import get_job_queue_manager

job_queue_manager = get_job_queue_manager()


@app.route("/queue/submit", methods=["POST"])
def submit_job_to_queue():
    """
    Submit a photo processing job to the queue
    
    Request body:
    - photo_id: Photo database ID
    - user_requested: Whether manually requested (default: false)
    - config: Optional processing configuration
    """
    logging_system.log("INFO", "Received request to submit job to queue")
    
    data = request.get_json()
    
    if not data or "photo_id" not in data:
        return jsonify({"error": "photo_id is required"}), 400
    
    photo_id = data["photo_id"]
    user_requested = data.get("user_requested", False)
    config = data.get("config")
    
    try:
        task_id = job_queue_manager.submit_photo_processing(
            photo_id=photo_id,
            user_requested=user_requested,
            config=config
        )
        
        logging_system.log("INFO", "Job submitted to queue",
                          photo_id=photo_id,
                          task_id=task_id)
        
        return jsonify({
            "message": "Job submitted successfully",
            "task_id": task_id,
            "photo_id": photo_id
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to submit job", exception=e)
        return jsonify({"error": f"Failed to submit job: {e}"}), 500


@app.route("/queue/batch", methods=["POST"])
def submit_batch_to_queue():
    """
    Submit batch of photos for processing
    
    Request body:
    - photo_ids: List of photo IDs
    - priority: Optional priority (1-10)
    """
    logging_system.log("INFO", "Received request to submit batch to queue")
    
    data = request.get_json()
    
    if not data or "photo_ids" not in data:
        return jsonify({"error": "photo_ids list is required"}), 400
    
    photo_ids = data["photo_ids"]
    priority = data.get("priority", 5)
    
    if not isinstance(photo_ids, list):
        return jsonify({"error": "photo_ids must be a list"}), 400
    
    try:
        task_ids = job_queue_manager.submit_batch_processing(
            photo_ids=photo_ids,
            priority=priority
        )
        
        logging_system.log("INFO", "Batch submitted to queue",
                          photo_count=len(photo_ids))
        
        return jsonify({
            "message": f"Batch of {len(photo_ids)} photos submitted",
            "task_ids": task_ids,
            "photo_count": len(photo_ids)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to submit batch", exception=e)
        return jsonify({"error": f"Failed to submit batch: {e}"}), 500


@app.route("/queue/session/<int:session_id>", methods=["POST"])
def submit_session_to_queue(session_id: int):
    """
    Submit all photos in a session for processing
    
    Request body:
    - auto_select: Whether to only process selected photos (default: true)
    """
    logging_system.log("INFO", "Received request to submit session to queue",
                      session_id=session_id)
    
    data = request.get_json() or {}
    auto_select = data.get("auto_select", True)
    
    try:
        result = job_queue_manager.submit_session_processing(
            session_id=session_id,
            auto_select=auto_select
        )
        
        logging_system.log("INFO", "Session submitted to queue",
                          session_id=session_id,
                          photo_count=result['photo_count'])
        
        return jsonify({
            "message": f"Session submitted with {result['photo_count']} photos",
            **result
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to submit session", exception=e)
        return jsonify({"error": f"Failed to submit session: {e}"}), 500


@app.route("/queue/status/<string:task_id>", methods=["GET"])
def get_job_status(task_id: str):
    """
    Get status of a job
    
    Path parameters:
    - task_id: Celery task ID
    """
    logging_system.log("DEBUG", "Received request for job status", task_id=task_id)
    
    try:
        status = job_queue_manager.get_job_status(task_id)
        
        return jsonify(status), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get job status", exception=e)
        return jsonify({"error": f"Failed to get status: {e}"}), 500


@app.route("/queue/stats", methods=["GET"])
def get_queue_stats():
    """
    Get queue statistics
    """
    logging_system.log("DEBUG", "Received request for queue statistics")
    
    try:
        stats = job_queue_manager.get_queue_stats()
        
        return jsonify(stats), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get queue stats", exception=e)
        return jsonify({"error": f"Failed to get statistics: {e}"}), 500


@app.route("/queue/cancel/<string:task_id>", methods=["POST"])
def cancel_job(task_id: str):
    """
    Cancel a pending or running job
    
    Path parameters:
    - task_id: Celery task ID
    """
    logging_system.log("INFO", "Received request to cancel job", task_id=task_id)
    
    try:
        success = job_queue_manager.cancel_job(task_id)
        
        if success:
            return jsonify({"message": "Job cancelled successfully"}), 200
        else:
            return jsonify({"error": "Failed to cancel job"}), 500
            
    except Exception as e:
        logging_system.log_error("Failed to cancel job", exception=e)
        return jsonify({"error": f"Failed to cancel job: {e}"}), 500


@app.route("/queue/pause", methods=["POST"])
def pause_queue():
    """
    Pause job processing
    """
    logging_system.log("INFO", "Received request to pause queue")
    
    try:
        success = job_queue_manager.pause_queue()
        
        if success:
            return jsonify({"message": "Queue paused successfully"}), 200
        else:
            return jsonify({"error": "Failed to pause queue"}), 500
            
    except Exception as e:
        logging_system.log_error("Failed to pause queue", exception=e)
        return jsonify({"error": f"Failed to pause queue: {e}"}), 500


@app.route("/queue/resume", methods=["POST"])
def resume_queue():
    """
    Resume job processing
    """
    logging_system.log("INFO", "Received request to resume queue")
    
    try:
        success = job_queue_manager.resume_queue()
        
        if success:
            return jsonify({"message": "Queue resumed successfully"}), 200
        else:
            return jsonify({"error": "Failed to resume queue"}), 500
            
    except Exception as e:
        logging_system.log_error("Failed to resume queue", exception=e)
        return jsonify({"error": f"Failed to resume queue: {e}"}), 500


@app.route("/queue/workers", methods=["GET"])
def get_worker_stats():
    """
    Get worker statistics
    """
    logging_system.log("DEBUG", "Received request for worker statistics")
    
    try:
        stats = job_queue_manager.get_worker_stats()
        
        return jsonify(stats), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get worker stats", exception=e)
        return jsonify({"error": f"Failed to get worker statistics: {e}"}), 500


@app.route("/queue/failed", methods=["GET"])
def get_failed_jobs():
    """
    Get list of failed jobs
    
    Query parameters:
    - limit: Maximum number of jobs to return (default: 50)
    """
    logging_system.log("DEBUG", "Received request for failed jobs")
    
    try:
        limit = int(request.args.get('limit', 50))
        failed_jobs = job_queue_manager.get_failed_jobs(limit=limit)
        
        return jsonify({
            "failed_jobs": failed_jobs,
            "count": len(failed_jobs)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get failed jobs", exception=e)
        return jsonify({"error": f"Failed to get failed jobs: {e}"}), 500


@app.route("/queue/retry/<string:task_id>", methods=["POST"])
def retry_failed_job(task_id: str):
    """
    Retry a failed job
    
    Path parameters:
    - task_id: Original task ID
    """
    logging_system.log("INFO", "Received request to retry failed job", task_id=task_id)
    
    try:
        new_task_id = job_queue_manager.retry_failed_job(task_id)
        
        if new_task_id:
            return jsonify({
                "message": "Job retried successfully",
                "original_task_id": task_id,
                "new_task_id": new_task_id
            }), 200
        else:
            return jsonify({"error": "Job not found or cannot be retried"}), 404
            
    except Exception as e:
        logging_system.log_error("Failed to retry job", exception=e)
        return jsonify({"error": f"Failed to retry job: {e}"}), 500


@app.route("/queue/purge", methods=["POST"])
def purge_queue():
    """
    Purge all pending tasks from queue
    
    Request body:
    - queue_name: Optional specific queue to purge
    """
    logging_system.log("WARNING", "Received request to purge queue")
    
    data = request.get_json() or {}
    queue_name = data.get("queue_name")
    
    try:
        count = job_queue_manager.purge_queue(queue_name=queue_name)
        
        return jsonify({
            "message": f"Purged {count} tasks from queue",
            "tasks_purged": count
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to purge queue", exception=e)
        return jsonify({"error": f"Failed to purge queue: {e}"}), 500


# --- Main Execution ---
if __name__ == "__main__":
    logging_system.log("INFO", "Starting Junmai AutoDev Bridge Server", port=5100)
    app.logger.info("Starting Junmai AutoDev Bridge Server...")
    app.run(debug=True, port=5100)
