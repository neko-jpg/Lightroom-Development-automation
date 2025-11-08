# gui.py
#
# A simple Tkinter-based GUI for submitting prompts to the Junmai AutoDev local bridge server.

import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import json

API_URL = "http://127.0.0.1:5100/job"

def submit_prompt():
    """Gets the prompt from the text area and submits it to the API."""
    prompt_text = text_area.get("1.0", tk.END).strip()

    if not prompt_text:
        messagebox.showwarning("Input Error", "Prompt cannot be empty.")
        return

    payload = {"prompt": prompt_text}

    try:
        # Change button to show "Submitting..."
        submit_button.config(text="Submitting...", state=tk.DISABLED)
        window.update_idletasks()

        response = requests.post(API_URL, json=payload, timeout=10)

        response.raise_for_status() # Raises an exception for 4xx or 5xx status codes

        job_info = response.json()
        job_id = job_info.get("jobId", "N/A")

        messagebox.showinfo("Success", f"Job submitted successfully!\\nJob ID: {job_id}")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("API Error", f"Failed to submit job: {e}")

    finally:
        # Restore button
        submit_button.config(text="Submit to Lightroom", state=tk.NORMAL)


# --- GUI Setup ---
window = tk.Tk()
window.title("Junmai AutoDev Prompt Submitter")
window.geometry("500x350")

# Main frame
main_frame = tk.Frame(window, padx=10, pady=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# Prompt label
prompt_label = tk.Label(main_frame, text="Enter your development prompt below:")
prompt_label.pack(anchor="w", pady=(0, 5))

# Text area with scrollbar
text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, width=60)
text_area.pack(fill=tk.BOTH, expand=True)
text_area.focus()

# Submit button
submit_button = tk.Button(main_frame, text="Submit to Lightroom", command=submit_prompt)
submit_button.pack(pady=(10, 0), fill=tk.X)

# Start the GUI event loop
window.mainloop()
