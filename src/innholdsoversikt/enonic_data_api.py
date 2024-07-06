# %%
import logging
import time

from tqdm.auto import tqdm
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# %%
def eksport_innhold_enonic(
    branch: str, query: str, types: str, fields: str, filnavn: str
):
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
    filnavn: str, påkrevd
        navn og sti til filen du skal lagre dataene i

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
    logging.info("Response object:")
    for key, value in json_response.items():
        logging.info("%s : %s \n", key, value)
    result_url = json_response["resultUrl"]
    request_id = json_response["requestId"]
    header_status = 0
    while header_status != 200:
        status_response = s.get(result_url, headers=headers, stream=True, timeout=600)
        status_response.raise_for_status()

        if status_response.status_code == 202:
            json_response = status_response.json()
            logging.info("File is being prepared")
            for key, value in json_response.items():
                logging.info("%s : %s \n", key, value)
            time.sleep(5)
        elif status_response.status_code == 200:
            logging.info("File is ready. Writing data to %s", filnavn)
            with tqdm.wrapattr(
                open(innhold_data, "wb"),
                "write",
                miniters=1,
                total=int(status_response.headers.get("content-length", 0)),
                desc=innhold_data,
            ) as fout:
                for chunk in status_response.iter_content(chunk_size=8192):
                    fout.write(chunk)
            header_status = 200
        else:
            logging.info(
                "An error occurred, retrying to reach request ID %s and request URL %s in 10 seconds",
                request_id,
                result_url,
            )
            time.sleep(10)
    return innhold_data
