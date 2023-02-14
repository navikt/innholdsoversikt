# %%
import logging
import time

from tqdm.auto import tqdm
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
# %%
def eksport_innhold_enonic(branch, query, types, fields, filnavn):
    """
    Last ned innhold fra Enonic XP

    Les også https://github.com/navikt/nav-enonicxp-dataquery

    Parametre
    ---------
    branch: str, påkrevd
        published eller unpublished, for å hente innhold på nettstedet idag og innhold som er avpublisert
    query: str, valgfritt
        NoQL query string (se dokumentasjon) - hvis tom hentes alt innhold fra branchen
    types: str, valgfritt
        array av content-typer queryet skal kjøres mot - hvis tom benyttes default-typer
    fields: str, valgfritt
        array av felter som skal returneres for hvert treff - hvis tom returneres alle felter

    Returnerer
    ----------
    innhold_data: zip-fil som inneholder innholdet fra Enonic som matcher søket
    """
    innhold_data = filnavn
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    response = s.get(
        "https://nav-enonicxp-dataquery.intern.nav.no/query",
        params={"branch": branch, "query": query, "types": types, "fields": fields},
        headers=headers,
        stream=True,
        timeout=600,
    )
    response.raise_for_status()
    json_response = response.json()
    print("Entire JSON response")
    for key, value in json_response.items():
        print(key, ":", value, "\n")
    result_url = json_response["resultUrl"]
    request_id = json_response["requestId"]
    header_status = ""
    while header_status != 200:
        status_response = s.get(result_url, headers=headers, stream=True, timeout=600)
        status_response.raise_for_status()

        if status_response.status_code == 202:
            json_response = status_response.json()
            print("File is being prepared")
            for key, value in json_response.items():
                print(key, ":", value, "\n")
            print(status_response.headers)
            time.sleep(5)
        elif status_response.status_code == 200:
            with tqdm.wrapattr(
                open(innhold_data, "wb"),
                "write",
                miniters=1,
                total=int(status_response.headers.get("content-length", 0)),
                desc=innhold_data,
            ) as fout:
                print(status_response.headers)
                for chunk in status_response.iter_content(chunk_size=8192):
                    fout.write(chunk)
            header_status = 200
        else:
            print(
                f"An error occurred, retrying to reach request ID {request_id} and request URL {result_url} in 10 seconds"
            )
            time.sleep(10)
    return innhold_data
