import numpy as np
import pandas as pd


# === Пороговые значения ===
GYRO_THRESHOLD = 20
ACC_MAG_THRESHOLD = 1.5
JERK_THRESHOLD = 2.0
JERK_RATIO_THRESHOLD = 0.3
MIN_SPEED_FOR_RATIO = 5 / 3.6
URBAN_THRESHOLD = 70
URBAN_LIMIT = 60
HIGHWAY_LIMIT = 120
JERK_RESET_STEPS = 3


def trim_instability(
    df: pd.DataFrame, std_window=10, std_thresh=0.15, padding=3
) -> pd.DataFrame:
    df = df.copy()
    df['acc_mag'] = np.sqrt(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2)
    df['acc_std'] = df['acc_mag'].rolling(std_window, center=True).std().fillna(0)
    stable_mask = df['acc_std'] < std_thresh
    stable_idx = np.where(stable_mask)[0]
    if len(stable_idx) == 0:
        return df.drop(columns='acc_std')
    start_idx = stable_idx[0] + padding
    end_idx = stable_idx[-1] - padding
    return df.iloc[start_idx:end_idx].reset_index(drop=True).drop(columns='acc_std')


def extract_trip_features(
    df: pd.DataFrame, filename: str = "trip.csv"
) -> tuple[dict, dict]:
    if df.empty or 'speed_kmh' not in df.columns:
        raise ValueError("Некорректный файл: отсутствует колонка 'speed_kmh'")

    df = df[df['speed_kmh'] >= 0].copy()
    df = trim_instability(df)

    if 'timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['delta_sec'] = df['timestamp'].diff().dt.total_seconds().fillna(1.0)
        except Exception:
            df['delta_sec'] = 1.0
    else:
        df['delta_sec'] = 1.0

    df['speed_ms'] = df['speed_kmh'] / 3.6
    df['acc_mag'] = np.sqrt(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2)
    df['gyro_mag'] = np.sqrt(df['gyro_x']**2 + df['gyro_y']**2 + df['gyro_z']**2)
    df['jerk'] = df['speed_ms'].diff().fillna(0) / df['delta_sec']
    df['jerk_ratio'] = df['jerk'].abs() / (df['speed_ms'] + 0.1)
    df['gyro_mag_smooth'] = df['gyro_mag'].rolling(window=5, center=True).mean()

    if df['speed_ms'].iloc[0] > MIN_SPEED_FOR_RATIO:
        df.loc[0:JERK_RESET_STEPS - 1, ['jerk', 'jerk_ratio']] = 0

    df['mean_speed_60s'] = df['speed_kmh'].rolling(window=60, center=True).mean()
    df['context'] = np.where(df['mean_speed_60s'] > URBAN_THRESHOLD, 'highway', 'urban')
    df['speed_threshold'] = np.where(df['context'] == 'highway', HIGHWAY_LIMIT, URBAN_LIMIT)

    df['event_gyro'] = df['gyro_mag_smooth'] > GYRO_THRESHOLD
    df['event_acc'] = df['acc_mag'] > ACC_MAG_THRESHOLD
    df['event_jerk'] = df['jerk'].abs() > JERK_THRESHOLD
    df['event_jerk_accel'] = df['jerk'] > JERK_THRESHOLD
    df['event_jerk_brake'] = df['jerk'] < -JERK_THRESHOLD
    df['event_jerk_relative'] = (df['jerk_ratio'] > JERK_RATIO_THRESHOLD) & (df['speed_ms'] > MIN_SPEED_FOR_RATIO)
    df['event_speed'] = df['speed_kmh'] > df['speed_threshold']
    df['event_any'] = df[['event_gyro', 'event_acc', 'event_jerk', 'event_jerk_relative', 'event_speed']].any(axis=1)

    if 'timestamp' in df.columns:
        try:
            trip_duration_sec = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds()
        except Exception:
            trip_duration_sec = df['delta_sec'].sum()
    else:
        trip_duration_sec = df['delta_sec'].sum()

    user_stats = {
        'avg_speed': df['speed_kmh'].mean(),
        'distance': (df['speed_kmh'] * df['delta_sec']).sum() / 3600,
        'hard_brakes': int(df['event_jerk_brake'].sum()),
        'hard_accels': int(df['event_jerk_accel'].sum()),
        'sharp_turns': int(df['event_gyro'].sum()),
        'avg_gyro_mag': df['gyro_mag'].mean(),
        'trip_duration': trip_duration_sec
    }

    stats = {
        'file': filename,
        'pct_event_jerk': df['event_jerk'].mean(),
        'pct_event_jerk_accel': df['event_jerk_accel'].mean(),
        'pct_event_jerk_brake': df['event_jerk_brake'].mean(),
        'pct_event_jerk_relative': df['event_jerk_relative'].mean(),
        'pct_event_acc': df['event_acc'].mean(),
        'pct_event_gyro': df['event_gyro'].mean(),
        'pct_event_speed': df['event_speed'].mean(),
        'pct_event_any': df['event_any'].mean(),
        'mean_speed_kmh': df['speed_kmh'].mean(),
        'max_speed_kmh': df['speed_kmh'].max(),
        'trip_duration_sec': trip_duration_sec
    }

    aggr_score = (
        stats['pct_event_jerk']
        + 0.5 * stats['pct_event_jerk_relative']
        + stats['pct_event_acc']
        + stats['pct_event_gyro']
        + stats['pct_event_speed']
    )

    if aggr_score < 0.1:
        stats['driving_style'] = 'плавный'
    elif aggr_score < 0.25:
        stats['driving_style'] = 'умеренный'
    else:
        stats['driving_style'] = 'агрессивный'

    return stats, user_stats
