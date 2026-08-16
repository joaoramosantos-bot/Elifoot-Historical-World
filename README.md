# Elifoot Historical World

Backend inicial de um simulador histórico e dinâmico de futebol.

## Stack
- Python 3.12+
- FastAPI
- SQLAlchemy
- SQLite
- Alembic
- Pytest

## Arranque
```bash
python -m venv .venv
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

A API fica em `http://127.0.0.1:8000/docs`.

O mundo começa em 1900-09-01 e o calendário avança por meses reais.
