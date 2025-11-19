# anomaly_model.py
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # go up to backup_tracker/
csv_path = os.path.join(BASE_DIR, "sample_metrics.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_model.pkl")

# --- Ensure CSV Exists ---
if not os.path.exists(csv_path):
    print("📄 No sample_metrics.csv found — creating baseline data...")
    df_init = pd.DataFrame([
        {"timestamp": "2025-11-08 00:00:00", "cpu_percent": 15, "ram_percent": 60, "disk_percent": 70},
        {"timestamp": "2025-11-08 00:05:00", "cpu_percent": 20, "ram_percent": 65, "disk_percent": 71},
        {"timestamp": "2025-11-08 00:10:00", "cpu_percent": 18, "ram_percent": 63, "disk_percent": 72}
    ])
    df_init.to_csv(csv_path, index=False)
    print(f"✅ Created {csv_path} with baseline entries.")

def train_model(csv_path="sample_metrics.csv"):
    """Train Isolation Forest model on historical metrics data."""
    df = pd.read_csv(csv_path)

    if df.empty:
        raise ValueError("Metrics CSV is empty!")

    features = ["cpu_percent", "ram_percent", "disk_percent"]
    X = df[features]

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)

    joblib.dump(model, MODEL_PATH)
    print(f"✅ Model trained and saved at {MODEL_PATH}")

def load_model():
    """Load trained model if exists, else train new one."""
    if not os.path.exists(MODEL_PATH):
        print("⚙️ No model found. Training new model...")
        train_model()
    return joblib.load(MODEL_PATH)

def detect_anomaly(cpu, ram, disk):
    model = load_model()
    import pandas as pd
    input_df = pd.DataFrame(
        [[cpu, ram, disk]],
        columns=["cpu_percent", "ram_percent", "disk_percent"]
    )
    pred = model.predict(input_df)[0]
    return "Anomaly" if pred == -1 else "Normal"
