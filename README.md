# Clipboard Vault

A local Windows clipboard history app built with Flask. Clipboard Vault watches copied text in the background, stores it in a local SQLite database, and provides a browser interface for searching, filtering, copying, and deleting saved entries.

## Features

- Automatically captures new text copied to the Windows clipboard
- Stores clipboard history locally in SQLite
- Search entries by text
- Filter entries by date
- Add entries manually from the web interface
- Delete saved entries
- Works as a local progressive web app

## Requirements

- Windows
- Python 3.10 or newer
- A modern web browser

The clipboard watcher uses `pywin32`, while the web server uses Flask.

## Installation

1. Clone the repository and open its folder:

	```powershell
	git clone https://github.com/raghuthakur7881-crypto/clip.git
	cd clip
	```

2. Create and activate a virtual environment:

	```powershell
	py -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

3. Install the dependencies:

	```powershell
	pip install -r requirements.txt
	pip install pywin32
	```

## Run Locally

Start the Flask server:

```powershell
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. Keep the server running while using the clipboard watcher.

The application creates `clipboard_data.db` in the project directory on first startup. This file contains your local clipboard history and is not uploaded by the application.

## API

### List entries

```text
GET /api/entries
```

Optional query parameters:

- `q`: search clipboard text
- `date`: filter by date using `YYYY-MM-DD`

### Add an entry

```text
POST /api/entries
Content-Type: application/json

{"text": "Example clipboard text"}
```

### Delete an entry

```text
DELETE /api/entries/<entry_id>
```

## Project Structure

```text
app.py                  Flask application and clipboard watcher
requirements.txt        Python dependencies
templates/index.html    Web interface
static/script.js        Frontend behavior
static/style.css        Application styles
static/manifest.json    Progressive web app metadata
static/service-worker.js
								Service worker for the web app
```

## Notes

- Clipboard contents stay on the local machine in SQLite.
- The clipboard watcher is enabled only on Windows.
- The development server binds to `127.0.0.1:5000` and is intended for local use.
