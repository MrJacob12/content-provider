from flask import Flask, send_from_directory, jsonify, abort, request, Response
import os
import json
import hashlib

import dotenv
dotenv.load_dotenv()

app = Flask(__name__)
FILES_DIR = os.getenv("FILES_DIR") or ""
PROJECT_DATA = json.loads(open(f'{os.getenv("PROJECT_DATA")}', "r").read())
PORT = int(os.getenv("PORT") or "") or 5000

if not FILES_DIR and FILES_DIR is not None and not os.path.exists(FILES_DIR):
    raise ValueError("FILES_DIR is not set in .env")
if not PROJECT_DATA and PROJECT_DATA is not None and not os.path.exists(PROJECT_DATA):
    raise ValueError("PROJECT_DATA is not set in .env")

# Define Content Security Policy
csp_policy = {
    "default-src": "'self'",
    "connect-src": ["'self'", f'{os.getenv("API_URL")}'],
}


# Helper function to format CSP header
def generate_csp_header(policy):
    header = "; ".join([f"{key} {' '.join(value)}" for key, value in policy.items()])
    return header


# Add Content Security Policy headers to all responses
@app.after_request
def add_security_headers(response):
    csp_header = generate_csp_header(csp_policy)
    response.headers["Content-Security-Policy"] = csp_header
    return response


@app.route("/files/", methods=["POST"])
def send_file():
    data = request.get_json()
    project = data.get("project")
    filename = data.get("filename")
    if project not in PROJECT_DATA.keys():
        abort(404)
    file_path = os.path.join(FILES_DIR, PROJECT_DATA[project], filename)
    if os.path.exists(file_path):
        return send_from_directory(
            os.path.dirname(file_path), os.path.basename(file_path)
        )
    else:
        abort(404)


@app.route("/files_info/<project>/")
def send_files_info(project):
    if project not in PROJECT_DATA.keys():
        abort(404)
    info_path = os.path.join(FILES_DIR, PROJECT_DATA[project], "files_info.json")
    if os.path.exists(info_path):
        with open(info_path, "r") as f:
            files_info = json.load(f)

        # Add project name to files_info
        files_info["project_name"] = PROJECT_DATA[project]

        return jsonify(files_info)
    else:
        abort(404)


@app.route("/status/")
def status():
    return jsonify({"status": "ok"})


@app.route("/update_info/")
def update_info():
    checksum = hashlib.md5()
    with open(f"{FILES_DIR}/deploy/game_updater.exe", "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            checksum.update(chunk)
    checksum = checksum.hexdigest()
    return jsonify({"version": checksum})


@app.route("/download_update/")
def download_update():
    return send_from_directory(f"{FILES_DIR}/deploy", "game_updater.exe")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT,
        ssl_context=(
            os.getenv("SSL_CERT"),
            os.getenv("SSL_KEY"),
        ),
    )
