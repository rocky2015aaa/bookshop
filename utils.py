import logging
import pandas as pd
from constants import BARCODE_PREFIX, QUANTITY_PREFIX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bookshop")


def get_barcode_quantity_datagram_from_bytes(data):
    """
    Extracts barcode-quantity pairs from the provided byte data.

    Args:
        data (bytes): The byte data containing barcode and quantity information.

    Returns:
        List[Dict[str, int]]: A list of dictionaries containing barcode-quantity pairs.
    """
    inventory_pairs = []
    lines = data.decode().split("\n")
    brc_line = None
    for line in lines:
        line = line.strip()
        if line.startswith(BARCODE_PREFIX):
            brc_line = line
        elif line.startswith(QUANTITY_PREFIX) and brc_line:
            inventory_pairs.append({
                BARCODE_PREFIX: int(brc_line.replace(BARCODE_PREFIX, "")),
                QUANTITY_PREFIX: int(line.replace(QUANTITY_PREFIX, ""))
            })
            brc_line = None
    return pd.DataFrame(inventory_pairs)


def model_to_dict(model_instance):
    """
    Convert a SQLAlchemy model instance to a dictionary.
    """
    result = {}
    for column in model_instance.__table__.columns:
        result[column.name] = getattr(model_instance, column.name)
    return result


def model_list_to_dict_list(model_list):
    """
    Convert a list of SQLAlchemy model instances to a list of dictionaries.
    """
    dict_list = []
    for model_instance in model_list:
        dict_list.append(model_to_dict(model_instance))
    return dict_list
