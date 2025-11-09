# main.py
import threading
import sys
import os
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests

# When running as a script, the project root is the current directory,
# so the 'local_bridge' package can be imported directly.
# For PyInstaller, we will need to ensure all modules are correctly bundled.
from local_bridge import app as flask_app_module

def run_server():
    """Runs the Flask server in a dedicated thread."""
    print("Starting Flask server...")
    try:
        # Run the Flask app without debug mode or the auto-reloader,
        # which are unsuitable for a packaged application.
        flask_app_module.app.run(host='127.0.0.1', port=5100, debug=False, use_reloader=False)
    except Exception as e:
        # This will be printed to the console if the server fails to start.
        print(f"Error starting Flask server: {e}")

def start_gui():
    """Creates and runs the main Tkinter GUI."""
    API_URL = "http://127.0.0.1:5100/job"

    def submit_prompt():
        """Handles the prompt submission via the API."""
        prompt_text = text_area.get("1.0", tk.END).strip()
        if not prompt_text:
            messagebox.showwarning("Input Error", "Prompt cannot be empty.")
            return

        payload = {"prompt": prompt_text}
        submit_button.config(text="Submitting...", state=tk.DISABLED)
        window.update_idletasks()

        try:
            # A longer timeout is better as the LLM generation can be slow.
            response = requests.post(API_URL, json=payload, timeout=60)
            response.raise_for_status()
            job_info = response.json()
            job_id = job_info.get("jobId", "N/A")
            messagebox.showinfo("Success", f"Job submitted successfully!\nJob ID: {job_id}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Could not submit job. Is the server running?\n\nDetails: {e}")
        finally:
            submit_button.config(text="Submit to Lightroom", state=tk.NORMAL)

    # --- GUI Layout ---
    window = tk.Tk()
    window.title("Junmai AutoDev v1.0")
    window.geometry("500x350")
    main_frame = tk.Frame(window, padx=10, pady=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    prompt_label = tk.Label(main_frame, text="Enter your development prompt:")
    prompt_label.pack(anchor="w", pady=(0, 5))

    text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, width=60)
    text_area.pack(fill=tk.BOTH, expand=True)
    text_area.focus()

    submit_button = tk.Button(main_frame, text="Submit to Lightroom", command=submit_prompt)
    submit_button.pack(pady=(10, 0), fill=tk.X)

    status_bar = tk.Label(window, text="Server status: Initializing...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def check_server_status():
        """Periodically pings a server endpoint to check its status."""
        try:
            # Use a lightweight, existing endpoint for the health check.
            requests.get("http://127.0.0.1:5100/config", timeout=1)
            status_bar.config(text="Server status: Running", fg="green")
        except requests.exceptions.ConnectionError:
            status_bar.config(text="Server status: Not responding", fg="red")

        # Schedule the next check.
        window.after(5000, check_server_status)

    # Start checking the server status shortly after the GUI loads.
    window.after(2000, check_server_status)

    # Start the Tkinter event loop. This blocks until the window is closed.
    window.mainloop()

if __name__ == '__main__':
    print("Starting Junmai AutoDev Application...")

    # Run the Flask server in a background thread.
    # Making it a daemon thread ensures it automatically shuts down
    # when the main application (GUI) exits.
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # The GUI must run in the main thread for OS compatibility (especially macOS).
    start_gui()

    print("GUI closed. Application shutting down.")
