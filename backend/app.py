import os
import csv
import json
import psutil
import random
import logging
import hashlib
from datetime import datetime
from urllib.parse import quote_plus
from cryptography.fernet import Fernet
import smtplib
from email.message import EmailMessage
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_apscheduler import APScheduler

from database import db, BackupJob


# ----------------------------------------
# Initial Setup
# ----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DIR = os.path.join(BASE_DIR, "vault")
DECRYPT_DIR = os.path.join(BASE_DIR, "restored")
ANOMALY_LOG_PATH = os.path.join(BASE_DIR, "anomaly_detector", "anomaly_log.csv")

os.makedirs(VAULT_DIR, exist_ok=True)
os.makedirs(DECRYPT_DIR, exist_ok=True)


# ----------------------------------------
# Vault Key Setup
# ----------------------------------------
KEY_PATH = os.path.join(BASE_DIR, "vault_key.key")
if os.path.exists(KEY_PATH):
    with open(KEY_PATH, "rb") as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(key)

fernet = Fernet(key)


# ----------------------------------------
# Flask & DB Setup
# ----------------------------------------
app = Flask(__name__)
password = quote_plus("root")
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:Be/1229/2019-20@localhost/backup_tracker"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

socketio = SocketIO(app, cors_allowed_origins="*")


# ----------------------------------------
# Logging
# ----------------------------------------
def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logger = logging.getLogger("BackupTracker")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('logs/backup_tracker.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    if not logger.hasHandlers():
        logger.addHandler(handler)
    return logger


logger = setup_logger()
logger.info("Flask Backup Tracker Started")


# ----------------------------------------
# Scheduler (Automatic Job Update)
# ----------------------------------------
scheduler = APScheduler()


def send_alert_email(failed_count):
    msg = EmailMessage()
    msg.set_content(f"{failed_count} backup job(s) failed!")
    msg['Subject'] = 'Backup Tracker Alert'
    msg['From'] = 'yogesht1520@gmail.com'
    msg['To'] = 'yt6399941@gmail.com'
    with smtplib.SMTP('smtp.gmail.com', 587) as s:
        s.starttls()
        s.login('yogesht1520@gmail.com', 'nbyrpwtwyliswsjf')
        s.send_message(msg)

def update_jobs():
    with app.app_context():

        # Update pending jobs randomly
        pending_jobs = BackupJob.query.filter_by(status='PENDING').all()
        for job in pending_jobs:
            job.status = random.choice(['SUCCESS', 'FAILED'])
            job.logs = f"Job {job.job_name} completed with status {job.status}"
        db.session.commit()

        # Send job stats
        stats = {
            "total": BackupJob.query.count(),
            "success": BackupJob.query.filter_by(status='SUCCESS').count(),
            "failed": BackupJob.query.filter_by(status='FAILED').count(),
            "pending": BackupJob.query.filter_by(status='PENDING').count()
        }
        socketio.emit('job_update', stats)

        # Anomaly Rule: CPU > 80%
        cpu_value = psutil.cpu_percent(interval=1)
        if cpu_value > 80:
            socketio.emit('anomaly_alert', {
                "cpu": cpu_value,
                "message": "CPU anomaly detected"
            })
 
        if stats["failed"] > 7:
            send_alert_email(stats["failed"])



with app.app_context():
    scheduler.add_job(id='JobUpdater', func=update_jobs, trigger='interval', seconds=30)
    scheduler.init_app(app)
    scheduler.start()


# ----------------------------------------
# Helper Functions
# ----------------------------------------
def compute_sha256(path):
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha.update(block)
    return sha.hexdigest()


def _safe_float(v):
    try:
        return float(v)
    except:
        return None


# ----------------------------------------
# API ROUTES
# ----------------------------------------

@app.route("/")
def home():
    return jsonify({"message": "Backup Tracker API Running"})


# ---------------------- JOBS ----------------------

@app.route("/api/jobs", methods=["GET"])
def api_jobs():
    jobs = BackupJob.query.order_by(BackupJob.timestamp.desc()).all()
    return jsonify([
        {
            "id": j.id,
            "name": j.job_name,
            "status": j.status,
            "timestamp": j.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for j in jobs
    ])


@app.route("/create_job", methods=["POST"])
def create_job():
    data = request.json
    new_job = BackupJob(job_name=data["job_name"])
    db.session.add(new_job)
    db.session.commit()
    return jsonify({"message": "Job created", "job_id": new_job.id})


# ---------------------- STATS ----------------------

@app.route("/api/stats")
def api_stats():
    total = BackupJob.query.count()
    success = BackupJob.query.filter_by(status='SUCCESS').count()
    failed = BackupJob.query.filter_by(status='FAILED').count()
    pending = BackupJob.query.filter_by(status='PENDING').count()

    return jsonify({
        "total": total,
        "success": success,
        "failed": failed,
        "pending": pending,
        "success_rate": round((success / total) * 100, 2) if total else 0,
        "fail_rate": round((failed / total) * 100, 2) if total else 0
    })


# ---------------------- VAULT ----------------------

@app.route("/vault/list")
def vault_list():
    files = []
    for file in os.listdir(VAULT_DIR):
        path = os.path.join(VAULT_DIR, file)
        files.append({
            "name": file,
            "size_kb": round(os.path.getsize(path) / 1024, 2),
            "modified": datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify(files)


@app.route("/vault/upload", methods=["POST"])
def vault_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    encrypted_name = f"{file.filename}_{ts}.enc"
    path = os.path.join(VAULT_DIR, encrypted_name)

    encrypted_data = fernet.encrypt(file.read())
    with open(path, "wb") as f:
        f.write(encrypted_data)

    hash_value = compute_sha256(path)
    with open(path + ".hash", "w") as h:
        h.write(hash_value)

    socketio.emit("vault_update", {"message": f"{file.filename} uploaded"})

    return jsonify({"message": "Encrypted & stored", "filename": encrypted_name})


@app.route('/vault/verify/<filename>', methods=['GET'])
def vault_verify(filename):
    """Verify integrity of encrypted file using its hash"""
    file_path = os.path.join(VAULT_DIR, filename)
    hash_path = file_path + ".hash"

    if not os.path.exists(file_path):
        return jsonify({"error": "Encrypted file not found"}), 404
    if not os.path.exists(hash_path):
        return jsonify({"error": "Hash file missing"}), 404

    stored_hash = open(hash_path).read().strip()
    current_hash = compute_sha256(file_path)

    if stored_hash == current_hash:
        return jsonify({"verified": True, "message": "✅ Integrity check passed"})
    else:
        return jsonify({"verified": False, "message": "⚠️ File integrity compromised!"})

    with open(file_path, "rb") as f:
        decrypted_data = fernet.decrypt(f.read())
    restore_path = os.path.join(DECRYPT_DIR, filename.replace(".enc", ""))
    with open(restore_path, "wb") as f:
        f.write(decrypted_data)

    return send_file(restore_path, as_attachment=True)

@app.route("/vault/restore/<filename>")
def vault_restore(filename):
    path = os.path.join(VAULT_DIR, filename)

    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404

    try:
        decrypted = fernet.decrypt(open(path, "rb").read())
        original_name = filename.replace(".enc", "")
        restore_path = os.path.join(DECRYPT_DIR, original_name)

        with open(restore_path, "wb") as f:
            f.write(decrypted)

        return send_file(restore_path, as_attachment=True, download_name=original_name)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------- ANOMALIES ----------------------

@app.route("/api/anomalies")
def api_anomalies():
    if not os.path.exists(ANOMALY_LOG_PATH):
        return jsonify([])

    rows = []
    with open(ANOMALY_LOG_PATH) as f:
        for r in csv.DictReader(f):
            rows.append({
                "timestamp": r.get("timestamp", ""),
                "source": r.get("source", "Rule-Based"),
                "metric": r.get("metric", "Unknown"),
                "value": _safe_float(r.get("value", "")),
                "severity": r.get("severity", "Low"),
                "trend": r.get("trend", "Stable"),
                "cpu_percent": _safe_float(r.get("cpu_percent", "")),
                "ram_percent": _safe_float(r.get("ram_percent", "")),
                "disk_percent": _safe_float(r.get("disk_percent", ""))
            })

    rows.sort(key=lambda x: x["timestamp"])
    return jsonify(rows[-50:])


@app.route("/api/anomaly_timeline")
def api_timeline():
    if not os.path.exists(ANOMALY_LOG_PATH):
        return jsonify([])

    rows = []
    with open(ANOMALY_LOG_PATH) as f:
        for r in csv.DictReader(f):
            rows.append({
                "timestamp": r.get("timestamp"),
                "source": r.get("source"),
                "metric": r.get("metric"),
                "value": _safe_float(r.get("value", "")),
                "severity": r.get("severity"),
                "trend": r.get("trend")
            })

    rows.sort(key=lambda x: x["timestamp"], reverse=True)
    return jsonify(rows)


# ---------------------- Socket.IO ----------------------

@socketio.on("metrics_update")
def socket_metrics(data):
    emit("metrics_update", data, broadcast=True)


@socketio.on("anomaly_alert")
def socket_anomaly(data):
    emit("anomaly_alert", data, broadcast=True)


# ----------------------------------------
# Run Server
# ----------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, host="127.0.0.1", port=5050, debug=True)
