# %%
import json
import logging

import numpy as np
import pandas as pd

from parse_json import extract_element_from_json

logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# %%
def bygg_dataframe(liste: list) -> pd.DataFrame:
    """
    Bygg en dataframe for vår tidsserie om innholdet. Send inn en liste med json-filer som skal søkes i.

    Returnerer en dataframe med alle metadataene som ble funnet i json-filene.

    Parametre
    ---------
    liste: list, påkrevd
        Liste med json-filer som du skal bygge datasettet med
    Returnerer
    ---------
    df: en dataframe med tidsserie for innholdet
    """

    list_id = []
    list_type = []
    list_created_time = []
    list_modified_time = []
    list_publish_first = []
    list_publish_from = []
    list_path = []
    list_displayName = []
    list_data_owner = []
    list_data_managedby = []
    list_data_taxonomy = []
    list_data_area = []
    list_data_audience = []
    list_data_customPath = []
    list_language = []

    for i in liste:
        with open(i, "r") as thefile:
            j: dict | list[dict] = json.load(thefile)
            try:
                list_id.append(extract_element_from_json(j, ["_id"]))
                list_type.append(extract_element_from_json(j, ["type"]))
                list_created_time.append(extract_element_from_json(j, ["createdTime"]))
                list_modified_time.append(
                    extract_element_from_json(j, ["modifiedTime"])
                )
                list_path.append(extract_element_from_json(j, ["_path"]))
                list_publish_first.append(
                    extract_element_from_json(j, ["publish", "first"])
                )
                list_publish_from.append(
                    extract_element_from_json(j, ["publish", "from"])
                )
                list_displayName.append(extract_element_from_json(j, ["displayName"]))
                list_data_owner.append(extract_element_from_json(j, ["data", "owner"]))
                list_data_managedby.append(
                    extract_element_from_json(j, ["data", "managed-by"])
                )
                list_data_taxonomy.append(
                    extract_element_from_json(j, ["data", "taxonomy"])
                )
                list_data_area.append(extract_element_from_json(j, ["data", "area"]))
                list_data_audience.append(
                    extract_element_from_json(j, ["data", "audience"])
                )
                list_data_customPath.append(
                    extract_element_from_json(j, ["data", "customPath"])
                )
                list_language.append(extract_element_from_json(j, ["language"]))
            except KeyError:
                list_id.append([None])
                list_type.append([None])
                list_created_time.append([None])
                list_modified_time.append([None])
                list_path.append([None])
                list_publish_first.append([None])
                list_publish_from.append([None])
                list_displayName.append([None])
                list_data_owner.append([None])
                list_data_managedby.append([None])
                list_data_taxonomy.append([None])
                list_data_area.append([None])
                list_data_audience.append([None])
                list_data_customPath.append([None])
                list_language.append([None])
    df = pd.DataFrame(
        {
            "_id": [item for sublist in list_id for item in sublist],
            "type": [item for sublist in list_type for item in sublist],
            "createdTime": [item for sublist in list_created_time for item in sublist],
            "modifiedTime": [
                item for sublist in list_modified_time for item in sublist
            ],
            "publishFirst": [
                item for sublist in list_publish_first for item in sublist
            ],
            "publishFrom": [item for sublist in list_publish_from for item in sublist],
            "_path": [item for sublist in list_path for item in sublist],
            "displayName": [item for sublist in list_displayName for item in sublist],
            "owner": [item for sublist in list_data_owner for item in sublist],
            "managedBy": [item for sublist in list_data_managedby for item in sublist],
            "taxonomy": [item for sublist in list_data_taxonomy for item in sublist],
            "area": [item for sublist in list_data_area for item in sublist],
            "audience": [item for sublist in list_data_audience for item in sublist],
            "customPath": [
                item for sublist in list_data_customPath for item in sublist
            ],
            "language": [item for sublist in list_language for item in sublist],
        }
    )
    logging.info("Bygget dataframe")
    return df


# %%
def finn_data(items: list, query: list) -> list:
    """
    Bygg en dataframe for vår tidsserie om innholdet. Send inn en liste med json-filer som skal søkes i.

    Returnerer en dataframe med alle metadataene som ble funnet i json-filene.

    Parametre
    ---------
    items: list, påkrevd
        Liste med json-filer som du skal bygge datasettet med
    query: list, påkrevd
        Spørring på felt du er ute etter, f.eks ["data", "capitol"] for data.capitol i json
    Returnerer
    ---------
    df: en dataframe med tidsserie for innholdet
    """
    found = []
    for i in items:
        with open(i, "r") as thefile:
            j = json.load(thefile)
            try:
                found.append(extract_element_from_json(j, query))
            except KeyError:
                found.append([None])
    return found
