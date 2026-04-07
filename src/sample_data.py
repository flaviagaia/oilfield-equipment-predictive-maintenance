from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import pandas as pd


PUBLIC_DATASET_REFERENCE = {
    "dataset_name": "3W Dataset",
    "dataset_owner": "Petrobras",
    "dataset_project": "3W Project",
    "dataset_reference": "3W Dataset: realistic and public dataset with rare undesirable real events in oil wells",
    "dataset_note": "This project uses a compact local 3W-style telemetry sample for deterministic execution while preserving the oil-and-gas predictive maintenance framing.",
}


def _atomic_write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", suffix=".csv", delete=False, dir=path.parent, encoding="utf-8") as tmp_file:
        temp_path = Path(tmp_file.name)
    try:
        df.to_csv(temp_path, index=False)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _atomic_write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", suffix=".json", delete=False, dir=path.parent, encoding="utf-8") as tmp_file:
        temp_path = Path(tmp_file.name)
    try:
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _generate_sample(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    assets = [
        "PUMP-01",
        "PUMP-02",
        "WIRELINE-01",
        "WIRELINE-02",
        "GENSET-01",
        "GENSET-02",
    ]
    rows = []
    for asset_id in assets:
        base_pressure = rng.uniform(2100, 2600)
        base_temp = rng.uniform(70, 90)
        base_vibration = rng.uniform(1.0, 2.2)
        base_current = rng.uniform(80, 120)
        for step in range(90):
            deterioration = step / 90
            event_risk = rng.random() < (0.03 + 0.10 * deterioration)
            vibration = base_vibration + deterioration * rng.uniform(1.0, 2.0) + rng.normal(0, 0.08)
            temperature = base_temp + deterioration * rng.uniform(12, 24) + rng.normal(0, 1.0)
            motor_current = base_current + deterioration * rng.uniform(16, 30) + rng.normal(0, 1.8)
            discharge_pressure = base_pressure + rng.normal(0, 35) - deterioration * rng.uniform(120, 260)
            suction_pressure = discharge_pressure - rng.uniform(420, 680) + rng.normal(0, 25)
            line_pressure = discharge_pressure - rng.uniform(150, 260) + rng.normal(0, 15)
            flow_rate = rng.uniform(102, 136) - deterioration * rng.uniform(18, 36) + rng.normal(0, 1.4)

            risk_score = (
                0.36 * max(vibration - 2.5, 0)
                + 0.24 * max(temperature - 90, 0) / 8
                + 0.20 * max(motor_current - 122, 0) / 10
                + 0.12 * max(112 - flow_rate, 0) / 8
                + 0.08 * max(1900 - discharge_pressure, 0) / 100
            )
            maintenance_required = int(event_risk or risk_score > 0.42 or deterioration > 0.82)

            rows.append(
                {
                    "asset_id": asset_id,
                    "window_id": f"{asset_id}-{step:03d}",
                    "discharge_pressure": round(float(discharge_pressure), 2),
                    "suction_pressure": round(float(suction_pressure), 2),
                    "line_pressure": round(float(line_pressure), 2),
                    "temperature": round(float(temperature), 2),
                    "vibration": round(float(vibration), 3),
                    "motor_current": round(float(motor_current), 2),
                    "flow_rate": round(float(flow_rate), 2),
                    "maintenance_required": maintenance_required,
                }
            )
    return pd.DataFrame(rows)


def ensure_dataset(base_dir: str | Path) -> dict[str, str]:
    base_path = Path(base_dir)
    telemetry_path = base_path / "data" / "raw" / "oilfield_telemetry_3w_style_sample.csv"
    reference_path = base_path / "data" / "raw" / "public_dataset_reference.json"

    telemetry_df = _generate_sample()
    _atomic_write_csv(telemetry_df, telemetry_path)
    _atomic_write_json(PUBLIC_DATASET_REFERENCE, reference_path)

    return {
        "telemetry_path": str(telemetry_path),
        "reference_path": str(reference_path),
    }
