import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import requests
from realestate_crawl.settings import IMAGES_OUT_DIR

username = 'lum-customer-timothyo-zone-zone2'
password = 'mcavv2l82le0gygh'
port = 22225
zone = "zone2"
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'

def format_proxy():
    proxy = 'http://lum-customer-%s-zone-%s-session-%s:%s@zproxy.luminati.io:%s' \
        %(username, zone, random.randint(0, 5000), password, port)
    return proxy

def get_proxy_dict():
    proxy = format_proxy()
    proxy_dict = {
        "http": proxy,
        "https": proxy,
        "ftp": proxy
    }
    return proxy_dict

def get_driver():
    options = Options()
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(chrome_options=options)
    return driver

def mkdir(name):
    if not os.path.exists(name):
        os.mkdir(name)

def download_image(url, image_folder, file_name, proxy_dict=None, headers=None):
    print('Download :', url)
    downloaded = requests.get(url, proxies=proxy_dict, headers=headers)
    mkdir(image_folder)
    with open(image_folder + "/{}".format(file_name), 'wb+') as out_file:
        out_file.write(downloaded.content)

def get_output_folder_for_location_id(response):
    location_id = response.meta['address']['locationId']
    output_folder_for_location_id = IMAGES_OUT_DIR + '/' + location_id
    return output_folder_for_location_id