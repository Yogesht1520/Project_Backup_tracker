# anomaly_detector/lstm_model.py
"""
Train a hybrid LSTM -> Dense model that predicts the next multivariate step.
Saves:
  - lstm_model.h5
  - scaler.pkl
  - threshold.pkl
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import pickle
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "sample_metrics.csv")
MODEL_PATH = os.path.join(BASE_DIR, "lstm_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
THRESH_PATH = os.path.join(BASE_DIR, "threshold.pkl")

# Config
WINDOW_SIZE = 12    # ~60s if you emit every 5s
TEST_SIZE = 0.2
RANDOM_STATE = 42
EPOCHS = 80
BATCH_SIZE = 32

def load_csv(path=CSV_PATH):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    # Keep only required columns and ensure order
    df = df.sort_values("timestamp").reset_index(drop=True)
    cols = ["cpu_percent", "ram_percent", "disk_percent"]
    # If dataset has different naming, try lowercase variants:
    for c in cols:
        if c not in df.columns:
            # try common alternatives
            for alt in [c.replace("_percent","%"), c.replace("_percent","")]:
                if alt in df.columns:
                    df[c] = df[alt]
                    break
    return df[cols].astype(float)

def create_sequences(values, window=WINDOW_SIZE):
    X, y = [], []
    for i in range(len(values) - window):
        X.append(values[i:i+window])
        y.append(values[i+window])  # next-step prediction
    return np.array(X), np.array(y)

def build_model(n_timesteps, n_features):
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(n_timesteps, n_features)),
        Dropout(0.15),
        LSTM(32, return_sequences=False),
        Dropout(0.10),
        Dense(32, activation='relu'),
        Dense(n_features, activation='linear')  # predict next-step values for each feature
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def train():
    df = load_csv()
    if df.shape[0] < WINDOW_SIZE + 5:
        raise RuntimeError("Not enough data to train. Need more rows in sample_metrics.csv")

    # scale
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df.values)
    joblib.dump(scaler, SCALER_PATH)
    print(f"[+] Saved scaler to {SCALER_PATH}")

    X, y = create_sequences(scaled, window=WINDOW_SIZE)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, shuffle=False)

    model = build_model(WINDOW_SIZE, X.shape[2])
    model.summary()

    es = EarlyStopping(monitor='val_loss', patience=8, restore_best_weights=True, verbose=1)
    ckpt = ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='val_loss', verbose=1)

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[es, ckpt],
        verbose=2
    )

    # Evaluate reconstruction/prediction errors on validation set
    preds_val = model.predict(X_val)
    mse_val = np.mean(np.square(preds_val - y_val), axis=1)  # per-sample MSE
    mean_err = float(np.mean(mse_val))
    std_err = float(np.std(mse_val))
    # threshold: mean + 3*std (conservative)
    threshold = mean_err + 3 * std_err

    # Save threshold
    with open(THRESH_PATH, "wb") as f:
        pickle.dump({"mean": mean_err, "std": std_err, "threshold": threshold}, f)

    print(f"[+] Saved model to {MODEL_PATH}")
    print(f"[+] Threshold: mean={mean_err:.6f}, std={std_err:.6f}, threshold={threshold:.6f}")

    return {
        "model_path": MODEL_PATH,
        "scaler_path": SCALER_PATH,
        "threshold": {"mean": mean_err, "std": std_err, "threshold": threshold}
    }

if __name__ == "__main__":
    print("Starting training...")
    res = train()
    print("Training completed.")
