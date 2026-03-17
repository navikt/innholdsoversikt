# Stage 1: Build and install Python dependencies
FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:3.14-dev AS builder

USER root

# Set working directory
WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python virtual environment
RUN python -m venv /opt/venv

# Install system build dependencies (Wolfi/apk)
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    postgresql-dev \
    ca-certificates

# Copy and install Python dependencies
COPY requirements/prod.txt ./requirements/prod.txt
COPY pyproject.toml .
COPY src/ src/

RUN pip install --upgrade pip \
 && pip install --no-cache-dir build wheel setuptools \
 && pip install --no-cache-dir -r requirements/prod.txt \
 && pip install --no-cache-dir --no-deps .

# ─────────────────────────────────────────────────────────

# Stage 2: Runtime image (distroless)
FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:3.14 AS runtime

WORKDIR /app

# Set environment and entrypoint
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV GCP_BQ_OPPDATERING_CREDS=secrets.json

# Copy virtualenv from build stage
COPY --from=builder /opt/venv /opt/venv

# Copy source code
COPY src/innholdsoversikt/ ./

CMD ["main.py"]