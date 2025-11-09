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
from websocket_fallback import init_websocket_fallback, get_websocket_fallback
from progress_reporter import init_progress_reporter, get_progress_reporter, ProcessingStage
from export_preset_manager import ExportPresetManager, ExportPreset
from auto_export_engine import AutoExportEngine
from websocket_server import init_websocket_server, get_websocket_server, EventType
from websocket_events import (
    broadcast_photo_imported, broadcast_photo_analyzed, broadcast_photo_selected,
    broadcast_photo_approved, broadcast_photo_rejected,
    broadcast_session_created, broadcast_session_updated, broadcast_session_completed,
    broadcast_job_created, broadcast_job_started, broadcast_job_progress,
    broadcast_job_completed, broadcast_job_failed,
    broadcast_system_status, broadcast_resource_warning, broadcast_error_occurred,
    broadcast_queue_status, broadcast_priority_changed,
    broadcast_approval_queue_updated,
    broadcast_export_started, broadcast_export_completed, broadcast_export_failed
)

# --- Initialization ---
app = Flask(__name__)
ollama = OllamaClient()

# Initialize WebSocket fallback server (for Lightroom Lua client)
websocket_fallback = init_websocket_fallback(app)

# Initialize WebSocket server for real-time updates (for GUI/Web clients)
websocket_server = init_websocket_server(app)

logging_system = None  # Will be initialized after config load
progress_reporter = None  # Will be initialized after WebSocket setup

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

# --- Progress Reporter Initialization ---
# Initialize progress reporter with WebSocket server
progress_reporter = init_progress_reporter(websocket_fallback)
logging_system.log("INFO", "Progress reporter initialized")

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

# --- Export Preset Manager Setup ---
export_preset_manager = ExportPresetManager()
logging_system.log("INFO", "Export preset manager initialized", 
                  preset_count=export_preset_manager.get_preset_count())

# --- Auto Export Engine Setup ---
auto_export_engine = AutoExportEngine(preset_manager=export_preset_manager)
logging_system.log("INFO", "Auto export engine initialized")

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
            
            # Broadcast photo imported event via WebSocket
            broadcast_photo_imported(
                photo_id=photo.id,
                session_id=session.id,
                file_name=photo.file_name,
                file_path=final_path
            )
            
            # Broadcast session updated event
            broadcast_session_updated(
                session_id=session.id,
                total_photos=session.total_photos,
                processed_photos=session.processed_photos,
                status=session.status
            )
            
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
        
        # Broadcast photo imported event via WebSocket
        if session_id:
            broadcast_photo_imported(
                photo_id=photo.id,
                session_id=session_id,
                file_name=photo.file_name,
                file_path=final_path
            )
        
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
        
        # Broadcast session created event via WebSocket
        broadcast_session_created(
            session_id=session.id,
            session_name=session.name,
            import_folder=session.import_folder
        )
        
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
        
        # Broadcast job created event via WebSocket
        broadcast_job_created(
            job_id=task_id,
            photo_id=photo_id,
            priority=3 if user_requested else 5
        )
        
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
        
        # Broadcast job created events for each photo via WebSocket
        for i, (task_id, photo_id) in enumerate(zip(task_ids, photo_ids)):
            broadcast_job_created(
                job_id=task_id,
                photo_id=photo_id,
                priority=priority
            )
        
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


# --- Priority Management API Endpoints ---
@app.route("/queue/priority/<string:job_id>", methods=["PUT"])
def adjust_job_priority(job_id: str):
    """
    Adjust priority of an existing job
    
    Path parameters:
    - job_id: Job database ID
    
    Request body:
    - priority: New priority value (1-10)
    """
    logging_system.log("INFO", "Received request to adjust job priority", job_id=job_id)
    
    data = request.get_json()
    
    if not data or "priority" not in data:
        return jsonify({"error": "priority is required"}), 400
    
    new_priority = data["priority"]
    
    if not isinstance(new_priority, int) or new_priority < 1 or new_priority > 10:
        return jsonify({"error": "priority must be an integer between 1 and 10"}), 400
    
    try:
        success = job_queue_manager.adjust_job_priority(job_id, new_priority)
        
        if success:
            return jsonify({
                "message": "Job priority adjusted successfully",
                "job_id": job_id,
                "new_priority": new_priority
            }), 200
        else:
            return jsonify({"error": "Job not found or failed to adjust priority"}), 404
            
    except Exception as e:
        logging_system.log_error("Failed to adjust job priority", exception=e)
        return jsonify({"error": f"Failed to adjust priority: {e}"}), 500


@app.route("/queue/priority/rebalance", methods=["POST"])
def rebalance_priorities():
    """
    Rebalance priorities for all pending jobs
    
    Adjusts priorities based on current age and queue state
    """
    logging_system.log("INFO", "Received request to rebalance queue priorities")
    
    try:
        stats = job_queue_manager.rebalance_priorities()
        
        return jsonify({
            "message": "Queue priorities rebalanced successfully",
            **stats
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to rebalance priorities", exception=e)
        return jsonify({"error": f"Failed to rebalance priorities: {e}"}), 500


@app.route("/queue/priority/distribution", methods=["GET"])
def get_priority_distribution():
    """
    Get distribution of priorities in the queue
    """
    logging_system.log("DEBUG", "Received request for priority distribution")
    
    try:
        distribution = job_queue_manager.get_priority_distribution()
        
        return jsonify(distribution), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get priority distribution", exception=e)
        return jsonify({"error": f"Failed to get priority distribution: {e}"}), 500


@app.route("/queue/priority/session/<int:session_id>/boost", methods=["POST"])
def boost_session_priority(session_id: int):
    """
    Boost priority for all jobs in a session
    
    Path parameters:
    - session_id: Session database ID
    
    Request body:
    - boost_amount: Amount to increase priority by (default: 2)
    """
    logging_system.log("INFO", "Received request to boost session priority",
                      session_id=session_id)
    
    data = request.get_json() or {}
    boost_amount = data.get("boost_amount", 2)
    
    if not isinstance(boost_amount, int) or boost_amount < 1 or boost_amount > 5:
        return jsonify({"error": "boost_amount must be an integer between 1 and 5"}), 400
    
    try:
        stats = job_queue_manager.boost_session_priority(session_id, boost_amount)
        
        if 'error' in stats:
            return jsonify({"error": stats['error']}), 500
        
        return jsonify({
            "message": f"Session priority boosted by {boost_amount}",
            **stats
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to boost session priority", exception=e)
        return jsonify({"error": f"Failed to boost session priority: {e}"}), 500


@app.route("/queue/priority/starvation", methods=["GET"])
def get_starvation_candidates():
    """
    Identify jobs at risk of starvation (waiting too long)
    
    Query parameters:
    - age_threshold_hours: Hours threshold for detection (default: 12)
    """
    logging_system.log("DEBUG", "Received request for starvation candidates")
    
    try:
        age_threshold_hours = int(request.args.get('age_threshold_hours', 12))
        
        candidates = job_queue_manager.get_starvation_candidates(age_threshold_hours)
        
        return jsonify({
            "candidates": candidates,
            "count": len(candidates),
            "age_threshold_hours": age_threshold_hours
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get starvation candidates", exception=e)
        return jsonify({"error": f"Failed to get starvation candidates: {e}"}), 500


@app.route("/queue/priority/auto-boost", methods=["POST"])
def auto_boost_starving_jobs():
    """
    Automatically boost priority of jobs waiting too long
    
    Request body:
    - age_threshold_hours: Hours threshold for auto-boost (default: 12)
    """
    logging_system.log("INFO", "Received request to auto-boost starving jobs")
    
    data = request.get_json() or {}
    age_threshold_hours = data.get("age_threshold_hours", 12)
    
    if not isinstance(age_threshold_hours, int) or age_threshold_hours < 1:
        return jsonify({"error": "age_threshold_hours must be a positive integer"}), 400
    
    try:
        stats = job_queue_manager.auto_boost_starving_jobs(age_threshold_hours)
        
        return jsonify({
            "message": f"Auto-boosted {stats['boosted_count']} starving jobs",
            **stats
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to auto-boost starving jobs", exception=e)
        return jsonify({"error": f"Failed to auto-boost: {e}"}), 500


# --- Progress Reporter API Endpoints ---

@app.route("/progress/job/<string:job_id>", methods=["GET"])
def get_job_progress(job_id: str):
    """
    Get current progress of a job
    
    Path parameters:
    - job_id: Job identifier
    
    Returns:
        JSON with job progress information
        
    Requirements: 4.5
    """
    try:
        if not progress_reporter:
            return jsonify({
                "success": False,
                "error": "Progress reporter not initialized"
            }), 500
        
        status = progress_reporter.get_job_status(job_id)
        
        if not status:
            return jsonify({
                "success": False,
                "error": f"Job {job_id} not found"
            }), 404
        
        return jsonify({
            "success": True,
            "job_status": status
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get job progress", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/progress/active", methods=["GET"])
def get_active_jobs_progress():
    """
    Get progress of all active jobs
    
    Returns:
        JSON with all active jobs and their progress
        
    Requirements: 4.5
    """
    try:
        if not progress_reporter:
            return jsonify({
                "success": False,
                "error": "Progress reporter not initialized"
            }), 500
        
        active_jobs = progress_reporter.get_active_jobs()
        
        return jsonify({
            "success": True,
            "active_jobs": active_jobs,
            "count": len(active_jobs)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get active jobs progress", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/progress/report", methods=["POST"])
def report_progress():
    """
    Report progress update for a job
    
    Request body:
    - job_id: Job identifier
    - stage: Processing stage
    - progress: Progress percentage (0-100)
    - message: Optional progress message
    - details: Optional additional details
    
    Requirements: 4.5
    """
    try:
        data = request.get_json()
        
        if not data or 'job_id' not in data or 'stage' not in data:
            return jsonify({
                "success": False,
                "error": "job_id and stage are required"
            }), 400
        
        if not progress_reporter:
            return jsonify({
                "success": False,
                "error": "Progress reporter not initialized"
            }), 500
        
        job_id = data['job_id']
        stage_name = data['stage']
        progress = data.get('progress', 0)
        message = data.get('message')
        details = data.get('details')
        
        # Convert stage name to ProcessingStage enum
        try:
            stage = ProcessingStage(stage_name)
        except ValueError:
            return jsonify({
                "success": False,
                "error": f"Invalid stage: {stage_name}"
            }), 400
        
        progress_reporter.update_progress(job_id, stage, progress, message, details)
        
        return jsonify({
            "success": True,
            "message": "Progress reported successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to report progress", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/progress/error", methods=["POST"])
def report_progress_error():
    """
    Report an error during job processing
    
    Request body:
    - job_id: Job identifier
    - error_type: Type of error
    - error_message: Error message
    - error_details: Optional detailed error information
    - stage: Optional stage where error occurred
    
    Requirements: 4.5
    """
    try:
        data = request.get_json()
        
        if not data or 'job_id' not in data or 'error_type' not in data or 'error_message' not in data:
            return jsonify({
                "success": False,
                "error": "job_id, error_type, and error_message are required"
            }), 400
        
        if not progress_reporter:
            return jsonify({
                "success": False,
                "error": "Progress reporter not initialized"
            }), 500
        
        job_id = data['job_id']
        error_type = data['error_type']
        error_message = data['error_message']
        error_details = data.get('error_details')
        stage_name = data.get('stage')
        
        stage = None
        if stage_name:
            try:
                stage = ProcessingStage(stage_name)
            except ValueError:
                pass
        
        progress_reporter.report_error(job_id, error_type, error_message, error_details, stage)
        
        return jsonify({
            "success": True,
            "message": "Error reported successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to report error", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# --- Batch Processing Control API Endpoints ---
from batch_controller import get_batch_controller

batch_controller = get_batch_controller()


@app.route("/batch/start", methods=["POST"])
def start_batch():
    """
    Start a new batch processing operation
    
    Request body:
    - photo_ids: List of photo IDs to process
    - session_id: Optional session ID
    - config: Optional processing configuration
    
    Requirements: 11.4
    """
    logging_system.log("INFO", "Received request to start batch processing")
    
    data = request.get_json()
    
    if not data or "photo_ids" not in data:
        logging_system.log("WARNING", "Request to /batch/start failed: 'photo_ids' not in request body")
        return jsonify({"error": "photo_ids is required"}), 400
    
    photo_ids = data["photo_ids"]
    session_id = data.get("session_id")
    config = data.get("config")
    
    if not isinstance(photo_ids, list) or len(photo_ids) == 0:
        return jsonify({"error": "photo_ids must be a non-empty list"}), 400
    
    try:
        batch_id = batch_controller.start_batch(
            photo_ids=photo_ids,
            session_id=session_id,
            config=config
        )
        
        logging_system.log("INFO", "Batch processing started",
                          batch_id=batch_id,
                          photo_count=len(photo_ids))
        
        # Broadcast system status update via WebSocket
        broadcast_system_status(
            status='batch_started',
            details={
                'batch_id': batch_id,
                'photo_count': len(photo_ids),
                'session_id': session_id
            }
        )
        
        return jsonify({
            "message": "Batch processing started",
            "batch_id": batch_id,
            "photo_count": len(photo_ids)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to start batch processing", exception=e)
        return jsonify({"error": f"Failed to start batch: {e}"}), 500


@app.route("/batch/<string:batch_id>/pause", methods=["POST"])
def pause_batch(batch_id: str):
    """
    Pause a running batch
    
    Path parameters:
    - batch_id: Batch identifier
    
    Requirements: 11.4, 14.3
    """
    logging_system.log("INFO", "Received request to pause batch", batch_id=batch_id)
    
    try:
        success = batch_controller.pause_batch(batch_id)
        
        if success:
            logging_system.log("INFO", "Batch paused successfully", batch_id=batch_id)
            
            # Broadcast system status update via WebSocket
            broadcast_system_status(
                status='batch_paused',
                details={'batch_id': batch_id}
            )
            
            return jsonify({
                "message": "Batch paused successfully",
                "batch_id": batch_id
            }), 200
        else:
            return jsonify({
                "error": "Failed to pause batch",
                "batch_id": batch_id
            }), 400
        
    except Exception as e:
        logging_system.log_error("Failed to pause batch", batch_id=batch_id, exception=e)
        return jsonify({"error": f"Failed to pause batch: {e}"}), 500


@app.route("/batch/<string:batch_id>/resume", methods=["POST"])
def resume_batch(batch_id: str):
    """
    Resume a paused batch
    
    Path parameters:
    - batch_id: Batch identifier
    
    Requirements: 11.4, 14.3
    """
    logging_system.log("INFO", "Received request to resume batch", batch_id=batch_id)
    
    try:
        success = batch_controller.resume_batch(batch_id)
        
        if success:
            logging_system.log("INFO", "Batch resumed successfully", batch_id=batch_id)
            
            # Broadcast system status update via WebSocket
            broadcast_system_status(
                status='batch_resumed',
                details={'batch_id': batch_id}
            )
            
            return jsonify({
                "message": "Batch resumed successfully",
                "batch_id": batch_id
            }), 200
        else:
            return jsonify({
                "error": "Failed to resume batch",
                "batch_id": batch_id
            }), 400
        
    except Exception as e:
        logging_system.log_error("Failed to resume batch", batch_id=batch_id, exception=e)
        return jsonify({"error": f"Failed to resume batch: {e}"}), 500


@app.route("/batch/<string:batch_id>/cancel", methods=["POST"])
def cancel_batch(batch_id: str):
    """
    Cancel a batch
    
    Path parameters:
    - batch_id: Batch identifier
    """
    logging_system.log("INFO", "Received request to cancel batch", batch_id=batch_id)
    
    try:
        success = batch_controller.cancel_batch(batch_id)
        
        if success:
            logging_system.log("INFO", "Batch cancelled successfully", batch_id=batch_id)
            return jsonify({
                "message": "Batch cancelled successfully",
                "batch_id": batch_id
            }), 200
        else:
            return jsonify({
                "error": "Failed to cancel batch",
                "batch_id": batch_id
            }), 400
        
    except Exception as e:
        logging_system.log_error("Failed to cancel batch", batch_id=batch_id, exception=e)
        return jsonify({"error": f"Failed to cancel batch: {e}"}), 500


@app.route("/batch/<string:batch_id>/status", methods=["GET"])
def get_batch_status(batch_id: str):
    """
    Get batch status
    
    Path parameters:
    - batch_id: Batch identifier
    
    Requirements: 11.4
    """
    logging_system.log("DEBUG", "Received request for batch status", batch_id=batch_id)
    
    try:
        status = batch_controller.get_batch_status(batch_id)
        
        if status is None:
            return jsonify({"error": "Batch not found"}), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get batch status", batch_id=batch_id, exception=e)
        return jsonify({"error": f"Failed to get batch status: {e}"}), 500


@app.route("/batch/list", methods=["GET"])
def list_batches():
    """
    Get all active batches
    
    Requirements: 11.4
    """
    logging_system.log("DEBUG", "Received request to list batches")
    
    try:
        batches = batch_controller.get_all_batches()
        
        return jsonify({
            "batches": batches,
            "count": len(batches)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to list batches", exception=e)
        return jsonify({"error": f"Failed to list batches: {e}"}), 500


@app.route("/batch/recover", methods=["POST"])
def recover_batches():
    """
    Recover interrupted batches
    
    Requirements: 14.3
    """
    logging_system.log("INFO", "Received request to recover interrupted batches")
    
    try:
        result = batch_controller.recover_interrupted_batches()
        
        logging_system.log("INFO", "Batch recovery completed", **result)
        
        return jsonify({
            "message": "Batch recovery completed",
            **result
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to recover batches", exception=e)
        return jsonify({"error": f"Failed to recover batches: {e}"}), 500


@app.route("/batch/cleanup", methods=["POST"])
def cleanup_batches():
    """
    Clean up old completed batch states
    
    Request body:
    - days_old: Remove batches completed more than this many days ago (default: 7)
    """
    logging_system.log("INFO", "Received request to cleanup old batches")
    
    data = request.get_json() or {}
    days_old = data.get("days_old", 7)
    
    try:
        count = batch_controller.cleanup_completed_batches(days_old=days_old)
        
        logging_system.log("INFO", "Batch cleanup completed", count=count)
        
        return jsonify({
            "message": "Batch cleanup completed",
            "cleaned_count": count,
            "days_old": days_old
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to cleanup batches", exception=e)
        return jsonify({"error": f"Failed to cleanup batches: {e}"}), 500


# --- Authentication Setup ---
from auth_manager import init_auth_manager, configure_cors

# Initialize authentication manager
auth_manager = init_auth_manager()
logging_system.log("INFO", "Authentication manager initialized")

# Configure CORS
configure_cors(app)
logging_system.log("INFO", "CORS configured")

# --- Register Blueprints ---
from api_dashboard import dashboard_bp
from api_extended import api_bp
from api_auth import auth_api_bp
from api_notifications import notifications_bp
from api_email_notifications import email_notifications_bp
from api_line_notifications import line_notifications_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp)
app.register_blueprint(auth_api_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(email_notifications_bp)
app.register_blueprint(line_notifications_bp)

# --- WebSocket Management API Endpoints ---

@app.route("/websocket/clients", methods=["GET"])
def get_websocket_clients():
    """
    Get list of connected WebSocket clients
    
    Returns:
        JSON with list of connected clients and their information
        
    Requirements: 4.5, 7.2
    """
    try:
        ws_server = get_websocket_server()
        
        if not ws_server:
            return jsonify({
                "success": False,
                "error": "WebSocket server not initialized"
            }), 500
        
        clients = ws_server.get_connected_clients()
        
        return jsonify({
            "success": True,
            "clients": clients,
            "count": len(clients)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get WebSocket clients", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/websocket/broadcast", methods=["POST"])
def broadcast_websocket_message():
    """
    Broadcast a custom message to all WebSocket clients
    
    Request body:
    - type: Message type
    - data: Message data (dict)
    - channel: Optional channel for filtered broadcast
    
    Requirements: 4.5, 7.2
    """
    try:
        data = request.get_json()
        
        if not data or 'type' not in data:
            return jsonify({
                "success": False,
                "error": "Message type is required"
            }), 400
        
        ws_server = get_websocket_server()
        
        if not ws_server:
            return jsonify({
                "success": False,
                "error": "WebSocket server not initialized"
            }), 500
        
        message_type = data['type']
        message_data = data.get('data', {})
        channel = data.get('channel')
        
        message = {
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            **message_data
        }
        
        ws_server.broadcast(message, channel=channel)
        
        logging_system.log("INFO", "Broadcasted custom WebSocket message",
                          message_type=message_type, channel=channel)
        
        return jsonify({
            "success": True,
            "message": "Message broadcasted successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to broadcast WebSocket message", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/websocket/disconnect/<int:client_id>", methods=["POST"])
def disconnect_websocket_client(client_id: int):
    """
    Disconnect a specific WebSocket client
    
    Path parameters:
    - client_id: Client ID to disconnect
    
    Requirements: 4.5
    """
    try:
        ws_server = get_websocket_server()
        
        if not ws_server:
            return jsonify({
                "success": False,
                "error": "WebSocket server not initialized"
            }), 500
        
        ws_server.disconnect_client(client_id)
        
        logging_system.log("INFO", "Disconnected WebSocket client", client_id=client_id)
        
        return jsonify({
            "success": True,
            "message": f"Client {client_id} disconnected"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to disconnect WebSocket client", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/websocket/stats", methods=["GET"])
def get_websocket_stats():
    """
    Get WebSocket server statistics
    
    Returns:
        JSON with connection statistics and server status
        
    Requirements: 4.5, 7.2
    """
    try:
        ws_server = get_websocket_server()
        
        if not ws_server:
            return jsonify({
                "success": False,
                "error": "WebSocket server not initialized"
            }), 500
        
        clients = ws_server.get_connected_clients()
        
        # Count clients by type
        client_types = {}
        for client in clients:
            client_type = client.get('client_type', 'unknown')
            client_types[client_type] = client_types.get(client_type, 0) + 1
        
        # Count subscriptions
        all_subscriptions = set()
        for client in clients:
            all_subscriptions.update(client.get('subscriptions', []))
        
        stats = {
            'total_clients': len(clients),
            'clients_by_type': client_types,
            'active_channels': list(all_subscriptions),
            'channel_count': len(all_subscriptions)
        }
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get WebSocket stats", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# --- Main Execution ---
if __name__ == "__main__":
    logging_system.log("INFO", "Starting Junmai AutoDev Bridge Server", port=5100)
    app.logger.info("Starting Junmai AutoDev Bridge Server...")
    app.run(debug=True, port=5100)


# --- Resource Management API Endpoints ---
# Import resource management modules
from resource_manager import get_resource_manager
from resource_aware_queue import get_resource_aware_queue

# Initialize resource management
resource_manager = get_resource_manager()
resource_aware_queue = get_resource_aware_queue()

@app.route("/resources/status", methods=["GET"])
def get_resource_status():
    """
    Get comprehensive system resource status
    
    Returns:
        JSON with CPU, GPU, memory, and disk status
        
    Requirements: 4.3, 12.4, 17.3
    """
    try:
        status = resource_manager.get_system_status()
        
        logging_system.log("DEBUG", "Resource status retrieved")
        
        return jsonify({
            "success": True,
            "status": status
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get resource status", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/cpu", methods=["GET"])
def get_cpu_status():
    """
    Get detailed CPU status
    
    Returns:
        JSON with CPU usage, core count, and frequency
        
    Requirements: 4.3
    """
    try:
        status = resource_manager.get_cpu_status()
        
        return jsonify({
            "success": True,
            "cpu": status
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get CPU status", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/gpu", methods=["GET"])
def get_gpu_status():
    """
    Get detailed GPU status
    
    Returns:
        JSON with GPU temperature, memory, and load
        
    Requirements: 17.3
    """
    try:
        status = resource_manager.get_gpu_status()
        
        return jsonify({
            "success": True,
            "gpu": status
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get GPU status", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/memory", methods=["GET"])
def get_memory_status():
    """
    Get detailed memory status
    
    Returns:
        JSON with memory usage and availability
    """
    try:
        status = resource_manager.get_memory_status()
        
        return jsonify({
            "success": True,
            "memory": status
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get memory status", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/idle", methods=["GET"])
def get_idle_status():
    """
    Get system idle status
    
    Returns:
        JSON with idle state and duration
        
    Requirements: 4.3
    """
    try:
        is_idle = resource_manager.is_system_idle()
        idle_duration = resource_manager.get_idle_duration()
        
        return jsonify({
            "success": True,
            "is_idle": is_idle,
            "idle_duration_seconds": idle_duration
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get idle status", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/metrics/history", methods=["GET"])
def get_metrics_history():
    """
    Get historical resource metrics
    
    Query Parameters:
        limit: Maximum number of records (optional)
        
    Returns:
        JSON with historical metrics
    """
    try:
        limit = request.args.get('limit', type=int)
        history = resource_manager.get_metrics_history(limit=limit)
        
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get metrics history", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/metrics/average", methods=["GET"])
def get_average_metrics():
    """
    Get average resource metrics over time period
    
    Query Parameters:
        duration_minutes: Duration to average over (default: 5)
        
    Returns:
        JSON with average metrics
    """
    try:
        duration = request.args.get('duration_minutes', default=5, type=int)
        averages = resource_manager.get_average_metrics(duration_minutes=duration)
        
        return jsonify({
            "success": True,
            "averages": averages
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get average metrics", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/monitoring/start", methods=["POST"])
def start_resource_monitoring():
    """
    Start continuous resource monitoring
    
    Requirements: 4.3
    """
    try:
        resource_manager.start_monitoring()
        
        logging_system.log("INFO", "Resource monitoring started via API")
        
        return jsonify({
            "success": True,
            "message": "Resource monitoring started"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to start resource monitoring", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/monitoring/stop", methods=["POST"])
def stop_resource_monitoring():
    """
    Stop continuous resource monitoring
    """
    try:
        resource_manager.stop_monitoring()
        
        logging_system.log("INFO", "Resource monitoring stopped via API")
        
        return jsonify({
            "success": True,
            "message": "Resource monitoring stopped"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to stop resource monitoring", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/config", methods=["GET"])
def get_resource_config():
    """
    Get resource manager configuration
    """
    try:
        config = resource_manager.config
        
        return jsonify({
            "success": True,
            "config": config
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get resource config", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/config", methods=["PUT"])
def update_resource_config():
    """
    Update resource manager configuration
    
    Request Body:
        JSON with configuration updates
        
    Requirements: 4.3, 17.3
    """
    try:
        updates = request.get_json()
        
        if not updates:
            return jsonify({
                "success": False,
                "error": "No configuration updates provided"
            }), 400
        
        success = resource_manager.update_config(updates)
        
        if success:
            logging_system.log("INFO", "Resource config updated via API",
                              updates=updates)
            
            return jsonify({
                "success": True,
                "message": "Configuration updated",
                "config": resource_manager.config
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update configuration"
            }), 500
        
    except Exception as e:
        logging_system.log_error("Failed to update resource config", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# --- Resource-Aware Queue API Endpoints ---

@app.route("/resources/queue/status", methods=["GET"])
def get_resource_queue_status():
    """
    Get resource-aware queue status
    
    Returns:
        JSON with queue status and resource state
        
    Requirements: 4.3, 12.4
    """
    try:
        status = resource_aware_queue.get_status()
        
        return jsonify({
            "success": True,
            "status": status
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get resource queue status", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/queue/start", methods=["POST"])
def start_resource_aware_queue():
    """
    Start resource-aware queue control
    
    Requirements: 4.3
    """
    try:
        resource_aware_queue.start()
        
        logging_system.log("INFO", "Resource-aware queue started via API")
        
        return jsonify({
            "success": True,
            "message": "Resource-aware queue control started"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to start resource-aware queue", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/queue/stop", methods=["POST"])
def stop_resource_aware_queue():
    """
    Stop resource-aware queue control
    """
    try:
        resource_aware_queue.stop()
        
        logging_system.log("INFO", "Resource-aware queue stopped via API")
        
        return jsonify({
            "success": True,
            "message": "Resource-aware queue control stopped"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to stop resource-aware queue", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/queue/auto-adjust", methods=["PUT"])
def set_auto_adjust():
    """
    Enable or disable automatic queue adjustment
    
    Request Body:
        {"enabled": true/false}
        
    Requirements: 4.3
    """
    try:
        data = request.get_json()
        
        if 'enabled' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'enabled' field"
            }), 400
        
        enabled = data['enabled']
        resource_aware_queue.set_auto_adjust(enabled)
        
        logging_system.log("INFO", "Auto-adjust setting changed",
                          enabled=enabled)
        
        return jsonify({
            "success": True,
            "message": f"Auto-adjust {'enabled' if enabled else 'disabled'}",
            "enabled": enabled
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to set auto-adjust", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/queue/concurrency", methods=["GET"])
def get_recommended_concurrency():
    """
    Get recommended concurrent job count based on resources
    
    Returns:
        JSON with recommended concurrency
        
    Requirements: 4.3, 12.4
    """
    try:
        concurrency = resource_aware_queue.get_recommended_concurrency()
        
        return jsonify({
            "success": True,
            "recommended_concurrency": concurrency
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get recommended concurrency", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/resources/queue/accept-jobs", methods=["GET"])
def check_accept_new_jobs():
    """
    Check if new jobs should be accepted
    
    Returns:
        JSON with acceptance status
    """
    try:
        should_accept = resource_aware_queue.should_accept_new_jobs()
        delay = resource_aware_queue.get_processing_delay()
        
        return jsonify({
            "success": True,
            "should_accept": should_accept,
            "processing_delay_seconds": delay
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to check job acceptance", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# --- WebSocket Communication API Endpoints ---

@app.route("/ws/status", methods=["GET"])
def get_websocket_status():
    """
    Get WebSocket server status
    
    Returns:
        JSON with connection status and client count
        
    Requirements: 4.5
    """
    try:
        clients = websocket_fallback.get_connected_clients()
        
        return jsonify({
            "success": True,
            "enabled": True,
            "client_count": len(clients),
            "clients": clients
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get WebSocket status", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/ws/broadcast", methods=["POST"])
def broadcast_message():
    """
    Broadcast message to all connected clients
    
    Request body:
    - message: Message object to broadcast
    - channel: Optional channel filter
    
    Requirements: 4.5
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400
        
        message = data['message']
        channel = data.get('channel')
        
        websocket_fallback.broadcast(message, channel=channel)
        
        logging_system.log("INFO", "Message broadcast via WebSocket",
                          message_type=message.get('type'),
                          channel=channel)
        
        return jsonify({
            "success": True,
            "message": "Message broadcast successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to broadcast message", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/ws/send/<string:client_id>", methods=["POST"])
def send_to_client(client_id: str):
    """
    Send message to specific client
    
    Path parameters:
    - client_id: Client identifier
    
    Request body:
    - message: Message object to send
    
    Requirements: 4.5
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400
        
        message = data['message']
        
        websocket_fallback.send_to_client(client_id, message)
        
        logging_system.log("INFO", "Message sent to client via WebSocket",
                          client_id=client_id,
                          message_type=message.get('type'))
        
        return jsonify({
            "success": True,
            "message": "Message sent successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to send message to client", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/ws/notify/job_progress", methods=["POST"])
def notify_job_progress():
    """
    Send job progress notification to all clients
    
    Request body:
    - job_id: Job identifier
    - stage: Current processing stage
    - progress: Progress percentage (0-100)
    - message: Optional progress message
    
    Requirements: 4.5
    """
    try:
        data = request.get_json()
        
        if not data or 'job_id' not in data:
            return jsonify({
                "success": False,
                "error": "job_id is required"
            }), 400
        
        message = {
            'type': 'job_progress',
            'job_id': data['job_id'],
            'stage': data.get('stage', 'processing'),
            'progress': data.get('progress', 0),
            'message': data.get('message', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        websocket_fallback.broadcast(message, channel='jobs')
        
        logging_system.log("INFO", "Job progress notification sent",
                          job_id=data['job_id'],
                          progress=data.get('progress', 0))
        
        return jsonify({
            "success": True,
            "message": "Progress notification sent"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to send job progress notification", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/ws/notify/job_complete", methods=["POST"])
def notify_job_complete():
    """
    Send job completion notification
    
    Request body:
    - job_id: Job identifier
    - success: Whether job succeeded
    - result: Optional result data
    
    Requirements: 4.5
    """
    try:
        data = request.get_json()
        
        if not data or 'job_id' not in data:
            return jsonify({
                "success": False,
                "error": "job_id is required"
            }), 400
        
        success = data.get('success', True)
        
        message = {
            'type': 'job_completed' if success else 'job_failed',
            'job_id': data['job_id'],
            'success': success,
            'result': data.get('result', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        websocket_fallback.broadcast(message, channel='jobs')
        
        logging_system.log("INFO", "Job completion notification sent",
                          job_id=data['job_id'],
                          success=success)
        
        return jsonify({
            "success": True,
            "message": "Completion notification sent"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to send job completion notification", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/ws/notify/system_status", methods=["POST"])
def notify_system_status():
    """
    Send system status update
    
    Request body:
    - status: System status object
    
    Requirements: 4.5
    """
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({
                "success": False,
                "error": "status is required"
            }), 400
        
        message = {
            'type': 'system_status',
            'status': data['status'],
            'timestamp': datetime.now().isoformat()
        }
        
        websocket_fallback.broadcast(message, channel='system')
        
        logging_system.log("DEBUG", "System status notification sent")
        
        return jsonify({
            "success": True,
            "message": "Status notification sent"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to send system status notification", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/ws/cleanup", methods=["POST"])
def cleanup_stale_clients():
    """
    Clean up stale WebSocket clients
    
    Request body:
    - timeout_minutes: Minutes of inactivity before cleanup (default: 5)
    
    Requirements: 4.5
    """
    try:
        data = request.get_json() or {}
        timeout_minutes = data.get('timeout_minutes', 5)
        
        removed_count = websocket_fallback.cleanup_stale_clients(timeout_minutes)
        
        logging_system.log("INFO", "Cleaned up stale WebSocket clients",
                          removed_count=removed_count)
        
        return jsonify({
            "success": True,
            "message": f"Removed {removed_count} stale clients",
            "removed_count": removed_count
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to cleanup stale clients", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Helper function to send WebSocket notifications from other parts of the application
def send_websocket_notification(event_type: str, data: dict, channel: str = None):
    """
    Helper function to send WebSocket notifications
    
    Args:
        event_type: Type of event
        data: Event data
        channel: Optional channel filter
    """
    try:
        message = {
            'type': event_type,
            **data,
            'timestamp': datetime.now().isoformat()
        }
        
        websocket_fallback.broadcast(message, channel=channel)
        
        logging_system.log("DEBUG", f"WebSocket notification sent: {event_type}")
    except Exception as e:
        logging_system.log_error(f"Failed to send WebSocket notification: {event_type}", exception=e)


# --- Export Preset Management API Endpoints ---

@app.route("/export/presets", methods=["GET"])
def get_export_presets():
    """
    Get all export presets
    
    Query parameters:
    - enabled_only: If true, only return enabled presets (optional)
    
    Requirements: 6.1, 6.2
    """
    try:
        enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
        
        presets = export_preset_manager.list_presets(enabled_only=enabled_only)
        
        presets_data = [preset.to_dict() for preset in presets]
        
        logging_system.log("INFO", "Export presets retrieved",
                          total_count=len(presets_data),
                          enabled_only=enabled_only)
        
        return jsonify({
            "success": True,
            "presets": presets_data,
            "count": len(presets_data)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get export presets", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/<string:name>", methods=["GET"])
def get_export_preset(name: str):
    """
    Get a specific export preset by name
    
    Path parameters:
    - name: Preset name
    
    Requirements: 6.1, 6.2
    """
    try:
        preset = export_preset_manager.get_preset(name)
        
        if preset is None:
            return jsonify({
                "success": False,
                "error": f"Preset '{name}' not found"
            }), 404
        
        logging_system.log("INFO", "Export preset retrieved", preset_name=name)
        
        return jsonify({
            "success": True,
            "preset": preset.to_dict()
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get export preset", exception=e, preset_name=name)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets", methods=["POST"])
def create_export_preset():
    """
    Create a new export preset
    
    Request body:
    - name: Preset name (required)
    - enabled: Whether preset is enabled (required)
    - format: Export format (JPEG, PNG, TIFF, DNG) (required)
    - quality: Quality 1-100 (required)
    - max_dimension: Maximum dimension in pixels (required)
    - color_space: Color space (sRGB, AdobeRGB, ProPhotoRGB) (required)
    - destination: Export destination folder (required)
    - Additional optional fields...
    
    Requirements: 6.1, 6.2
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'enabled', 'format', 'quality', 'max_dimension', 'color_space', 'destination']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Create preset
        try:
            preset = ExportPreset.from_dict(data)
        except (ValueError, TypeError) as e:
            return jsonify({
                "success": False,
                "error": f"Invalid preset data: {str(e)}"
            }), 400
        
        # Validate preset
        is_valid, error_msg = export_preset_manager.validate_preset(preset)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": f"Preset validation failed: {error_msg}"
            }), 400
        
        # Add preset
        success = export_preset_manager.add_preset(preset)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Preset '{preset.name}' already exists"
            }), 409
        
        # Save presets
        export_preset_manager.save()
        
        logging_system.log("INFO", "Export preset created", preset_name=preset.name)
        
        return jsonify({
            "success": True,
            "message": f"Preset '{preset.name}' created successfully",
            "preset": preset.to_dict()
        }), 201
        
    except Exception as e:
        logging_system.log_error("Failed to create export preset", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/<string:name>", methods=["PUT"])
def update_export_preset(name: str):
    """
    Update an existing export preset
    
    Path parameters:
    - name: Preset name
    
    Request body:
    - Fields to update (partial update supported)
    
    Requirements: 6.1, 6.2
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        # Check if preset exists
        preset = export_preset_manager.get_preset(name)
        if preset is None:
            return jsonify({
                "success": False,
                "error": f"Preset '{name}' not found"
            }), 404
        
        # Update preset
        success = export_preset_manager.update_preset(name, data)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Failed to update preset '{name}'"
            }), 400
        
        # Save presets
        export_preset_manager.save()
        
        # Get updated preset
        updated_preset = export_preset_manager.get_preset(name)
        
        logging_system.log("INFO", "Export preset updated", preset_name=name)
        
        return jsonify({
            "success": True,
            "message": f"Preset '{name}' updated successfully",
            "preset": updated_preset.to_dict()
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to update export preset", exception=e, preset_name=name)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/<string:name>", methods=["DELETE"])
def delete_export_preset(name: str):
    """
    Delete an export preset
    
    Path parameters:
    - name: Preset name
    
    Requirements: 6.1, 6.2
    """
    try:
        # Check if preset exists
        preset = export_preset_manager.get_preset(name)
        if preset is None:
            return jsonify({
                "success": False,
                "error": f"Preset '{name}' not found"
            }), 404
        
        # Delete preset
        success = export_preset_manager.delete_preset(name)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Failed to delete preset '{name}'"
            }), 400
        
        # Save presets
        export_preset_manager.save()
        
        logging_system.log("INFO", "Export preset deleted", preset_name=name)
        
        return jsonify({
            "success": True,
            "message": f"Preset '{name}' deleted successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to delete export preset", exception=e, preset_name=name)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/<string:name>/enable", methods=["POST"])
def enable_export_preset(name: str):
    """
    Enable an export preset
    
    Path parameters:
    - name: Preset name
    
    Requirements: 6.1, 6.2
    """
    try:
        success = export_preset_manager.enable_preset(name)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Preset '{name}' not found"
            }), 404
        
        # Save presets
        export_preset_manager.save()
        
        logging_system.log("INFO", "Export preset enabled", preset_name=name)
        
        return jsonify({
            "success": True,
            "message": f"Preset '{name}' enabled successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to enable export preset", exception=e, preset_name=name)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/<string:name>/disable", methods=["POST"])
def disable_export_preset(name: str):
    """
    Disable an export preset
    
    Path parameters:
    - name: Preset name
    
    Requirements: 6.1, 6.2
    """
    try:
        success = export_preset_manager.disable_preset(name)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Preset '{name}' not found"
            }), 404
        
        # Save presets
        export_preset_manager.save()
        
        logging_system.log("INFO", "Export preset disabled", preset_name=name)
        
        return jsonify({
            "success": True,
            "message": f"Preset '{name}' disabled successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to disable export preset", exception=e, preset_name=name)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/<string:source_name>/duplicate", methods=["POST"])
def duplicate_export_preset(source_name: str):
    """
    Duplicate an export preset
    
    Path parameters:
    - source_name: Source preset name
    
    Request body:
    - new_name: Name for the duplicated preset (required)
    
    Requirements: 6.1, 6.2
    """
    try:
        data = request.get_json()
        
        if not data or 'new_name' not in data:
            return jsonify({
                "success": False,
                "error": "new_name is required"
            }), 400
        
        new_name = data['new_name']
        
        success = export_preset_manager.duplicate_preset(source_name, new_name)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Failed to duplicate preset. Source '{source_name}' not found or target '{new_name}' already exists"
            }), 400
        
        # Save presets
        export_preset_manager.save()
        
        # Get duplicated preset
        duplicated_preset = export_preset_manager.get_preset(new_name)
        
        logging_system.log("INFO", "Export preset duplicated",
                          source_name=source_name,
                          new_name=new_name)
        
        return jsonify({
            "success": True,
            "message": f"Preset '{source_name}' duplicated to '{new_name}' successfully",
            "preset": duplicated_preset.to_dict()
        }), 201
        
    except Exception as e:
        logging_system.log_error("Failed to duplicate export preset", exception=e, source_name=source_name)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/validate", methods=["POST"])
def validate_export_preset():
    """
    Validate an export preset without saving
    
    Request body:
    - Preset data to validate
    
    Requirements: 6.1, 6.2
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        # Create preset for validation
        try:
            preset = ExportPreset.from_dict(data)
        except (ValueError, TypeError) as e:
            return jsonify({
                "success": False,
                "valid": False,
                "error": f"Invalid preset data: {str(e)}"
            }), 200
        
        # Validate preset
        is_valid, error_msg = export_preset_manager.validate_preset(preset)
        
        if is_valid:
            return jsonify({
                "success": True,
                "valid": True,
                "message": "Preset is valid"
            }), 200
        else:
            return jsonify({
                "success": True,
                "valid": False,
                "error": error_msg
            }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to validate export preset", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/stats", methods=["GET"])
def get_export_preset_stats():
    """
    Get export preset statistics
    
    Requirements: 6.1, 6.2
    """
    try:
        total_count = export_preset_manager.get_preset_count()
        enabled_count = export_preset_manager.get_enabled_preset_count()
        
        presets = export_preset_manager.list_presets()
        
        # Group by format
        format_distribution = {}
        for preset in presets:
            format_distribution[preset.format] = format_distribution.get(preset.format, 0) + 1
        
        # Group by color space
        color_space_distribution = {}
        for preset in presets:
            color_space_distribution[preset.color_space] = color_space_distribution.get(preset.color_space, 0) + 1
        
        logging_system.log("INFO", "Export preset stats retrieved")
        
        return jsonify({
            "success": True,
            "stats": {
                "total_presets": total_count,
                "enabled_presets": enabled_count,
                "disabled_presets": total_count - enabled_count,
                "format_distribution": format_distribution,
                "color_space_distribution": color_space_distribution
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get export preset stats", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/export", methods=["GET"])
def export_presets_to_file():
    """
    Export all presets to a JSON file
    
    Query parameters:
    - path: Export file path (optional, defaults to backup location)
    
    Requirements: 6.1, 6.2
    """
    try:
        export_path = request.args.get('path')
        
        if export_path is None:
            # Use default backup location
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = pathlib.Path(__file__).parent / "config" / f"export_presets_backup_{timestamp}.json"
        else:
            export_path = pathlib.Path(export_path)
        
        export_preset_manager.export_presets(export_path)
        
        logging_system.log("INFO", "Export presets exported to file", export_path=str(export_path))
        
        return jsonify({
            "success": True,
            "message": "Presets exported successfully",
            "export_path": str(export_path)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to export presets to file", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/export/presets/import", methods=["POST"])
def import_presets_from_file():
    """
    Import presets from a JSON file
    
    Request body:
    - path: Import file path (required)
    - merge: Whether to merge with existing presets (optional, default: true)
    
    Requirements: 6.1, 6.2
    """
    try:
        data = request.get_json()
        
        if not data or 'path' not in data:
            return jsonify({
                "success": False,
                "error": "path is required"
            }), 400
        
        import_path = pathlib.Path(data['path'])
        merge = data.get('merge', True)
        
        if not import_path.exists():
            return jsonify({
                "success": False,
                "error": f"Import file not found: {import_path}"
            }), 404
        
        imported_count = export_preset_manager.import_presets(import_path, merge=merge)
        
        # Save presets
        export_preset_manager.save()
        
        logging_system.log("INFO", "Export presets imported from file",
                          import_path=str(import_path),
                          imported_count=imported_count,
                          merge=merge)
        
        return jsonify({
            "success": True,
            "message": f"Imported {imported_count} presets successfully",
            "imported_count": imported_count
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to import presets from file", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# --- Auto Export API Endpoints ---

@app.route("/export/auto/trigger", methods=["POST"])
def trigger_auto_export():
    """
    Trigger automatic export for an approved photo
    
    Request body:
    - photo_id: ID of the approved photo (required)
    
    Requirements: 6.1, 6.4
    """
    try:
        data = request.get_json()
        
        if not data or 'photo_id' not in data:
            return jsonify({
                "success": False,
                "error": "photo_id is required"
            }), 400
        
        photo_id = data['photo_id']
        
        # Trigger auto-export
        export_jobs = auto_export_engine.trigger_auto_export(photo_id)
        
        logging_system.log("INFO", "Auto-export triggered",
                          photo_id=photo_id,
                          job_count=len(export_jobs))
        
        return jsonify({
            "success": True,
            "message": f"Created {len(export_jobs)} export jobs",
            "job_count": len(export_jobs),
            "jobs": [job.to_dict() for job in export_jobs]
        }), 200
        
    except ValueError as e:
        logging_system.log_error("Failed to trigger auto-export", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logging_system.log_error("Failed to trigger auto-export", exception=e)
        return jsonify({
            "success": False,
            "error": f"Failed to trigger auto-export: {e}"
        }), 500


@app.route("/export/auto/multiple", methods=["POST"])
def export_multiple_formats():
    """
    Export a photo in multiple formats simultaneously
    
    Request body:
    - photo_id: ID of the photo to export (required)
    - preset_names: List of preset names to use (required)
    
    Requirements: 6.1, 6.4
    """
    try:
        data = request.get_json()
        
        if not data or 'photo_id' not in data or 'preset_names' not in data:
            return jsonify({
                "success": False,
                "error": "photo_id and preset_names are required"
            }), 400
        
        photo_id = data['photo_id']
        preset_names = data['preset_names']
        
        if not isinstance(preset_names, list):
            return jsonify({
                "success": False,
                "error": "preset_names must be a list"
            }), 400
        
        # Export in multiple formats
        export_jobs = auto_export_engine.export_multiple_formats(photo_id, preset_names)
        
        logging_system.log("INFO", "Multiple format export triggered",
                          photo_id=photo_id,
                          preset_count=len(preset_names),
                          job_count=len(export_jobs))
        
        return jsonify({
            "success": True,
            "message": f"Created {len(export_jobs)} export jobs",
            "job_count": len(export_jobs),
            "jobs": [job.to_dict() for job in export_jobs]
        }), 200
        
    except ValueError as e:
        logging_system.log_error("Failed to export multiple formats", exception=e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logging_system.log_error("Failed to export multiple formats", exception=e)
        return jsonify({
            "success": False,
            "error": f"Failed to export multiple formats: {e}"
        }), 500


@app.route("/export/auto/queue", methods=["GET"])
def get_export_queue():
    """
    Get export queue status
    
    Returns queue statistics and pending/processing jobs
    
    Requirements: 6.1, 6.4
    """
    try:
        status = auto_export_engine.get_export_queue_status()
        
        logging_system.log("DEBUG", "Export queue status retrieved",
                          pending_count=status['pending_count'],
                          processing_count=status['processing_count'])
        
        return jsonify({
            "success": True,
            **status
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get export queue status", exception=e)
        return jsonify({
            "success": False,
            "error": f"Failed to get queue status: {e}"
        }), 500


@app.route("/export/auto/job/<string:job_id>", methods=["GET"])
def get_export_job(job_id: str):
    """
    Get export job details
    
    Path parameters:
    - job_id: ID of the export job
    
    Requirements: 6.1, 6.4
    """
    try:
        job = auto_export_engine.get_export_job(job_id)
        
        if not job:
            return jsonify({
                "success": False,
                "error": f"Export job not found: {job_id}"
            }), 404
        
        logging_system.log("DEBUG", "Export job retrieved", job_id=job_id)
        
        return jsonify({
            "success": True,
            "job": job.to_dict()
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get export job", exception=e, job_id=job_id)
        return jsonify({
            "success": False,
            "error": f"Failed to get export job: {e}"
        }), 500


@app.route("/export/auto/job/next", methods=["GET"])
def get_next_export_job():
    """
    Get the next export job from the queue
    
    Returns the oldest pending export job and its Lightroom configuration
    
    Requirements: 6.1, 6.4
    """
    try:
        job = auto_export_engine.get_next_export_job()
        
        if not job:
            return jsonify({
                "success": True,
                "message": "No pending export jobs"
            }), 200
        
        # Get Lightroom export configuration
        config = auto_export_engine.get_export_config_for_lightroom(job.id)
        
        if not config:
            return jsonify({
                "success": False,
                "error": "Failed to generate export configuration"
            }), 500
        
        # Process the job (move to processing state)
        success, error = auto_export_engine.process_export_job(job.id)
        
        if not success:
            return jsonify({
                "success": False,
                "error": error
            }), 500
        
        logging_system.log("INFO", "Next export job retrieved", job_id=job.id)
        
        return jsonify({
            "success": True,
            "job": job.to_dict(),
            "config": config
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get next export job", exception=e)
        return jsonify({
            "success": False,
            "error": f"Failed to get next export job: {e}"
        }), 500


@app.route("/export/auto/job/<string:job_id>/complete", methods=["POST"])
def complete_export_job(job_id: str):
    """
    Mark an export job as completed
    
    Path parameters:
    - job_id: ID of the export job
    
    Request body:
    - success: Whether the export was successful (required)
    - error_message: Optional error message if failed
    
    Requirements: 6.1, 6.4
    """
    try:
        data = request.get_json()
        
        if not data or 'success' not in data:
            return jsonify({
                "success": False,
                "error": "success field is required"
            }), 400
        
        success = data['success']
        error_message = data.get('error_message')
        
        # Complete the job
        result = auto_export_engine.complete_export_job(job_id, success, error_message)
        
        if not result:
            return jsonify({
                "success": False,
                "error": f"Export job not found: {job_id}"
            }), 404
        
        logging_system.log("INFO", "Export job completed",
                          job_id=job_id,
                          success=success)
        
        return jsonify({
            "success": True,
            "message": "Export job completed successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to complete export job", exception=e, job_id=job_id)
        return jsonify({
            "success": False,
            "error": f"Failed to complete export job: {e}"
        }), 500


@app.route("/export/auto/job/<string:job_id>/cancel", methods=["POST"])
def cancel_export_job(job_id: str):
    """
    Cancel an export job
    
    Path parameters:
    - job_id: ID of the export job to cancel
    
    Requirements: 6.1, 6.4
    """
    try:
        result = auto_export_engine.cancel_export_job(job_id)
        
        if not result:
            return jsonify({
                "success": False,
                "error": f"Export job not found or cannot be cancelled: {job_id}"
            }), 404
        
        logging_system.log("INFO", "Export job cancelled", job_id=job_id)
        
        return jsonify({
            "success": True,
            "message": "Export job cancelled successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to cancel export job", exception=e, job_id=job_id)
        return jsonify({
            "success": False,
            "error": f"Failed to cancel export job: {e}"
        }), 500


@app.route("/export/auto/queue/clear", methods=["POST"])
def clear_export_queue():
    """
    Clear all pending export jobs
    
    Requirements: 6.1, 6.4
    """
    try:
        count = auto_export_engine.clear_export_queue()
        
        logging_system.log("WARNING", "Export queue cleared", cleared_count=count)
        
        return jsonify({
            "success": True,
            "message": f"Cleared {count} export jobs",
            "cleared_count": count
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to clear export queue", exception=e)
        return jsonify({
            "success": False,
            "error": f"Failed to clear export queue: {e}"
        }), 500


@app.route("/export/auto/filename/generate", methods=["POST"])
def generate_export_filename():
    """
    Generate automatic filename for a photo and preset
    
    Request body:
    - photo_id: ID of the photo (required)
    - preset_name: Name of the export preset (required)
    - sequence_number: Optional sequence number
    
    Requirements: 6.4
    """
    try:
        data = request.get_json()
        
        if not data or 'photo_id' not in data or 'preset_name' not in data:
            return jsonify({
                "success": False,
                "error": "photo_id and preset_name are required"
            }), 400
        
        photo_id = data['photo_id']
        preset_name = data['preset_name']
        sequence_number = data.get('sequence_number')
        
        # Get photo and preset
        db_session = get_session()
        try:
            from models.database import Photo
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({
                    "success": False,
                    "error": f"Photo not found: {photo_id}"
                }), 404
            
            preset = export_preset_manager.get_preset(preset_name)
            
            if not preset:
                return jsonify({
                    "success": False,
                    "error": f"Preset not found: {preset_name}"
                }), 404
            
            # Generate filename
            filename = auto_export_engine.generate_filename(photo, preset, sequence_number)
            
            # Get full export path
            export_path = auto_export_engine.get_export_path(photo, preset, sequence_number)
            
            logging_system.log("DEBUG", "Export filename generated",
                              photo_id=photo_id,
                              preset_name=preset_name,
                              filename=filename)
            
            return jsonify({
                "success": True,
                "filename": filename,
                "export_path": str(export_path)
            }), 200
            
        finally:
            db_session.close()
        
    except Exception as e:
        logging_system.log_error("Failed to generate export filename", exception=e)
        return jsonify({
            "success": False,
            "error": f"Failed to generate filename: {e}"
        }), 500




# --- Photo Approval API Endpoints ---

@app.route("/photos/<int:photo_id>/approve", methods=["POST"])
def approve_photo(photo_id: int):
    """
    Approve a photo and optionally trigger auto-export
    
    Path parameters:
    - photo_id: ID of the photo to approve
    
    Request body:
    - auto_export: Whether to trigger auto-export (optional, default: true)
    
    Requirements: 5.3, 6.1, 6.4
    """
    try:
        data = request.get_json() or {}
        auto_export = data.get('auto_export', True)
        
        # Get photo from database
        db_session = get_session()
        try:
            from models.database import Photo
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({
                    "success": False,
                    "error": f"Photo not found: {photo_id}"
                }), 404
            
            # Update photo approval status
            photo.approved = True
            photo.approved_at = datetime.now()
            photo.status = 'completed'
            db_session.commit()
            
            logging_system.log("INFO", "Photo approved",
                              photo_id=photo_id,
                              auto_export=auto_export)
            
            # Trigger auto-export if enabled
            export_jobs = []
            if auto_export:
                try:
                    export_jobs = auto_export_engine.trigger_auto_export(photo_id, db_session)
                    logging_system.log("INFO", "Auto-export triggered after approval",
                                      photo_id=photo_id,
                                      job_count=len(export_jobs))
                except Exception as e:
                    logging_system.log_error("Failed to trigger auto-export after approval",
                                            exception=e,
                                            photo_id=photo_id)
                    # Don't fail the approval if auto-export fails
            
            return jsonify({
                "success": True,
                "message": "Photo approved successfully",
                "photo": photo.to_dict(),
                "export_jobs": [job.to_dict() for job in export_jobs] if export_jobs else []
            }), 200
            
        finally:
            db_session.close()
        
    except Exception as e:
        logging_system.log_error("Failed to approve photo", exception=e, photo_id=photo_id)
        return jsonify({
            "success": False,
            "error": f"Failed to approve photo: {e}"
        }), 500


@app.route("/photos/<int:photo_id>/reject", methods=["POST"])
def reject_photo(photo_id: int):
    """
    Reject a photo
    
    Path parameters:
    - photo_id: ID of the photo to reject
    
    Request body:
    - reason: Rejection reason (optional)
    
    Requirements: 5.4
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        # Get photo from database
        db_session = get_session()
        try:
            from models.database import Photo
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({
                    "success": False,
                    "error": f"Photo not found: {photo_id}"
                }), 404
            
            # Update photo rejection status
            photo.approved = False
            photo.status = 'rejected'
            photo.rejection_reason = reason
            db_session.commit()
            
            logging_system.log("INFO", "Photo rejected",
                              photo_id=photo_id,
                              reason=reason)
            
            return jsonify({
                "success": True,
                "message": "Photo rejected successfully",
                "photo": photo.to_dict()
            }), 200
            
        finally:
            db_session.close()
        
    except Exception as e:
        logging_system.log_error("Failed to reject photo", exception=e, photo_id=photo_id)
        return jsonify({
            "success": False,
            "error": f"Failed to reject photo: {e}"
        }), 500


@app.route("/photos/approval/queue", methods=["GET"])
def get_approval_queue():
    """
    Get photos pending approval
    
    Query parameters:
    - limit: Maximum number of photos to return (optional, default: 50)
    - offset: Offset for pagination (optional, default: 0)
    
    Requirements: 5.1, 5.2
    """
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Get photos from database
        db_session = get_session()
        try:
            from models.database import Photo
            
            # Query photos that are completed but not yet approved
            photos = db_session.query(Photo).filter(
                Photo.status == 'completed',
                Photo.approved == False
            ).order_by(Photo.import_time.desc()).limit(limit).offset(offset).all()
            
            total_count = db_session.query(Photo).filter(
                Photo.status == 'completed',
                Photo.approved == False
            ).count()
            
            logging_system.log("DEBUG", "Approval queue retrieved",
                              count=len(photos),
                              total_count=total_count)
            
            return jsonify({
                "success": True,
                "photos": [photo.to_dict() for photo in photos],
                "count": len(photos),
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }), 200
            
        finally:
            db_session.close()
        
    except Exception as e:
        logging_system.log_error("Failed to get approval queue", exception=e)
        return jsonify({
            "success": False,
            "error": f"Failed to get approval queue: {e}"
        }), 500


