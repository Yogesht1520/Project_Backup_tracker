# metrics_collector.py (updated)
import time, csv, os, psutil, socketio
from datetime import datetime
from anomaly_detector.lstm_inference import WINDOW_SIZE, detect_anomaly as detect_anomaly_ml
import traceback

# ===== File Setup =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "sample_metrics.csv")
log_path = os.path.join(BASE_DIR, "anomaly_log.csv")

if not os.path.exists(csv_path):
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "cpu_percent", "ram_percent", "disk_percent"])

# Ensure consistent anomaly_log header
ANOMALY_HEADER = ["timestamp", "source", "metric", "value", "cpu_percent", "ram_percent", "disk_percent", "severity", "trend"]

if not os.path.exists(log_path):
    with open(log_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(ANOMALY_HEADER)

# ===== Connect to Flask Socket =====
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=2)

@sio.event
def connect():
    print("✅ Connected to Flask server!")

@sio.event
def disconnect():
    print("❌ Disconnected from server")

try:
    sio.connect("http://127.0.0.1:5050")
except Exception as e:
    print("❌ Could not connect. Start app.py first.", str(e))
    # don't exit: allow offline mode (still write CSV logs)
    # exit()

print("📊 Starting extended metrics collector...")

# ==========================================================
#               METRICS COLLECTION LOOP
# ==========================================================
def collect_metrics():
    previous_score = None

    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # -------- Write live metrics to CSV --------
            with open(csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, cpu, ram, disk])

            # -------- Load sliding ML window (if available) --------
            def load_recent_buffer(window=WINDOW_SIZE):
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
                    df = df.sort_values("timestamp")
                    vals = df[["cpu_percent", "ram_percent", "disk_percent"]].tail(window).values
                    if vals.shape[0] == window:
                        return vals
                    return None
                except Exception:
                    return None

            recent_buf = load_recent_buffer(WINDOW_SIZE)

            # -------- ML anomaly detection (robust) --------
            label, score = "Normal", 0.0
            try:
                lab, sc = detect_anomaly_ml(cpu, ram, disk, recent_buf)
                label, score = lab, float(sc)
            except FileNotFoundError as e:
                # model/scaler not available — keep ML disabled but continue
                # print minimal message but continue with rule-based
                # print("ML assets missing, skipping ML detection:", e)
                label, score = "ModelMissing", 0.0
            except Exception as e:
                print("[ML detection error]", str(e))
                traceback.print_exc()
                label, score = "Error", 0.0

            # Severity mapping for ML score (if ML produced a score)
            if label == "Anomaly":
                if score > 0.7:
                    ml_sev = "High"
                elif score > 0.4:
                    ml_sev = "Medium"
                else:
                    ml_sev = "Low"
            else:
                ml_sev = "Low"

            # Trend calculation
            if previous_score is None:
                trend = "Stable"
            else:
                trend = "Rising" if score > previous_score else "Falling"

            previous_score = score

            # ==========================================================
            #                ML ANOMALY LOGGING (normalized schema)
            # ==========================================================
            # We always append a normalized row when ML says Anomaly (or ModelMissing for visibility)
            if label == "Anomaly":
                with open(log_path, "a", newline="") as logf:
                    writer = csv.writer(logf)
                    writer.writerow([
                        timestamp,
                        "ML",
                        "Composite",                # metric: composite score
                        round(score, 5),
                        round(cpu, 2),
                        round(ram, 2),
                        round(disk, 2),
                        ml_sev,
                        trend
                    ])
                print(f"[ML] Logged anomaly at {timestamp}, score={score}")

                # Emit ML detection to dashboard (if connected)
                try:
                    sio.emit("anomaly_alert", {
                        "timestamp": timestamp,
                        "source": "ML",
                        "metric": "Composite",
                        "value": round(score, 4),
                        "cpu_percent": round(cpu,2),
                        "ram_percent": round(ram,2),
                        "disk_percent": round(disk,2),
                        "severity": ml_sev,
                        "trend": trend
                    })
                except Exception:
                    pass

            # ==========================================================
            #         RULE-BASED ANOMALY LOGGING (same normalized schema)
            # ==========================================================
            # Rule thresholds (kept as before but written into same schema)
            # NOTE: keep thresholds as project expects — you can adjust later
            rule_triggered = False
            rule_metric = None
            rule_value = None

            if cpu > 15:
                rule_triggered = True; rule_metric = "CPU"; rule_value = cpu
            elif ram > 95:
                rule_triggered = True; rule_metric = "RAM"; rule_value = ram
            elif disk > 30:
                rule_triggered = True; rule_metric = "Disk"; rule_value = disk

            if rule_triggered:
                with open(log_path, "a", newline="") as logf:
                    writer = csv.writer(logf)
                    writer.writerow([
                        timestamp,
                        "Rule-Based",
                        rule_metric,
                        round(rule_value, 2),
                        round(cpu, 2),
                        round(ram, 2),
                        round(disk, 2),
                        "High",      # rule-based set to High severity
                        "Stable"
                    ])
                print(f"🧾 Rule-based anomaly logged at {timestamp} ({rule_metric}={rule_value})")

                try:
                    sio.emit("anomaly_alert", {
                        "timestamp": timestamp,
                        "source": "Rule-Based",
                        "metric": rule_metric,
                        "value": round(rule_value, 2),
                        "cpu_percent": round(cpu,2),
                        "ram_percent": round(ram,2),
                        "disk_percent": round(disk,2),
                        "severity": "High",
                        "trend": "Stable"
                    })
                except Exception:
                    pass

            # -------- Send live metrics (same as before, kept for live charts) --------
            try:
                sio.emit("metrics_update", {
                    "timestamp": timestamp,
                    "cpu": cpu,
                    "ram": ram,
                    "disk": disk
                })
            except Exception:
                pass

            print(f"📡 Sent metrics — CPU:{cpu}%, RAM:{ram}%, Disk:{disk}%")
            time.sleep(5)

        except Exception as e:
            print("[Collector loop error]", e)
            traceback.print_exc()
            # sleep a bit to avoid tight failure loop
            time.sleep(3)


# Run
if __name__ == "__main__":
    collect_metrics()
