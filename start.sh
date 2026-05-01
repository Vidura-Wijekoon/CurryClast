#!/bin/bash
echo "🚀 CurryCast Backend Initializing..."

# Generate data if it doesn't exist
if [ ! -f "data/synthetic/transactions.parquet" ]; then
    echo "📊 No data found. Generating synthetic data..."
    python scripts/generate_synthetic_data.py
fi

# Train model if it doesn't exist
if [ ! -f "data/models/currycast_model.pkl" ]; then
    echo "🧠 No model found. Training..."
    python scripts/train_model.py
fi

echo "✨ Starting API Service..."
uvicorn src.api.service:app --host 0.0.0.0 --port 7860
