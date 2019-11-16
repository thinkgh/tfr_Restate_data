import re
import sys
import csv
import json
import random
import requests

from scrapy import Spider, Request
import urllib.request
import urllib.parse
from realestate_crawl.settings import INPUT_DIR, IMAGES_OUT_DIR
from realestate_crawl.utils import get_proxy_dict, download_image, mkdir, format_proxy


class RealtorSpider(Spider):
    realtor_search_url = "https://www.realtor.com/validate_geo?location={}"

    name = "realtor"

    custom_settings = {
        'HTTPPROXY_ENABLED': True,
        'HTTPERROR_ALLOW_ALL': True,
        "handle_httpstatus_list": [301, 302, 416, 404],
        "RETRY_HTTP_CODES": [403],
        "RETRY_TIMES": 10,
        'USER_AGENT': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1
        }
    }

    def start_requests(self):
        self.output_dir = IMAGES_OUT_DIR + '/' + self.file_name.split('.')[0]
        mkdir(self.output_dir)
        reqs = []

        with open(INPUT_DIR + '/' + self.file_name, 'r') as addr_file:
            addresses = csv.DictReader(addr_file)
            for address in addresses:
                addr = "{}, {}, {} {}".format(
                    address['Address'], address['City'], address['State'], address['Zip'])
                reqs.append(Request(url=self.realtor_search_url.format(urllib.parse.quote(addr)),
                                    callback=self.parse_realtor_search,
                                    meta={
                    "proxy": format_proxy(),
                    "address": dict(address)
                }))
        return reqs

    def parse_realtor_search(self, response):
        resp = json.loads(response.body)
        if 'url' in resp:
            print(resp['url'])
            yield response.follow(
                resp['url'],
                callback=self.parse_realtor_result,
                meta={
                    "proxy": format_proxy(),
                    "address": response.meta['address']
                }
            )

    def parse_realtor_result(self, response):
        status = response.status
        if status > 300 or status < 200:
            print(status, 'Try again', response.url)
            yield Request(
                url=response.url,
                callback = self.parse_realtor_result,
                meta = {
                    "proxy": format_proxy(),
                    "address": response.meta['address']
                }
            )
            return

        location_id = response.meta['address']['locationId']
        for index, img in enumerate(response.css('#ldpHeroCarousel img::attr(data-src)').extract()):
            proxy_dict = get_proxy_dict()
            download_image(
                img,
                image_folder=self.output_dir + '/' + location_id,
                file_name="{}_realtor_{}.jpg".format(location_id, index),
                proxy_dict=proxy_dict
            )