# Stage 1: Build and install Python dependencies
FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:3.14-dev AS builder

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# Install system build dependencies with security updates (only during this stage)
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    openssl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
RUN python -m venv /opt/venv

COPY requirements/prod.txt ./requirements/
COPY pyproject.toml .
COPY src/ src/

RUN pip install --upgrade pip \
 && pip install --no-cache-dir build wheel setuptools \
 && pip install --no-cache-dir -r requirements/prod.txt \
 && pip install --no-cache-dir --no-deps .

# ─────────────────────────────────────────────────────────

# Stage 2: Runtime image (distroless)
FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:3.14 AS runtime

# Copy source code
COPY --chown=python:python src/innholdsoversikt .

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV GCP_BQ_OPPDATERING_CREDS=secrets.json

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

CMD ["python", "main.py"]