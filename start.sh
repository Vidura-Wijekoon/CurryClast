#!/bin/bash
echo "🚀 CurryCast Backend Initializing..."

# Generate data if it doesn't exist
if [ ! -f "data/synthetic/transactions.parquet" ]; then
    echo "📊 No data found. Generating synthetic data..."
    python scripts/generate_synthetic_data.py
fi

# Run training pipeline (handles staleness check internally)
echo "🧠 Checking model/data freshness..."
python scripts/train_model.py

echo "✨ Starting API Service..."
uvicorn src.api.service:app --host 0.0.0.0 --port 7860
