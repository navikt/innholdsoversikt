# %%
import logging

import pandas as pd
import requests
from urllib.parse import urlparse

logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# %%
def url_parser(url):
    parts = urlparse(url)
    directories = parts.path.strip("/").split("/")
    queries = parts.query.strip("&").split("&")
    elements = {
        "scheme": parts.scheme,
        "netloc": parts.netloc,
        "path": parts.path,
        "params": parts.params,
        "query": parts.query,
        "fragment": parts.fragment,
        "directories": directories,
        "queries": queries,
    }
    return elements
