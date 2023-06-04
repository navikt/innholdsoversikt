FROM python:3.10-slim-buster AS compile-image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY ["requirements/main.txt", "main.txt"]
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r main.txt

FROM python:3.9-slim-buster AS build-image
RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python
USER 999
WORKDIR /app
COPY --chown=python:python --from=compile-image /opt/venv /opt/venv
COPY /innholdsoversikt .
USER 999
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV GCP_BQ_OPPDATERING_CREDS=secrets.json
CMD [ "python", "main.py" ]