# %%
import sys
import os
import json
import time
import zipfile
import logging

import pandas as pd
from dotenv import load_dotenv

from bygg_df import bygg_dataframe
from enonic_data_api import eksport_innhold_enonic
from bq_tabell_jobber import oppdater_tabell_csv
from gcs_api import last_opp_fil, hent_liste_blobs
from get_url import url_parser

logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# %%
load_dotenv()

client_json = os.getenv(key="GCP_BQ_OPPDATERING_CREDS")
with open(client_json, "r") as keys:
    data = keys.read()
obj = json.loads(data)
project_id = obj["project_id"]
location = "europe-north1"
dataset_id = "navno_innholdsmengde"
dataset_id_backup = "navno_innholdsmengde_backup"
mappe = "enonic_content_data"


# %%
def goalpost(client_json: str, bucket_name: str) -> tuple[bool, str]:
    """
    Checks if we have archived, unpublished and published content stored in the cloud

    Parameters:
    -----------
    client_json: string, required
        Our credentials to use cloud services
    bucket_name: string, required
        Our blob storage folder in the cloud

    Returns:
    -------------------------
    got_data, bool is True if our folder contains the archived, unpublished and published content for today's date, otherwise returns False

    current is today's date in the format YYYYMMDD
    """
    blobs = hent_liste_blobs(client_json=client_json, bucket_name=bucket_name)
    d = list(blobs)
    fil_urler = []
    for i in d:
        fil_urler.append(i.public_url)
    current = time.strftime("%Y%m%d")
    arkivert = [i for i in fil_urler if current in i and "tmp_enonic_arkivert" in i]
    avpublisert = [
        i for i in fil_urler if current in i and "tmp_enonic_avpublisert" in i
    ]
    publisert = [i for i in fil_urler if current in i and "tmp_enonic_publisert" in i]
    if len(avpublisert) > 0 and len(publisert) > 0 and len(arkivert) > 0:
        got_data = True
    else:
        got_data = False
    return got_data, current


# %%


def forbered_filsti(filename: str) -> str:
    """
    Lager en filsti med dato
    """
    timestr = time.strftime("%Y%m%d")
    modsti = timestr + filename
    for char in "/-":
        modsti = modsti.replace(char, "_")
    return modsti


def eksport_arkivert() -> str:
    filnavn = "/tmp/enonic-arkivert.zip"
    eksport_innhold_enonic(
        branch="archived", query="", types="", fields="", filnavn=filnavn
    )
    logging.info("Lastet ned %s", filnavn)
    last_opp_fil(
        client_json=client_json,
        bucket_name=mappe,
        source_file_name=filnavn,
        destination_blob_name=forbered_filsti(filnavn),
    )
    logging.info("Lastet opp rådataene %s til GCP", filnavn)
    with zipfile.ZipFile(filnavn, "r") as my_zip:
        my_zip.extractall("/tmp/enonic-arkivert")
    return filnavn


def eksport_avpublisert() -> str:
    filnavn = "/tmp/enonic-avpublisert.zip"
    eksport_innhold_enonic(
        branch="unpublished", query="", types="", fields="", filnavn=filnavn
    )
    logging.info("Lastet ned %s", filnavn)
    last_opp_fil(
        client_json=client_json,
        bucket_name=mappe,
        source_file_name=filnavn,
        destination_blob_name=forbered_filsti(filnavn),
    )
    logging.info("Lastet opp rådataene %s til GCP", filnavn)
    with zipfile.ZipFile(filnavn, "r") as my_zip:
        my_zip.extractall("/tmp/enonic-avpublisert")
    return filnavn


def eksport_publisert() -> str:
    filnavn = "/tmp/enonic-publisert.zip"
    eksport_innhold_enonic(
        branch="published", query="", types="", fields="", filnavn=filnavn
    )
    logging.info("Lastet ned %s", filnavn)
    last_opp_fil(
        client_json=client_json,
        bucket_name=mappe,
        source_file_name=filnavn,
        destination_blob_name=forbered_filsti(filnavn),
    )
    logging.info("Lastet opp rådataene %s til GCP", filnavn)
    with zipfile.ZipFile(filnavn, "r") as my_zip:
        my_zip.extractall("/tmp/enonic-publisert")
    return filnavn


# %%


def forbered_innholdsoversikt_datasett() -> pd.DataFrame:
    pubsti = "/tmp/enonic-publisert/www.nav.no"
    avpubsti = "/tmp/enonic-avpublisert/www.nav.no"
    arksti = "/tmp/enonic-arkivert/archive"

    publisert = [
        os.path.join(path, name)
        for path, subdirs, files in os.walk(pubsti)
        for name in files
    ]
    avpublisert = [
        os.path.join(path, name)
        for path, subdirs, files in os.walk(avpubsti)
        for name in files
    ]
    arkivert = [
        os.path.join(path, name)
        for path, subdirs, files in os.walk(arksti)
        for name in files
    ]
    alt = publisert + avpublisert
    df = bygg_dataframe(alt)
    df_ark = bygg_dataframe(arkivert)
    df["status"] = [
        "publisert" if x is not None else "avpublisert" for x in df["publishFrom"]
    ]
    df_ark["status"] = [
        "arkivert" if x.startswith("/archive") else "mangler status"
        for x in df_ark["_path"]
    ]
    df["_path"] = df["_path"].str.replace("/www", "https://www")
    df["customPath"] = df["customPath"].str.replace(
        r"^\/", "https://www.nav.no/", regex=True
    )
    url_list = df["_path"].tolist()
    df_urls = pd.DataFrame([url_parser(i) for i in url_list])
    df_dirs = pd.DataFrame(
        df_urls["directories"].to_list(),
        columns=[
            "level_1",
            "level_2",
            "level_3",
            "level_4",
            "level_5",
            "level_6",
            "level_7",
            "level_8",
            "level_9",
            "level_10",
        ],
    )
    df = pd.concat([df, df_dirs], axis=1)
    df = pd.concat([df, df_ark])
    logging.info("Innholdsoversikt steg 1: Trakk ut metadata fra filene.")
    return df


# %%
def innholdsoversikt_kolonner(df: pd.DataFrame) -> pd.DataFrame:
    df.rename(
        columns={
            "type": "innholdstype",
            "_path": "url",
            "displayName": "sidetittel",
            "owner": "eier",
            "managedBy": "forvaltetAv",
            "taxonomy": "produktType",
            "area": "omrade",
            "audience": "malgruppe",
            "customPath": "kortUrl",
            "language": "sprak",
        },
        inplace=True,
    )
    logging.info("Innholdsoversikt steg 2: Sett navn på kolonner")
    return df


def innholdsoversikt_datoer(df: pd.DataFrame) -> pd.DataFrame:
    df["dato"] = pd.Series(
        pd.date_range(start="today", end="today", periods=len(df)).normalize()
    )
    df["createdTime"] = pd.to_datetime(df["createdTime"], format="ISO8601")
    df["createdTime"] = df["createdTime"].dt.date
    df["modifiedTime"] = pd.to_datetime(df["modifiedTime"], format="ISO8601")
    df["modifiedTime"] = df["modifiedTime"].dt.date
    df["publishFirst"] = pd.to_datetime(df["publishFirst"], format="ISO8601")
    df["publishFirst"] = df["publishFirst"].dt.date
    df["publishFrom"] = pd.to_datetime(df["publishFrom"], format="ISO8601")
    df["publishFrom"] = df["publishFrom"].dt.date
    logging.info("Innholdsoversikt steg 3: Sett datoer")
    return df


def innholdsoversikt_kategorisering(df: pd.DataFrame, sti: str):
    """
    Kategoriserer innholdet og skriver csv til ønsket sti
    """
    df["kategorier"] = [
        "vedlegg" if y.startswith("media") else "side" for y in df["innholdstype"]
    ]
    df.drop(columns=["produktType", "omrade"], inplace=True)
    df.to_csv(sti, index=False)
    logging.info(
        "Innholdsoversikt steg 4: innholdet er kategorisert og skrevet til csv ved %s",
        sti,
    )


# %%


def main():
    state, current = goalpost(client_json=client_json, bucket_name=mappe)
    if state == False:
        logging.info(
            "Vi har ikke data for %s. Fortsetter naisjob. Flagget er %s", current, state
        )
        eksport_arkivert()
        eksport_avpublisert()
        eksport_publisert()
        df = forbered_innholdsoversikt_datasett()
        df = innholdsoversikt_kolonner(df)
        df = innholdsoversikt_datoer(df)
        innholdsoversikt_kategorisering(df, sti="/tmp/data.csv")
        last_opp_fil(
            client_json=client_json,
            bucket_name="enonic_data_csv",
            source_file_name="/tmp/data.csv",
            destination_blob_name=forbered_filsti("/tmp/data.csv"),
        )
        logging.info("Innholdsoversikt steg 5: CSV backup lastet opp")
        oppdater_tabell_csv(
            client_json=client_json,
            table_id="navno_innholdsmengde.innhold_tidsserie",
            source_file="data.csv",
            file_path="/tmp/data.csv",
            json_schema_path="schema_tabell.json",
        )
        logging.info("Innholdsoversikt steg 6: Lastet opp til database")
        logging.info("Naisjob er ferdig")
    elif state == True:
        logging.info(
            "Vi har data for %s. Stopper naisjob. Flagget er %s", current, state
        )
        sys.exit()


if __name__ == "__main__":
    main()

# %%
