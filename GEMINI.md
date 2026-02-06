# GEMINI.md

## Project Overview

This project is a feature-rich Telegram bot written in Python. The bot serves as a personal assistant, allowing users to interact with the underlying system through a Telegram chat interface. It supports text and voice commands, can execute shell commands (including with `sudo`), and integrates with an AI for question answering. The bot also includes text-to-speech and speech-to-text capabilities.

The main components of the project are:

*   **`bot.py`**: The main bot script that handles Telegram messages, authentication, command parsing, and execution.
*   **`ask_ai`**: A shell script that acts as a wrapper to an external AI service.
*   **`transcribe.py`**: A Python script that uses the `whisper` library to transcribe voice messages.
*   **`tospeech.py`**: A Python script that uses various text-to-speech engines to generate voice messages.
*   **`env.example`**: An example environment file that lists the required configuration variables.
*   **`aliases.json` and `builtin_aliases.json`**: Files for managing command aliases.

## Building and Running

1.  **Install Dependencies:** The project uses a `venv` for managing dependencies. The required packages are listed in the `venv_old/lib/python3.12/site-packages` directory. A `requirements.txt` file would be helpful here. Based on the file listing, the following command might work to install the dependencies:
    ```bash
    pip install -r requirements.txt 
    ```
    *TODO: Create a `requirements.txt` file from the `venv_old` directory.*

2.  **Set up Environment Variables:** Copy `env.example` to a `.env` file and fill in the required values:
    ```bash
    cp env.example .env
    ```
    The `.env` file should contain the following variables:
    *   `API_KEY`: Your Telegram bot API key.
    *   `PASSWORD`: The password for authorizing users.
    *   `SUDO_PASSWORD`: Your Linux user password for running `sudo` commands.
    *   `DISPLAY`: The display server address (e.g., `:0.0`).
    *   `DBUS_SESSION_BUS_ADDRESS`: The D-Bus session bus address.
    *   `VOICE_EN`: The English voice for text-to-speech.
    *   `VOICE_ES`: The Spanish voice for text-to-speech.

3.  **Run the Bot:**
    ```bash
    python bot.py
    ```

## Development Conventions

*   **Virtual Environment:** The project uses a Python virtual environment to manage dependencies.
*   **Configuration:** The bot is configured through environment variables.
*   **Modular Design:** The bot is broken down into several scripts, each with a specific responsibility (e.g., `transcribe.py`, `tospeech.py`).
*   **Logging:** The bot uses the `logging` module to log messages to a file.
*   **Aliases:** The bot supports both built-in and user-defined command aliases, which are stored in JSON files.
