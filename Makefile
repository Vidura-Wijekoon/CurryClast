# CurryCast convenience commands

.PHONY: install data train predict backtest dashboard api test clean

install:
	pip install -r requirements.txt

data:
	python scripts/generate_synthetic_data.py

train:
	python scripts/train_model.py

predict:
	python scripts/predict_tomorrow.py

backtest:
	python scripts/run_backtest.py --holdout-days 30

dashboard:
	streamlit run dashboard/app.py

api:
	uvicorn src.api.service:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

clean:
	rm -rf data/processed/* data/models/* data/synthetic/*
	find . -type d -name __pycache__ -exec rm -rf {} +
