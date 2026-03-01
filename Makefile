.PHONY: install run test init-db

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

run:
	python -m src.bot.main

test:
	pytest -q

init-db:
	python scripts/init_db.py
