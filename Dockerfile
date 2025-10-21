# Stage 1: Build and install Python dependencies
FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:3.12-dev AS compile-image
WORKDIR /app

RUN python3 -m venv venv
ENV PATH=/app/venv/bin:$PATH

# Copy and install Python dependencies
# Copy the whole requirements dir to support includes
COPY requirements/ ./requirements/
COPY pyproject.toml .
COPY src/ src/

RUN pip install -r ./requirements/prod.txt

# ─────────────────────────────────────────────────────────

# Stage 2: Runtime image
FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:3.12 AS build-image

# Create non-root user
## RUN groupadd -g 999 python && useradd -r -u 999 -g python python

## USER python
WORKDIR /app

# Copy virtualenv from build stage
COPY --from=compile-image /app/venv /app/venv

# Copy source code
COPY src/innholdsoversikt .

# Set environment and entrypoint
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV GCP_BQ_OPPDATERING_CREDS=secrets.json

CMD ["python", "main.py"]