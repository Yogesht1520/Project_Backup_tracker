# anomaly_detector/lstm_inference.py
"""
Load the trained model + scaler + threshold and expose detect_anomaly(cpu,ram,disk).
Returns (label, score) where score is MSE between predicted next-step and actual.
"""

import os
import numpy as np
import joblib
import pickle
from tensorflow.keras.models import load_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "lstm_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
THRESH_PATH = os.path.join(BASE_DIR, "threshold.pkl")

WINDOW_SIZE = 12
FEATURE_ORDER = ["cpu_percent", "ram_percent", "disk_percent"]

# Load assets (lazy load)
_model = None
_scaler = None
_th = None

def _ensure_loaded():
    global _model, _scaler, _th
    if _scaler is None:
        if not os.path.exists(SCALER_PATH):
            raise FileNotFoundError("Scaler not found. Run training first.")
        _scaler = joblib.load(SCALER_PATH)
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("Model not found. Run training first.")
        _model = load_model(MODEL_PATH, compile=False)

    if _th is None:
        if not os.path.exists(THRESH_PATH):
            raise FileNotFoundError("Threshold not found. Run training first.")
        with open(THRESH_PATH, "rb") as f:
            _th = pickle.load(f)

def detect_anomaly(cpu, ram, disk, recent_buffer=None):
    """
    cpu, ram, disk: numbers (percent)
    recent_buffer: optional numpy array shape (WINDOW_SIZE, 3) to use as historical points.
                   If None, the caller must provide a buffer of last WINDOW_SIZE samples (including current)
                   otherwise detection will be made using available items (padding may be applied).
    Returns: (label:str, score:float)
    """

    _ensure_loaded()

    # Build current sample vector
    sample = np.array([cpu, ram, disk], dtype=float).reshape(1, -1)

    # If no recent buffer passed, create a minimal buffer by repeating current sample
    if recent_buffer is None:
        # padded buffer: last WINDOW_SIZE values -> repeat current sample
        recent_buffer = np.tile(sample, (WINDOW_SIZE, 1))
    else:
        # ensure shape correctness
        arr = np.array(recent_buffer, dtype=float)
        if arr.shape[0] < WINDOW_SIZE:
            # pad by repeating first rows at top
            pad_count = WINDOW_SIZE - arr.shape[0]
            pad = np.tile(arr[0:1, :], (pad_count, 1))
            arr = np.vstack([pad, arr])
        recent_buffer = arr[-WINDOW_SIZE:, :]

    # scale the window
    scaled_window = _scaler.transform(recent_buffer)  # shape (WINDOW_SIZE, features)
    X = np.expand_dims(scaled_window, axis=0)  # shape (1, WINDOW_SIZE, features)

    # predict next step (scaled)
    pred_scaled = _model.predict(X, verbose=0)  # shape (1, features)
    # inverse-scale prediction to original units
    # trick: scaler uses mean & scale per feature; we can invert by applying scaler.mean_ & scale_
    pred = pred_scaled[0] * _scaler.scale_ + _scaler.mean_
    actual = sample.flatten()

    # MSE
    mse = float(np.mean((pred - actual) ** 2))

    threshold_value = _th.get("threshold", None)
    label = "Anomaly" if threshold_value is not None and mse > threshold_value else "Normal"

    return label, mse

# Convenience wrapper for compatibility with older code that uses detect_anomaly(cpu,ram,disk)
def detect_anomaly_simple(cpu, ram, disk):
    return detect_anomaly(cpu, ram, disk)

if __name__ == "__main__":
    # quick smoke test (requires trained model)
    import sys
    if len(sys.argv) < 4:
        print("Usage: python lstm_inference.py <cpu> <ram> <disk>")
    else:
        c, r, d = map(float, sys.argv[1:4])
        label, score = detect_anomaly(c, r, d)
        print(f"Label={label}, score={score:.6f}")
