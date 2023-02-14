# %%
import sys
import os
import json
import time
import zipfile
import logging

import pandas as pd
import numpy as np
from google.cloud import bigquery

from bygg_df import bygg_dataframe
from enonic_data_api import eksport_innhold_enonic
from bq_tabell_jobber import oppdater_tabell, skrivover_tabell, oppdater_tabell_csv
from gcs_api import last_opp_fil, hent_liste_blobs
from get_url import url_parser

# %%
DATA = ""
client = os.environ["GCP_BQ_OPPDATERING_CREDS"]
with open(os.environ["GCP_BQ_OPPDATERING_CREDS"], "r") as keys:
    data = keys.read()
obj = json.loads(data)
project_id = obj["project_id"]
location = "europe-north1"
dataset_id = "navno_innholdsmengde"
dataset_id_backup = "navno_innholdsmengde_backup"
mappe = "enonic_content_data"
# %%
def goalpost(client, mappe):
    blobs = hent_liste_blobs(client, mappe)
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
        DATA = True
    else:
        DATA = False
    return DATA, current


# %%


def forbered_filsti(filename):
    timestr = time.strftime("%Y%m%d")
    modsti = timestr + filename
    for char in "/-":
        modsti = modsti.replace(char, "_")
    return modsti


def eksport_arkivert():
    filnavn = "/tmp/enonic-arkivert.zip"
    eksport_innhold_enonic(
        branch="archived", query="", types="", fields="", filnavn=filnavn
    )
    logging.info("Lastet ned %s", filnavn)
    last_opp_fil(
        client=client,
        bucket_name=mappe,
        source_file_name=filnavn,
        destination_blob_name=forbered_filsti(filnavn),
    )
    logging.info("Lastet opp rådataene %s til GCP", filnavn)
    with zipfile.ZipFile(filnavn, "r") as my_zip:
        my_zip.extractall("/tmp/enonic-arkivert")
    return filnavn


def eksport_avpublisert():
    filnavn = "/tmp/enonic-avpublisert.zip"
    eksport_innhold_enonic(
        branch="unpublished", query="", types="", fields="", filnavn=filnavn
    )
    logging.info("Lastet ned %s", filnavn)
    last_opp_fil(
        client=client,
        bucket_name=mappe,
        source_file_name=filnavn,
        destination_blob_name=forbered_filsti(filnavn),
    )
    logging.info("Lastet opp rådataene %s til GCP", filnavn)
    with zipfile.ZipFile(filnavn, "r") as my_zip:
        my_zip.extractall("/tmp/enonic-avpublisert")
    return filnavn


def eksport_publisert():
    filnavn = "/tmp/enonic-publisert.zip"
    eksport_innhold_enonic(
        branch="published", query="", types="", fields="", filnavn=filnavn
    )
    logging.info("Lastet ned %s", filnavn)
    last_opp_fil(
        client=client,
        bucket_name=mappe,
        source_file_name=filnavn,
        destination_blob_name=forbered_filsti(filnavn),
    )
    logging.info("Lastet opp rådataene %s til GCP", filnavn)
    with zipfile.ZipFile(filnavn, "r") as my_zip:
        my_zip.extractall("/tmp/enonic-publisert")
    return filnavn


# %%


def forbered_innholdsoversikt_datasett():
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
    df["customPath"] = df["customPath"].str.replace(r"^\/", "https://www.nav.no/")
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
def innholdsoversikt_kolonner(df):
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


def innholdsoversikt_datoer(df):
    df["dato"] = pd.Series(
        pd.date_range(start="today", end="today", periods=len(df)).normalize()
    )
    df["createdTime"] = pd.to_datetime(df["createdTime"])
    df["createdTime"] = df["createdTime"].dt.date
    df["modifiedTime"] = pd.to_datetime(df["modifiedTime"])
    df["modifiedTime"] = df["modifiedTime"].dt.date
    df["publishFirst"] = pd.to_datetime(df["publishFirst"])
    df["publishFirst"] = df["publishFirst"].dt.date
    df["publishFrom"] = pd.to_datetime(df["publishFrom"])
    df["publishFrom"] = df["publishFrom"].dt.date
    logging.info("Innholdsoversikt steg 3: Sett datoer")
    return df


# %%
def datasett_sideprodukt(df):
    df_filtered = df.explode("produktType")
    df_sideprodukt = df_filtered[["_id", "produktType", "dato"]]
    df_sideprodukt["produktType"] = df_sideprodukt["produktType"].map(
        {
            "benefits": "pengestøtte",
            "followup": "oppfølging",
            "rights": "veiledning",
            "measures": "tiltak",
            "for_employers": "for arbeidsgivere",
            "for_providers": "for samarbeidspartnere",
        }
    )
    logging.info("Datasett %s er klart", df_sideprodukt)
    return df_sideprodukt


def datasett_produkt(df_sideprodukt):
    uniques = list(filter(None, df_sideprodukt["produktType"].unique()))
    df_produkt = pd.DataFrame(uniques, columns=["produktType"])
    logging.info("Datasett %s er klart", df_produkt)
    return df_produkt


def datasett_sideomrade(df):
    df_filtered = df.explode("omrade")
    df_sideomrade = df_filtered[["_id", "omrade", "dato"]]

    df_sideomrade["omrade"] = df_sideomrade["omrade"].map(
        {
            "social_counselling": "økonomisk sosialhjelp, råd og veiledning",
            "family": "familie og barn",
            "health": "helse og sykdom",
            "work": "arbeid",
            "accessibility": "hjelpemidler og tilrettelegging",
            "pension": "pensjon",
        }
    )
    logging.info("Datasett %s er klart", df_sideomrade)
    return df_sideomrade


def datasett_omrade(df_sideomrade):
    uniques = list(filter(None, df_sideomrade["omrade"].unique()))
    df_omrade = pd.DataFrame(uniques, columns=["omrade"])
    logging.info("Datasett %s er klart", df_omrade)
    return df_omrade


# %%


def lastopp_innholdsoversikt_db(df):
    typer_sider = {
        "no.nav.navno:situation-page": "side",
        "no.nav.navno:dynamic-page": "side",
        "no.nav.navno:content-page-with-sidemenus": "side",
        "no.nav.navno:main-article": "side",
        "no.nav.navno:section-page": "side",
        "no.nav.navno:page-list": "side",
        "no.nav.navno:transport-page": "side",
        "no.nav.navno:office-information": "side",
        "no.nav.navno:publishing-calendar": "side",
        "no.nav.navno:large-table": "side",
        "no.nav.navno:employer-situation-page": "side",
        "no.nav.navno:guide-page": "side",
        "no.nav.navno:front-page": "side",
        "no.nav.navno:area-page": "side",
        "no.nav.navno:main-article-chapter": "side",
        "no.nav.navno:themed-article-page": "side",
        "no.nav.navno:tools-page": "side",
        "no.nav.navno:overview": "side",
        "no.nav.navno:generic-page": "side",
        "no.nav.navno:melding": "side",
        "media:text": "vedlegg",
        "media:document": "vedlegg",
        "media:spreadsheet": "vedlegg",
        "media:presentation": "vedlegg",
    }
    df["kategorier"] = df["innholdstype"].map(typer_sider)
    df.drop(columns=["produktType", "omrade"], inplace=True)
    schema = [
        bigquery.SchemaField("_id", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("status", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("innholdstype", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("createdTime", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("modifiedTime", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("url", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("dato", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("kategorier", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("publishFirst", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("publishFrom", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("level_1", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("level_2", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("level_3", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("level_4", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("level_5", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("level_6", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("level_7", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("level_8", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("level_9", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("level_10", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("sidetittel", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("malgruppe", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("kortUrl", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("sprak", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("eier", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("forvaltetAv", bigquery.enums.SqlTypeNames.STRING),
    ]
    df.to_csv("/tmp/data.csv", index=False)
    oppdater_tabell_csv(
        client, "navno_innholdsmengde.innhold_tidsserie", "data.csv", "/tmp/data.csv"
    )
    logging.info("Innholdsoversikt steg 4: Lastet opp til database")


def lastopp_csv():
    last_opp_fil(
        client=client,
        bucket_name="enonic_data_csv",
        source_file_name="/tmp/data.csv",
        destination_blob_name=forbered_filsti("/tmp/data.csv"),
    )
    logging.info("Innholdsoversikt steg 5: CSV backup lastet opp")


# %%
def lastopp_sideomrade(df_sideomrade):
    schema = [
        bigquery.SchemaField("_id", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("omrade", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("dato", bigquery.enums.SqlTypeNames.DATE),
    ]
    oppdater_tabell(df_sideomrade, client, "navno_innholdsmengde.side_omrade", schema)
    logging.info("Oppdatert tabell om sideområdene")


def lastopp_sideprodukt(df_sideprodukt):
    schema = [
        bigquery.SchemaField("_id", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("produktType", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("dato", bigquery.enums.SqlTypeNames.DATE),
    ]
    oppdater_tabell(df_sideprodukt, client, "navno_innholdsmengde.side_produkt", schema)
    logging.info("Oppdatert tabell om sideproduktene")


# %%
def lastopp_omrade(df_omrade):
    # nye områder
    bq_client = bigquery.Client.from_service_account_info(obj)
    result = bq_client.query("SELECT * FROM navno_innholdsmengde.omrade")
    df_temp = result.to_dataframe()
    df_temp.fillna(np.nan, inplace=True)
    df_new = pd.concat([df_temp, df_omrade]).drop_duplicates()
    schema = [bigquery.SchemaField("omrade", bigquery.enums.SqlTypeNames.STRING)]
    skrivover_tabell(df_new, client, "navno_innholdsmengde.omrade", schema)
    logging.info("Oppdatert tabell om områdene")


def lastopp_produkt(df_omrade):
    # nye produkter
    bq_client = bigquery.Client.from_service_account_info(obj)
    result = bq_client.query("SELECT * FROM navno_innholdsmengde.produkt")
    df_temp = result.to_dataframe()
    df_temp.fillna(np.nan, inplace=True)
    df_new = pd.concat([df_temp, df_omrade]).drop_duplicates()
    schema = [bigquery.SchemaField("produktType", bigquery.enums.SqlTypeNames.STRING)]
    skrivover_tabell(df_new, client, "navno_innholdsmengde.produkt", schema)
    logging.info("Oppdatert tabell om produktene")


# %%
def lastopp_innholdsmengde_total(df):
    innholdsmengde = (
        df.groupby(["innholdstype", "status"])
        .agg({"_id": "count"})
        .sort_values(by=["_id"], ascending=False)
    )
    innholdsmengde.reset_index(inplace=True)
    innholdsmengde.rename(columns={"_id": "antall"}, inplace=True)
    innholdsmengde["dato"] = pd.Series(
        pd.date_range(
            start="today", end="today", periods=len(innholdsmengde)
        ).normalize()
    )
    innholdsmengde["datakilde"] = "enonic"
    typer_sider = {
        "no.nav.navno:situation-page": "side",
        "no.nav.navno:dynamic-page": "side",
        "no.nav.navno:content-page-with-sidemenus": "side",
        "no.nav.navno:main-article": "side",
        "no.nav.navno:section-page": "side",
        "no.nav.navno:page-list": "side",
        "no.nav.navno:transport-page": "side",
        "no.nav.navno:office-information": "side",
        "no.nav.navno:publishing-calendar": "side",
        "no.nav.navno:large-table": "side",
        "no.nav.navno:employer-situation-page": "side",
        "no.nav.navno:guide-page": "side",
        "no.nav.navno:front-page": "side",
        "no.nav.navno:area-page": "side",
        "no.nav.navno:main-article-chapter": "side",
        "no.nav.navno:themed-article-page": "side",
        "no.nav.navno:tools-page": "side",
        "no.nav.navno:overview": "side",
        "no.nav.navno:generic-page": "side",
        "no.nav.navno:melding": "side",
        "media:text": "vedlegg",
        "media:document": "vedlegg",
        "media:spreadsheet": "vedlegg",
        "media:presentation": "vedlegg",
    }
    innholdsmengde["kategorier"] = innholdsmengde["innholdstype"].map(typer_sider)
    schema = [
        bigquery.SchemaField("status", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("innholdstype", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("antall", bigquery.enums.SqlTypeNames.INTEGER),
        bigquery.SchemaField("dato", bigquery.enums.SqlTypeNames.DATE),
        bigquery.SchemaField("datakilde", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("kategorier", bigquery.enums.SqlTypeNames.STRING),
    ]
    oppdater_tabell(
        innholdsmengde, client, "navno_innholdsmengde.innhold_aggregert", schema
    )
    logging.info("Lastet opp metrikker til gammel oversiktstabell")


# %%


def main():
    state, current = goalpost(client, mappe)
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
        df_sideprodukt = datasett_sideprodukt(df)
        df_sideomrade = datasett_sideomrade(df)
        df_produkt = datasett_produkt(df_sideprodukt)
        df_omrade = datasett_omrade(df_sideomrade)
        lastopp_innholdsoversikt_db(df)
        lastopp_csv()
        lastopp_sideomrade(df_sideomrade)
        lastopp_sideprodukt(df_sideprodukt)
        lastopp_omrade(df_omrade)
        lastopp_produkt(df_omrade)
        lastopp_innholdsmengde_total(df)
        logging.info("Naisjob er ferdig")
    elif state == True:
        logging.info(
            "Vi har data for %s. Stopper naisjob. Flagget er %s", current, state
        )
        sys.exit()


if __name__ == "__main__":
    main()