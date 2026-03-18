# file_handler.py

"""
This module provides utility functions for uploading product files to server storage.
"""

import os
import requests


def upload_file(file_path, server_url):
    """
    Uploads a file to the specified server URL.

    Parameters:
    - file_path: str, path to the file to be uploaded
    - server_url: str, the URL of the server endpoint to upload the file

    Returns:
    - response: Response object from requests library
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"{file_path} does not exist.")

    with open(file_path, 'rb') as f:
        response = requests.post(server_url, files={'file': f})

    return response
