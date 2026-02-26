import os
import time
import hmac
import hashlib
import secrets
import shutil
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-toctou-secret-key')

UPLOAD_FOLDER = '/app/uploads'
ALLOWED_EXTENSIONS = {'txt', 'log', 'csv'}
MAX_FILE_SIZE = 1024  # 1KB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def generate_flag(content_hash, content_length):
    """
    Generate dynamic flag based on successfully exfiltrated content.

    Flag proves:
    - File was actually read (content hash)
    - TOCTOU exploit succeeded (got sensitive file, not original)
    """
    data = f"toctou:{content_hash}:{content_length}:{int(time.time())}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]

    return f"S7BEN{{toctou_file_race_{flag_hash}}}"

def allowed_file(filename):
    """Check if filename has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(filepath):
    """Validate file before processing."""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            return False, "File does not exist"

        # Check extension
        filename = os.path.basename(filepath)
        if not allowed_file(filename):
            return False, f"Invalid file extension. Allowed: {ALLOWED_EXTENSIONS}"

        # Check for path traversal
        if '..' in filepath:
            return False, "Path traversal detected"

        # Check file size
        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Max size: {MAX_FILE_SIZE} bytes"

        # Note: We check if it's a regular file, but symlinks can appear as files
        # This is where the vulnerability starts
        if not os.path.isfile(filepath):
            return False, "Not a regular file"

        return True, "Validation passed"

    except Exception as e:
        return False, f"Validation error: {str(e)}"

def process_file(filepath, file_id):
    """Process the file."""
    try:
        # Read file content
        with open(filepath, 'r') as f:
            content = f.read()

        # Calculate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        content_length = len(content)

        # Check if this is the flag file (indicates successful TOCTOU)
        is_flag_file = '/flag.txt' in os.path.realpath(filepath)

        # If symlink or path changed, detect TOCTOU
        real_path = os.path.realpath(filepath)
        expected_path = os.path.realpath(f"{UPLOAD_FOLDER}/{file_id}/file.txt")

        toctou_detected = (real_path != expected_path) or is_flag_file

        result = {
            "status": "success",
            "file_id": file_id,
            "content_preview": content[:200] if len(content) <= 200 else content[:200] + "...",
            "content_length": content_length,
            "content_hash": content_hash,
            "real_path": real_path,
            "expected_path": expected_path
        }

        if toctou_detected:
            # Generate dynamic flag as proof of exploitation
            flag = generate_flag(content_hash, content_length)

            result.update({
                "exploitation_detected": True,
                "toctou_proven": True,
                "message": "File content has changed since validation.",
                "flag": flag,
                "full_content": content  # Include full exfiltrated content
            })

        return result, 200

    except Exception as e:
        return {
            "status": "error",
            "message": f"Processing error: {str(e)}",
            "hint": "File may have been deleted or access denied"
        }, 500

@app.route('/')
def index():
    """Homepage with upload interface"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload a file and return file_id"""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({
                "status": "error",
                "message": f"Invalid file type. Allowed: {ALLOWED_EXTENSIONS}"
            }), 400

        # Generate unique file ID
        file_id = secrets.token_hex(16)
        file_dir = os.path.join(UPLOAD_FOLDER, file_id)
        os.makedirs(file_dir, exist_ok=True)

        # Save file
        filepath = os.path.join(file_dir, secure_filename(file.filename))
        file.save(filepath)

        return jsonify({
            "status": "success",
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
            "next_step": f"Call /validate/{file_id} to validate, then /process/{file_id} to process"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/validate/<file_id>', methods=['POST'])
def validate_endpoint(file_id):
    """Validate uploaded file and return validation token."""
    try:
        file_dir = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(file_dir):
            return jsonify({"status": "error", "message": "File ID not found"}), 404

        # Find the uploaded file
        files = os.listdir(file_dir)
        if not files:
            return jsonify({"status": "error", "message": "No file in upload"}), 404

        filepath = os.path.join(file_dir, files[0])

        # Validate file
        valid, message = validate_file(filepath)

        if not valid:
            return jsonify({
                "status": "validation_failed",
                "message": message,
                "file_id": file_id
            }), 400

        # Generate validation token
        validation_token = hmac.new(
            FLAG_SECRET.encode(),
            f"{file_id}:{int(time.time())}".encode(),
            hashlib.sha256
        ).hexdigest()

        return jsonify({
            "status": "validation_passed",
            "message": message,
            "file_id": file_id,
            "validation_token": validation_token,
            "next_step": f"Call /process/{file_id} with this token"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/process/<file_id>', methods=['POST'])
def process_endpoint(file_id):
    """Process validated file."""
    try:
        # Verify validation token
        token = request.json.get('validation_token') if request.json else None

        if not token:
            return jsonify({
                "status": "error",
                "message": "Validation token required",
                "hint": "Call /validate first"
            }), 400

        file_dir = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(file_dir):
            return jsonify({"status": "error", "message": "File ID not found"}), 404

        # Find the file
        files = os.listdir(file_dir)
        if not files:
            return jsonify({"status": "error", "message": "No file in upload"}), 404

        filepath = os.path.join(file_dir, files[0])

        # Simulate I/O processing delay
        time.sleep(0.2)

        # TIME OF USE - Process the file
        result, status_code = process_file(filepath, file_id)

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/files')
def list_files():
    """List all uploaded files"""
    try:
        files = []
        for file_id in os.listdir(UPLOAD_FOLDER):
            file_dir = os.path.join(UPLOAD_FOLDER, file_id)
            if os.path.isdir(file_dir):
                file_list = os.listdir(file_dir)
                if file_list:
                    files.append({
                        "file_id": file_id,
                        "filename": file_list[0],
                        "path": os.path.join(file_dir, file_list[0])
                    })

        return jsonify({
            "status": "success",
            "files": files,
            "count": len(files)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/status/<file_id>')
def file_status(file_id):
    """Get file status and metadata"""
    try:
        file_dir = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(file_dir):
            return jsonify({"status": "error", "message": "File ID not found"}), 404

        files = os.listdir(file_dir)
        if not files:
            return jsonify({"status": "error", "message": "No file in upload"}), 404

        filepath = os.path.join(file_dir, files[0])
        real_path = os.path.realpath(filepath)

        return jsonify({
            "status": "success",
            "file_id": file_id,
            "filename": files[0],
            "stored_path": filepath,
            "real_path": real_path,
            "is_symlink": os.path.islink(filepath),
            "exists": os.path.exists(filepath),
            "size": os.path.getsize(filepath) if os.path.exists(filepath) else 0
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    """Reset all uploaded files"""
    try:
        # Clear upload directory
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        return jsonify({
            "status": "success",
            "message": "All uploads cleared",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
