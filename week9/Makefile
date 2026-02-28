PYTHONPATH=.

run:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8002

test:
	PYTHONPATH=. pytest -q backend/tests
