FROM python:3.9-slim-buster AS compile-image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY ["requirements.txt", "./"]
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim-buster AS build-image
RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python
USER 999
COPY --chown=python:python --from=compile-image /opt/venv /opt/venv
COPY ["bq_tabell_jobber.py", "enonic_data_api.py", "gcs_api.py", "main.py", "parse_json.py", "bygg_df.py", "get_url.py" ,"./"]
USER 999
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV GCP_BQ_OPPDATERING_CREDS=secrets.json
CMD [ "python", "main.py" ]