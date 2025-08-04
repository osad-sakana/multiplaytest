FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install poetry==1.6.1

# Copy poetry configuration
COPY pyproject.toml poetry.lock* ./

# Configure poetry
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-dev

COPY server/ ./

EXPOSE 8000

CMD ["python", "main.py"]