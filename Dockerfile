# Stage 1: Build and install Python dependencies
FROM python:3.10-slim-bookworm AS compile-image

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python virtual environment
RUN python -m venv $VIRTUAL_ENV

# Set working directory
WORKDIR /app

# Install system build dependencies (only during this stage)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY pyproject.toml .
RUN pip install --upgrade pip \
    && pip install pip-tools \
    && pip-compile --output-file=requirements.txt pyproject.toml \
    && pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────

# Stage 2: Runtime image
FROM python:3.10-slim-bookworm AS build-image

# Create non-root user
RUN groupadd -g 999 python && useradd -r -u 999 -g python python

USER python
WORKDIR /app

# Copy virtualenv from build stage
COPY --chown=python:python --from=compile-image /opt/venv /opt/venv

# Copy source code
COPY --chown=python:python src/innholdsoversikt .

# Set environment and entrypoint
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV GCP_BQ_OPPDATERING_CREDS=secrets.json

CMD ["python", "main.py"]