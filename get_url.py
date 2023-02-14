# %%
import pandas as pd
import requests
import xmltodict
from urllib.parse import urlparse

# %%
def get_url_from_sitemap(url: str) -> pd.DataFrame:
    """
    Parses an XML sitemap and returns all URLs as a DataFrame

    Parameters
    ---------
    url: str, required
        URL to the sitemap

    Returns
    ----------
    df = DataFrame
    """
    res = requests.get(url)
    raw = xmltodict.parse(res.text)

    data = [[r["loc"]] for r in raw["urlset"]["url"]]
    df = pd.DataFrame(data, columns=["links"])
    return df


# %%
def get_sitemaps_from_domain(domain: str) -> pd.DataFrame:
    """
    Gets all sitemaps from a sitemap index file if it exists for a given domain.

    Parameters:
    ---------
    domain: str, required
        URL to the sitemap index file
    """
    res = requests.get(domain)
    raw = xmltodict.parse(res.text)

    data = [[r["loc"]] for r in raw["sitemapindex"]["sitemap"]]
    df = pd.DataFrame(data, columns=["links"])
    return df


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
