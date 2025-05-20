from __future__ import annotations
from pathlib import Path

import joblib
import pandas as pd


FEATURE_COLS = [
    "pct_event_jerk", "pct_event_jerk_accel", "pct_event_jerk_brake",
    "pct_event_jerk_relative", "pct_event_acc", "pct_event_gyro",
    "pct_event_speed", "pct_event_any",
    "mean_speed_kmh", "max_speed_kmh", "trip_duration_sec",
]

DEFAULT_TRIPS_DIR = Path("Trips")


def _debug(msg: str, enable: bool):
    if enable:
        print("[DEBUG]", msg)


def _csv_to_row(stats, debug: bool) -> pd.DataFrame:

    missing = [c for c in FEATURE_COLS if c not in stats]
    if missing:
        raise ValueError(f"В вычисленных признаках отсутствуют: {missing}")

    row = pd.DataFrame([{k: stats[k] for k in FEATURE_COLS}])
    _debug(f"Извлечены признаки: {row.to_dict(orient='records')[0]}", debug)
    return row


def classify_trip(
    stats,
    *,
    model_path: str | Path = "data_processing/rf_v1.joblib",
    debug: bool = False
) -> str:
    """Классифицирует поездку; возвращает 'smooth'/'moderate'/'aggressive'.

    Если `csv_path is None`, берёт первый .csv из каталога `Trips/`.
    """
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    X = _csv_to_row(stats, debug)

    _debug(f"Загружаю модель: {model_path}", debug)
    pipe = joblib.load(model_path)

    label = pipe.predict(X)[0]
    prob = pipe.predict_proba(X).max()
    _debug(f"Прогноз: {label}  (p={prob:.2f})", debug)

    return str(label)
