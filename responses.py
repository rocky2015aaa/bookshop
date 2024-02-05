from constants import RESP_DATA, RESP_STATUS, RESP_MESSAGE


def Response(data: object, message: str) -> object:
    return {
        RESP_DATA: data,
        RESP_STATUS: True,
        RESP_MESSAGE: message,
    }
