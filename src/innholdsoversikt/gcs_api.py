# %%
import logging

from google.cloud import storage

logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# %%
def opprett_mappe(client, bucket_name, location, storage_class):
    """
    Opprett ny mappe i google cloud storage for å lagre filer i et datasenter med lagringstype.

    Parametre:
    ---------

    client: påkrevd
        JSON for å bruke service konto med google cloud tjenester

    bucket_name: str, påkrevd
        Hva skal mappen med innholdet hete? Se også https://cloud.google.com/storage/docs/naming-buckets

    location: str, påkrevd
        Hvor skal dataene lagres? F.eks EUROPE-NORTH1 for Finland og EUROPE-WEST1 for Belgia. Se også https://cloud.google.com/storage/docs/locations

    storage_class: str, påkrevd
        Hvilken type lagring skal mappen ha? F.eks COLDLINE for minimum 90 dager og STANDARD for minimum null dager. Se også https://cloud.google.com/storage/docs/storage-classes

    Returnerer:
    ----------
    new_bucket: den nye mappen
    """
    client = storage.Client.from_service_account_json(client)
    bucket = client.bucket(bucket_name)
    bucket.storage_class = storage_class
    new_bucket = client.create_bucket(bucket, location=location)

    logging.info(
        "Opprettet mappen %s i %s med storage class %s.",
        bucket_name,
        location,
        storage_class,
    )
    return new_bucket


# %%
def last_opp_fil(client, bucket_name, source_file_name, destination_blob_name):
    """
    Last opp en fil til en mappe i google cloud storage.

    Parametre:
    ----------

    client: påkrevd
        Client for å bruke service konto med google cloud tjenester

    bucket_name: str, påkrevd
        Hva heter mappen du skal laste opp innholdet til?

    source_file_name: str, påkrevd
        Stien og navnet på filen du skal laste opp

    destination_blob_name: str, påkrevd
        Hva skal filen hete når den er lastet opp i mappen?

    """
    client = storage.Client.from_service_account_json(client)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    logging.info(
        "Filen %s ble lastet opp som %s", source_file_name, destination_blob_name
    )


# %%
def hent_liste_mapper(client):
    """
    Last ned en liste med mapper i GCS
    """
    client = storage.Client.from_service_account_json(client)
    buckets = list(client.list_buckets())
    logging.info("Lasted ned en liste med mapper")
    return buckets


# %%
def hent_liste_blobs(client, bucket_name):
    """
    Last ned en liste over alt innhold i en mappe i GCS
    """
    client = storage.Client.from_service_account_json(client)
    blobs = client.list_blobs(bucket_name)
    logging.info("Lastet ned en liste med blobs i mappen %s", bucket_name)
    return blobs


# %%
def last_ned_fil(client, bucket_name, source_blob_name, destination_file_name):
    """
    Last ned en fil fra GCS til en sti
    """
    client = storage.Client.from_service_account_json(client)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    logging.info(
        "Lastet ned %s fra mappen %s lokalt til %s",
        source_blob_name,
        bucket_name,
        destination_file_name,
    )


# %%
def last_ned_i_minne(client, bucket_name, source_blob_name):
    """
    Last en fil fra GCS inn i minne
    """
    client = storage.Client.from_service_account_json(client)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    contents = blob.download_as_string()
    logging.info("Lastet %s inn i minne fra mappen %s", source_blob_name, bucket_name)
    return contents


# %%
def slett_fil(client, bucket_name, source_blob_name):
    """
    Slett en fil fra GCS
    """
    client = storage.Client.from_service_account_json(client)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.delete()
    logging.info("Blob %s slettet fra mappen %s", source_blob_name, bucket_name)
