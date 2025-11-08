# Junmai Auto Development Lightroom Plugin

This project automates Adobe Lightroom Classic development settings using a Large Language Model (LLM). It consists of a Lightroom plugin (written in Lua) and a local bridge server (written in Python with Flask) that communicates with an LLM hosted locally via Ollama.

## Architecture

```
[Ollama LLM] ⇄ [Local Bridge (Python/Flask)] ⇄ [Lightroom Plugin (Lua)]
```

-   **Lightroom Plugin**: Sends requests to the bridge and applies development settings to the selected photo.
-   **Local Bridge**: Receives requests from the plugin, formats a prompt for the LLM, gets the development settings (as JSON), and serves them to the plugin.
-   **Ollama**: Hosts the local LLM that generates the development settings.

## Features

-   Non-destructive editing via Virtual Copies and Snapshots.
-   Background polling for new development jobs.
-   Simple UI for status and manual job checking.
-   Desktop GUI for easy prompt submission.

## Setup

### 1. Prerequisites

-   Adobe Lightroom Classic 12.0 or later.
-   [Ollama](https://ollama.ai/) installed and running.
-   A compatible LLM pulled via Ollama (e.g., `ollama pull llama3.1:8B-instruct`).
-   Python 3.8 or later.

### 2. Local Bridge Server Setup

1.  **Navigate to the `local_bridge` directory:**
    ```bash
    cd local_bridge
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the server:**
    ```bash
    python app.py
    ```
    The server will start on `http://127.0.0.1:5100`.

### 3. Lightroom Plugin Setup

1.  **Open Lightroom Classic.**
2.  Go to **File > Plug-in Manager**.
3.  Click the **"Add"** button.
4.  Navigate to this project's directory and select the `JunmaiAutoDev.lrdevplugin` folder.
5.  The plugin will be added and enabled.

## Usage

### 1. Using the Desktop GUI

1.  **Ensure the Local Bridge Server is running.**
2.  **Run the GUI:**
    ```bash
    python gui.py
    ```
3.  Enter your development prompt in the text box (e.g., "A warm, vintage look for a sunny portrait").
4.  Click **"Submit to Lightroom"**.

### 2. In Lightroom Classic

1.  Select a photo in the Library or Develop module.
2.  The plugin will automatically poll for the job you submitted and apply the settings.
3.  A new virtual copy named "JunmaiAutoDev Edit" will be created with the settings applied. The original photo remains untouched.
4.  You can also manually check for a job by going to **Library > Plug-in Extras > Junmai AutoDev Control Panel**.

---

This project is a proof-of-concept and is under active development.
