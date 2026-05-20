FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 5000

CMD ["sh", "-c", "poetry run flask --app app.py reset_db && poetry run flask --app app.py seed_db && poetry run flask --app app.py run --host=0.0.0.0 --port=5000"]
