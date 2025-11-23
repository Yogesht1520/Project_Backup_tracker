import os
import numpy as np
import joblib
import pickle
import keras
from keras.saving import load_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "lstm_model.keras")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
THRESH_PATH = os.path.join(BASE_DIR, "threshold.pkl")

WINDOW_SIZE = 12

_model = None
_scaler = None
_th = None

def _ensure_loaded():
    global _model, _scaler, _th

    if _scaler is None:
        _scaler = joblib.load(SCALER_PATH)

    if _model is None:
        _model = load_model(MODEL_PATH, compile=False)

    if _th is None:
        with open(THRESH_PATH, "rb") as f:
            _th = pickle.load(f)

def detect_anomaly(cpu, ram, disk, recent_buffer=None):
    _ensure_loaded()

    sample = np.array([cpu, ram, disk], dtype=float).reshape(1, -1)

    if recent_buffer is None:
        recent_buffer = np.tile(sample, (WINDOW_SIZE, 1))
    else:
        arr = np.array(recent_buffer, dtype=float)
        if arr.shape[0] < WINDOW_SIZE:
            pad = np.tile(arr[0:1, :], (WINDOW_SIZE - arr.shape[0], 1))
            arr = np.vstack([pad, arr])
        recent_buffer = arr[-WINDOW_SIZE:]

    scaled_window = _scaler.transform(recent_buffer)
    X = np.expand_dims(scaled_window, axis=0)

    pred_scaled = _model.predict(X, verbose=0)
    pred = pred_scaled[0] * _scaler.scale_ + _scaler.mean_
    actual = sample.flatten()

    mse = float(np.mean((pred - actual) ** 2))
    threshold = _th["threshold"]

    label = "Anomaly" if mse > threshold else "Normal"
    return label, mse
