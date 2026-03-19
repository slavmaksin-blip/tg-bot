# utils/file_handler.py

"""
Utility functions for uploading product files to an external storage server.
"""

import os
import requests


def upload_file(file_path: str, server_url: str) -> requests.Response:
    """
    Upload a file to the specified server URL.

    Parameters
    ----------
    file_path : str
        Path to the file to be uploaded.
    server_url : str
        URL of the server endpoint that accepts file uploads.

    Returns
    -------
    requests.Response
        The HTTP response returned by the server.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not point to an existing file.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"{file_path} does not exist.")

    with open(file_path, "rb") as f:
        response = requests.post(server_url, files={"file": f}, timeout=30)

    return response
