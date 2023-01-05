#!/usr/bin/python3

import logging
import sys
import yaml
from yaml.loader import SafeLoader
from pytimeparse2 import parse
import datetime as dt
import requests

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(message)s')


# Global Variables
# Will be updated in the first phase of this script

# config stuff
conf_file_name = "config.yml"
config = dict()     # The config read from config file

# HTTP request stuff
base_url = ""
headers = dict()
base_params = {'direction':'asc', 'order':'published_at', 'status':'unread'}
timeout = 30.0


class RequestError(Exception):
    def __init__(self, response):
        self.status_code = response.status_code
        self._response = response

    def get_error_reason(self):
        result = self._response.json()
        default_reason = f"status_code={self.status_code}"
        if isinstance(result, dict):
            return result.get("error_message", default_reason)
        return default_reason


def read_config():

    global config
    global base_url
    global headers

    try:
        with open(conf_file_name) as file:
            # config = json.load(file)
            config = yaml.load(file, Loader=SafeLoader)

    except IOError:
        logging.error(f"Could not read config file {conf_file_name}. Are you sure it's there?")
        sys.exit(1)
    except yaml.scanner.ScannerError:
        logging.error(f"Invalid YAML in {conf_file_name}")
        sys.exit(1)

    validate_config()

    # update global variables
    base_url = config['url']
    headers = {"X-Auth-Token": config['api_token']}


def validate_config():

    # TODO: Config file validation could be improved, e.g. by using a schema
    # and/or a suitable library like https://github.com/edaniszewski/bison

    logging.debug(f"Parsed config file: {config}")

    if ("api_token" not in config) or (config['api_token'] == None) or (config['api_token'] == ""):
        logging.error(f"Miniflux API token not set in config")
        sys.exit(1)
    
    if ("url" not in config) or (config['url'] == None) or (config['url'] == ""):
        logging.error(f"Miniflux URL not set in config")
        sys.exit(1)


def find_and_mark_expired_entries():

    if ("categories" not in config and "feeds" not in config):
        logging.error(f"config does not include either 'categories' or 'feeds' entry. Nothing to do here.")
        sys.exit(1)

    logging.debug("Starting to find and mark expired entries")

    # category entries
    for cat in config['categories']:
        entries = get_expired_category_entries(str(cat['category']), cat['expiry'])

    # TODO: repeat for feeds


def get_expired_category_entries(category, expiry):

    logging.debug(f"Get category entries: {category}, {expiry}")

    
    params = base_params | {'before': calculate_expiry_timestamp(expiry)}        # extend params with expiry timestamp for this request
    endpoint = f"{base_url}/v1/categories/{category}/entries"

    logging.debug(f"Calling {endpoint} with {params}")
    """
    response = requests.get(
        endpoint,
        headers,
        params,
        timeout
    )
    """


def calculate_expiry_timestamp(expiry):
    # parse expiry term and calculate unix timestamp in the past
    delta = int(parse(expiry))
    now = dt.datetime.now()
    now_posix = int(now.timestamp())
    expiry_ts = now - dt.timedelta(seconds=delta)
    expiry_ts_posix = int(expiry_ts.timestamp())
    logging.debug(f"{expiry} = {delta} seconds, now = {now_posix} ({now.isoformat(timespec='seconds')}), expiry_ts = {expiry_ts_posix} ({expiry_ts.isoformat(timespec='seconds')})")
    return str(expiry_ts_posix)
    


if __name__ == "__main__":
    read_config()
    find_and_mark_expired_entries()
