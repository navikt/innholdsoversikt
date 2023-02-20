# %%
import logging

from google.cloud import bigquery

logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# %%
def oppdater_tabell(df, client, table_id, schema):
    """
    Oppdatér datasett med append
    Les også https://cloud.google.com/bigquery/docs/samples/bigquery-load-table-dataframe

    Parametre
    ---------
    df: DataFrame, påkrevd
        DataFrame som du ønsker å oppdatere tabellen med
    client: object, påkrevd
        json for service account
    table_id: str, påkrevd
        ID for tabellen i bigquery som du ønsker å oppdatere med din DataFrame
    schema: påkrevd
        Schema for tabellen i bigquery. Kan være en liste om det er flere felt og typer.
    Returnerer
    ----------
    table: tabell med metadata fra bigquery
    """
    client = bigquery.Client.from_service_account_json(client)
    job_config = bigquery.LoadJobConfig(
        schema=schema, write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

    table = client.get_table(table_id)
    logging.info(
        "Tabellen %s har %s rader totalt og %s kolonner",
        table_id,
        table.num_rows,
        len(table.schema),
    )
    return table


# %%
def skrivover_tabell(df, client, table_id, schema):
    """
    Skriv over hele datasettet med en dataframe
    Les også https://cloud.google.com/bigquery/docs/samples/bigquery-load-table-dataframe

    Parametre
    ---------
    df: DataFrame, påkrevd
        DataFrame som du ønsker å skrive over tabellen med
    client: object, påkrevd
        json for service account
    table_id: str, påkrevd
        ID for tabellen i bigquery som du ønsker å skrive over med din DataFrame
    schema: påkrevd
        Schema for tabellen i bigquery. Kan være en liste om det er flere felt og typer.
    Returnerer
    ----------
    table: tabell med metadata fra bigquery
    """
    client = bigquery.Client.from_service_account_json(client)
    job_config = bigquery.LoadJobConfig(
        schema=schema, write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    table = client.get_table(table_id)
    logging.info(
        "Tabellen %s har %s rader totalt og %s kolonner",
        table_id,
        table.num_rows,
        len(table.schema),
    )


# %%
def opprett_tabell(client, table_id, schema):
    """
    Opprett en tabell i bigquery.

    Parametre
    ----------
    client: object, påkrevd
        json for service account
    table_id: str, påkrevd
        Navn på tabellen du ønsker å opprette i bigquery
    schema: påkrevd
        Schema for tabellen du ønsker å opprette. Kan være en liste.

    Returnerer
    ----------
    Tabellen du opprettet
    """
    client = bigquery.Client.from_service_account_json(client)
    schema = schema
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table)
    logging.info(
        "Opprettet tabellen %s.%s.%s", table.project, table.dataset_id, table.table_id
    )


# %%
def slett_tabell(client, table_id):
    """
    Slett en tabell i bigquery.

    Parametre
    ----------
    client: object, påkrevd
        json for service account
    table_id: str, påkrevd
        Navn på tabellen du ønsker å slette i bigquery

    Returnerer
    ----------
    Tabellen du slettet
    """
    client = bigquery.Client.from_service_account_json(client)
    client.delete_table(table_id, not_found_ok=True)
    logging.info("Slettet tabellen %s", table_id)


# %%
def opprett_datasett(client, dataset_id, location):
    """
    Oppretter et datasett. Du må opprette et datasett før du kan opprette en tabell i bigquery.

    Parametre
    ---------
    client: object, påkrevd
        json for service account
    dataset_id: str, påkrevd
        Hva skal datasettet hete?
    location: str, påkrevd
        Hvor skal databasen opprettes, f.eks europe-north1 for Finland og europe-west1 for Belgia
    """
    client = bigquery.Client.from_service_account_json(client)
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = location
    dataset = client.create_dataset(dataset, timeout=30)
    logging.info("Opprettet datasettet %s.%s", client.project, dataset.dataset_id)


# %%
def slett_datasett(client, dataset_id):
    """
    Sletter et datasett og alle tabellene i datasettet.

    Parametre
    ---------
    client: object, påkrevd
        json for service account
    dataset_id: str, påkrevd
        Hva heter datasettet?
    """
    client = bigquery.Client.from_service_account_json(client)
    client.delete_dataset(dataset_id, delete_contents=True, not_found_ok=False)
    logging.info("Slettet datasettet %s", dataset_id)


# %%
def legg_til_felt(client, table_id, schema):
    """
    For å legge til et felt i en tabell som eksisterer fra før.
    Obs! Tar 1 felt om gangen, og kolonnen blir regnet som NULLABLE, ikke REQUIRED.

    Parametre
    ---------
    client: object, påkrevd
        json for service account
    table_id: string, påkrevd
        Navn på tabellen du ønsker å endre
    schema: påkrevd
        Ny schema for feltet du ønsker å legge til

    Returnerer:
    -----------
    schema: oppdatert schema for tabellen
    """
    client = bigquery.Client.from_service_account_json(client)
    table = client.get_table(table_id)
    original_schema = table.schema
    new_schema = original_schema[:]
    new_schema.append(schema)
    table.schema = new_schema
    table = client.update_table(table, ["schema"])
    if len(table.schema) == len(original_schema) + 1 == len(new_schema):
        logging.info("Feltet %s har blitt lagt til tabellen %s", schema, table_id)
    else:
        logging.info("Feltet %s ble IKKE lagt til tabellen %s", schema, table_id)
    return table.schema


#%%
def oppdater_tabell_csv(client, table_id, source_file, file_path):
    """
    Oppdaterer en bigquery tabell med en csv-fil.

    Default så vil denne funksjonen kun legge til innholdet i filen til tabellen som nye rader.

    Parametre:
    ---------
    client: object, påkrevd
        json for service account
    table_id: string, påkrevd
        Id på tabellen du ønsker å oppdatere
    source_file: string, påkrevd
        filnavn
    file_path: string, påkrevd
        sti til filen
    """
    client = bigquery.Client.from_service_account_json(client)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1, autodetect=True
    )
    with open(file_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)
    job.result()
    table = client.get_table(table_id)
    logging.info(
        "Lastet %s rader og %s kolonner til %s",
        table.num_rows,
        len(table.schema),
        table_id,
    )


# %%
def oppdater_tabell_gcs(client, table_id, uri, schema):
    """
    Oppdatér en bigquery tabell med en csv fil fra google cloud storage

    Parametre:
    ---------
    client: object, påkrevd
        json for service account
    table_id: string, påkrevd
        id for tabellen som skal oppdateres
    uri: string, påkrevd
        ...
    schema: påkrevd
        schema for tabellen
    """
    client = bigquery.Client.from_service_account_json(client)
    job_config = bigquery.LoadJobConfig(
        schema=schema, skip_leading_rows=1, source_format=bigquery.SourceFormat.CSV
    )
    load_job = client.load_table_from_uri(uri, table_id, job_config=job_config)
    load_job.result()
    destination_table = client.get_table(table_id)
    logging.info("Lasted %s rader", destination_table.num_rows)


# %%
def oppdater_tabell_schema(client, table_id, schema):
    """
    Metoden tar en kopi av schema for tabellen og oppdaterer den med schema du sender inn.
    """
    client = bigquery.Client.from_service_account_json(client)
    table = client.get_table(table_id)
    original_schema = table.schema
    new_schema = original_schema[:]
    new_schema.append(schema)
    table.schema = new_schema
    table = client.update_table(table, ["schema"])
    if len(table.schema) > len(original_schema):
        logging.info("Nye kolonner har blitt lagt til")
    else:
        logging.info("Nye kolonner har IKKE blitt lagt til")


# %%
def get_schema(client, table_id):
    client = bigquery.Client.from_service_account_json(client)
    table = client.get_table(table_id)
    original_schema = table.schema
    logging.info("Hentet schema fra %s", table_id)
    return original_schema
