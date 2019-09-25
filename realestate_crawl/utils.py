import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

username = 'lum-customer-timothyo-zone-zone2'
password = 'mcavv2l82le0gygh'
port = 22225
zone = "zone2"
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'

def format_proxy():
    proxy = 'http://lum-customer-%s-zone-%s-session-%s:%s@zproxy.luminati.io:%s' \
        %(username, zone, random.randint(0, 500), password, port)
    print(proxy)
    return proxy


def get_driver():
    options = Options()
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(chrome_options=options)
    return driver

def mkdir(name):
    if not os.path.exists(name):
        os.mkdir(name)