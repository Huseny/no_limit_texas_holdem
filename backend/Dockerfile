# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copy only dependency files first for caching
COPY pyproject.toml ./

# Install dependencies (no virtualenvs inside container)
ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --no-interaction --no-root

# Copy rest of the app
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the app
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
