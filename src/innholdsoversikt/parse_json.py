# %%
import logging
from typing import Any

logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# %%
def extract_element_from_json(obj: dict | list[dict], path: list) -> list | list[list]:
    """
    Extracts an element from a nested dictionary or
    a list of nested dictionaries along a specified path.
    If the input is a dictionary, a list is returned.
    If the input is a list of dictionary, a list of lists is returned.

    Parameters:
    -----------
    obj: list or dict
        input dictionary or list of dictionaries
    path: list
        list of strings that form the path to the desired element

    Returns:
    --------
    A list is returned if the input is a dictionary. A list of lists is returned if the input is a list of dictionary.
    """

    def extract(obj: Any, path: list, ind: int, arr: list):
        """
        Extracts an element from a nested dictionary
        along a specified path and returns a list.

        Parameters:
        -----------
        obj: dict or list, required
            input dictionary or list
        path: list, required
            list of strings that form the JSON path
        ind: int, required
            starting index
        arr: list, required
            output list

        Returns:
        --------
        arr, modified list
        """
        key: str = path[ind]
        if ind + 1 < len(path):
            if isinstance(obj, dict):
                if key in obj.keys():
                    extract(obj.get(key), path, ind + 1, arr)
                else:
                    arr.append(None)
            elif isinstance(obj, list):
                if not obj:
                    arr.append(None)
                else:
                    for item in obj:
                        extract(item, path, ind, arr)
            else:
                arr.append(None)
        if ind + 1 == len(path):
            if isinstance(obj, list):
                if not obj:
                    arr.append(None)
                else:
                    for item in obj:
                        arr.append(item.get(key, None))
            elif isinstance(obj, dict):
                arr.append(obj.get(key, None))
            else:
                arr.append(None)
        return arr

    if isinstance(obj, dict):
        return extract(obj, path, 0, [])
    elif isinstance(obj, list):
        outer_arr = []
        for item in obj:
            outer_arr.append(extract(item, path, 0, []))
        return outer_arr
