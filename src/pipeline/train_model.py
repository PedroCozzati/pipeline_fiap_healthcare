from pathlib import Path

import pandas as pd

from model import (
    DEFAULT_FEATURE_COLUMNS,
    DEFAULT_TARGET_COLUMN,
    generate_demo_training_data,
    save_model,
    train_risk_model,
)


def main(base_dir: Path, output_dir: Path):
    raw_training_csv = output_dir / "risk_training.csv"
    model_path = output_dir / "risk_model.joblib"

    if raw_training_csv.exists():
        df = pd.read_csv(raw_training_csv)
        print(f"Loading training data from {raw_training_csv}")
    else:
        print("No labeled training CSV found, generating demo dataset.")
        df = generate_demo_training_data()
        df.to_csv(raw_training_csv, index=False)
        print(f"Demo training data saved to {raw_training_csv}")

    model, X_test, y_test = train_risk_model(df, feature_columns=DEFAULT_FEATURE_COLUMNS, target_column=DEFAULT_TARGET_COLUMN)
    save_model(model, model_path)

    accuracy = model.score(X_test, y_test)
    print(f"Model trained and saved to {model_path}")
    print(f"Validation accuracy: {accuracy:.3f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train or regenerate the risk model.")
    parser.add_argument(
        "--base-dir",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Discovery base directory.",
    )
    parser.add_argument(
        "--output-dir",
        default=Path(__file__).resolve().parents[1] / "output",
        type=Path,
        help="Where the trained model will be saved.",
    )
    args = parser.parse_args()
    main(args.base_dir, args.output_dir)
