import pandas as pd
from argparse import ArgumentParser
import requests
from bs4 import BeautifulSoup
import time
from data_utils import *

def get_uac_data():
    # scrapes UAC website and returns a dataframe
    url = 'https://utahavalanchecenter.org/avalanches'

    # Send a GET request to the webpage
    response = requests.get(url)

    # Parse the HTML content of the webpage
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the link to start the dataset export process
    export_link = soup.find("a", id="/avalanches/details/csv")

    # Click on the link to start the export process
    response = requests.get(export_link["href"])

    # Wait for the export process to finish
    while "export-finished-message" not in response.text:
        time.sleep(1)
        response = requests.get(url)

    # Find the download link for the dataset
    download_link = soup.find("a", id="download-link")

    # Download the dataset
    download_url = download_link["href"]
    dataset_filename = download_url.split("/")[-1]
    download_path = "/path/to/your/directory/" + dataset_filename
    with open(download_path, "wb") as f:
        dataset_response = requests.get(download_url)
        f.write(dataset_response.content)

if __name__=="__main__":
    parser = ArgumentParser()

    parser.add_argument('--get_uac_data', action='store_true')

    args = parser.parse_args()

    if args.get_uac_data:
        #data = get_uac_data()
        #data = clean_uac_avalanche_data(data)
        get_uac_forecast()