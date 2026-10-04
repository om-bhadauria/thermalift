#!/usr/bin/env python
"""
Training script for ML models.
Trains production forecaster and risk predictors on synthetic data.

Usage:
    python -m app.ml.train_models [--output-dir DIR] [--n-days N] [--test-size FLOAT]
"""
import argparse
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ml.production_forecaster import train_production_model
from app.ml.risk_predictor import train_risk_model


def main():
    parser = argparse.ArgumentParser(description="Train ML models for THERMALIFT")
    parser.add_argument("--output-dir", type=str, default="models", help="Output directory for models")
    parser.add_argument("--n-days", type=int, default=180, help="Days of synthetic data to generate")
    parser.add_argument("--freq-hours", type=int, default=6, help="Frequency in hours")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set fraction")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    parser.add_argument("--risk-target", type=str, default="rod_float_risk", 
                       choices=["rod_float_risk", "impact_loading_risk"],
                       help="Risk target to train")
    parser.add_argument("--train-both-risks", action="store_true", 
                       help="Train both rod_float_risk and impact_loading_risk")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("THERMALIFT ML Model Training")
    print("=" * 60)
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Synthetic data: {args.n_days} days, {args.freq_hours}h frequency")
    print(f"Test size: {args.test_size}")
    print(f"Random state: {args.random_state}")
    print()
    print("WARNING: ALL MODELS TRAINED ON SYNTHETIC/DEMO DATA")
    print("         NOT VALIDATED AGAINST REAL BAGHEWALA/OIL FIELD DATA")
    print("=" * 60)
    
    all_results = {}
    
    # Train production forecaster
    print("\n" + "=" * 60)
    print("TRAINING PRODUCTION FORECASTER")
    print("=" * 60)
    
    prod_forecaster, prod_train, prod_test = train_production_model(
        n_days=args.n_days,
        freq_hours=args.freq_hours,
        test_size=args.test_size,
        random_state=args.random_state,
        save_path=str(output_dir / "production_forecaster.joblib")
    )
    
    all_results["production_forecaster"] = {
        "train_metrics": prod_train,
        "test_metrics": prod_test,
        "feature_count": len(prod_forecaster.feature_names) if prod_forecaster.feature_names else 0
    }
    
    # Train risk model(s)
    risk_targets = []
    if args.train_both_risks:
        risk_targets = ["rod_float_risk", "impact_loading_risk"]
    else:
        risk_targets = [args.risk_target]
    
    for risk_target in risk_targets:
        print("\n" + "=" * 60)
        print(f"TRAINING RISK PREDICTOR: {risk_target.upper()}")
        print("=" * 60)
        
        risk_predictor, risk_train, risk_test = train_risk_model(
            risk_target=risk_target,
            n_days=args.n_days,
            freq_hours=args.freq_hours,
            test_size=args.test_size,
            random_state=args.random_state,
            save_path=str(output_dir / f"risk_predictor_{risk_target}.joblib")
        )
        
        all_results[f"risk_predictor_{risk_target}"] = {
            "train_metrics": risk_train,
            "test_metrics": risk_test,
            "feature_count": len(risk_predictor.feature_names) if risk_predictor.feature_names else 0
        }
    
    # Save metrics summary
    metrics_path = output_dir / "training_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE - SUMMARY")
    print("=" * 60)
    for model_name, results in all_results.items():
        print(f"\n{model_name}:")
        print(f"  Train MAE: {results['train_metrics'].get('train_mae', 'N/A'):.4f}")
        print(f"  Test MAE:  {results['test_metrics'].get('test_mae', 'N/A'):.4f}")
        print(f"  Test R²:   {results['test_metrics'].get('test_r2', 'N/A'):.4f}")
        print(f"  Features:  {results['feature_count']}")
    
    print(f"\nMetrics saved to: {metrics_path}")
    print(f"Models saved to:  {output_dir.absolute()}")
    print("\nREMINDER: Models trained on SYNTHETIC/DEMO DATA only.")
    print("          Not validated against real Baghewala/OIL field data.")


if __name__ == "__main__":
    main()