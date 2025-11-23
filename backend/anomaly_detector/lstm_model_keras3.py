# lstm_model_keras3.py
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import pickle
import tensorflow as tf
from tensorflow import keras
from keras import layers

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "sample_metrics.csv")
MODEL_PATH = os.path.join(BASE_DIR, "lstm_model.keras")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
THRESH_PATH = os.path.join(BASE_DIR, "threshold.pkl")

WINDOW_SIZE = 12
EPOCHS = 80
BATCH_SIZE = 32
TEST_SIZE = 0.2
RANDOM_STATE = 42

def load_csv(path=CSV_PATH):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    cols = ["cpu_percent", "ram_percent", "disk_percent"]
    return df[cols].astype(float)

def create_sequences(values, window=WINDOW_SIZE):
    X, y = [], []
    for i in range(len(values) - window):
        X.append(values[i:i+window])
        y.append(values[i+window])
    return np.array(X), np.array(y)

def build_model(n_timesteps, n_features):
    inputs = keras.Input(shape=(n_timesteps, n_features))

    x = layers.LSTM(64, return_sequences=True)(inputs)
    x = layers.Dropout(0.15)(x)

    x = layers.LSTM(32, return_sequences=False)(x)
    x = layers.Dropout(0.10)(x)

    x = layers.Dense(32, activation="relu")(x)
    outputs = layers.Dense(n_features, activation="linear")(x)

    model = keras.Model(inputs, outputs)
    model.compile(optimizer="adam", loss="mse")
    return model

def train():
    print("🔄 Loading dataset...")
    df = load_csv()

    # Scale features
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df.values)
    joblib.dump(scaler, SCALER_PATH)
    print(f"[+] Saved scaler → {SCALER_PATH}")

    X, y = create_sequences(scaled)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, shuffle=False
    )

    model = build_model(WINDOW_SIZE, X.shape[2])
    model.summary()

    es = keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=8,
        restore_best_weights=True
    )

    ckpt = keras.callbacks.ModelCheckpoint(
        MODEL_PATH, save_best_only=True, monitor="val_loss"
    )

    print("🚀 Training model...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[es, ckpt],
        verbose=2
    )

    print(f"[+] Saved model → {MODEL_PATH}")

    # Compute threshold
    preds_val = model.predict(X_val, verbose=0)
    mse_val = np.mean(np.square(preds_val - y_val), axis=1)

    mean_err = float(np.mean(mse_val))
    std_err = float(np.std(mse_val))
    threshold = mean_err + 3 * std_err

    with open(THRESH_PATH, "wb") as f:
        pickle.dump({"mean": mean_err, "std": std_err, "threshold": threshold}, f)

    print(f"[+] Saved threshold → {THRESH_PATH}")
    print(f"📌 mean={mean_err}, std={std_err}, threshold={threshold}")

if __name__ == "__main__":
    train()
