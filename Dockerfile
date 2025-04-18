FROM python:3.10-slim-buster AS compile-image
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV
WORKDIR /app
COPY ["requirements/main.txt", "main.txt"]
RUN pip install --upgrade pip && pip install --no-cache-dir -r main.txt

FROM python:3.10-slim-buster AS build-image
RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python
USER 999
WORKDIR /app
COPY --chown=python:python --from=compile-image /opt/venv /opt/venv
COPY /src/innholdsoversikt .
USER 999
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV GCP_BQ_OPPDATERING_CREDS=secrets.json
CMD ["python", "main.py"]
