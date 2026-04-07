from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.sample_data import ensure_dataset


def run_pipeline(base_dir: str | Path) -> dict:
    base_path = Path(base_dir)
    dataset = ensure_dataset(base_path)
    telemetry = pd.read_csv(dataset["telemetry_path"])

    feature_columns = [
        "asset_id",
        "discharge_pressure",
        "suction_pressure",
        "line_pressure",
        "temperature",
        "vibration",
        "motor_current",
        "flow_rate",
    ]
    X = telemetry[feature_columns]
    y = telemetry["maintenance_required"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        stratify=y,
        random_state=42,
    )

    numeric_features = [
        "discharge_pressure",
        "suction_pressure",
        "line_pressure",
        "temperature",
        "vibration",
        "motor_current",
        "flow_rate",
    ]
    categorical_features = ["asset_id"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric_features),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=220,
                    max_depth=8,
                    min_samples_leaf=4,
                    random_state=42,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    roc_auc = float(roc_auc_score(y_test, probabilities))
    average_precision = float(average_precision_score(y_test, probabilities))
    f1 = float(f1_score(y_test, predictions))

    processed_dir = base_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    scored_path = processed_dir / "maintenance_scored_windows.csv"
    report_path = processed_dir / "oilfield_predictive_maintenance_report.json"

    scored_df = X_test.copy()
    scored_df["maintenance_required"] = y_test.values
    scored_df["predicted_probability"] = probabilities.round(4)
    scored_df["predicted_label"] = predictions
    scored_df.to_csv(scored_path, index=False)

    summary = {
        "dataset_source": "3w_style_oilfield_telemetry_sample",
        "public_dataset_reference": dataset["reference_path"],
        "row_count": int(len(telemetry)),
        "asset_count": int(telemetry["asset_id"].nunique()),
        "positive_rate": round(float(telemetry["maintenance_required"].mean()), 4),
        "roc_auc": round(roc_auc, 4),
        "average_precision": round(average_precision, 4),
        "f1": round(f1, 4),
        "scored_artifact": str(scored_path),
        "report_artifact": str(report_path),
    }
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
