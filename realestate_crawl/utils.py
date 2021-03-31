import os
import re
import json
import random
import pathlib
import datetime as dt

import requests

from realestate_crawl.settings import IMAGES_OUT_DIR

username = "c_d0adb603"
password = "lt9ovjp1wo3b"
zone = "shely"


def format_proxy():
    proxy = "http://lum-customer-%s-zone-%s-session-%s:%s@zproxy.luminati.io:22225" \
        %(username, zone, random.randint(0, 1000000), password)
    return proxy


def get_proxy_dict():
    proxy = format_proxy()
    proxy_dict = {
        "http": proxy,
        "https": proxy
    }
    return proxy_dict


def mkdir(name):
    if not os.path.exists(name):
        os.mkdir(name)


def download_image(url: str, image_folder: pathlib.Path, file_name: str, proxy_dict=None, headers=None):
    print('Download :', url)
    try:
        downloaded = requests.get(url, proxies=proxy_dict, headers=headers)
        if downloaded.status_code == 200:
            image_folder.mkdir(exist_ok=True, parents=True)
            with open(image_folder / file_name, 'wb+') as out_file:
                out_file.write(downloaded.content)
    except Exception as e:
        print(f"Error when downloading image {url}:", e)


def get_output_folder_for_location_id(response):
    location_id = response.meta['address']['locationId']
    output_folder_for_location_id = IMAGES_OUT_DIR + '/' + location_id
    return output_folder_for_location_id


def search_with_pattern(pattern, text, group=None):
    result = ''
    if pattern:
        search = re.search(pattern, text)
        if search:
            if group is not None:
                result = search.group(group)
            else:
                result = search.group()
    return result


def get_text_of_selector(texts):
    s = ""
    for text in texts:
        s += " " + text.strip()
    return s.strip()


def get_datetime_now_str():
    now = dt.datetime.utcnow()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def parse_json_string(string: str):
    try:
        return json.loads(string)
    except Exception as e:
        print("Error when parsing json string: ", string)
        return {}
