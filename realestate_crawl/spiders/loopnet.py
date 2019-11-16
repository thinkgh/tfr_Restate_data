import re
import sys
import csv
import json
import random
import requests

from scrapy import Spider, Request, Item, Field, FormRequest
import urllib.request
import urllib.parse
from realestate_crawl.settings import INPUT_DIR, IMAGES_OUT_DIR
from realestate_crawl.utils import format_proxy, download_image, get_proxy_dict, mkdir


class LoopnetSpider(Spider):
    name = "loopnet"

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
                reqs.append(
                    FormRequest(
                        url="https://www.loopnet.com/search", 
                        formdata={
                            "geography": addr.replace(" ", "+"),
                            "listingtypes": "1",
                            "categories": "",
                            "advancedSearch": "",
                            "fullAddress": ""
                        }, 
                        meta={
                            "address": dict(address),
                            'proxy': format_proxy()
                        }, 
                        callback=self.parse_loopnet
                    )
                )
        return reqs

    def parse_loopnet(self, response):
        images = response.css(
            '.mosaic-carousel-container ::attr(data-src)').extract()
        if images:
            print(response.url, images)
        headers = { 
            'Referer': response.url,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
        }

        location_id = response.meta['address']['locationId']
        for index, image in enumerate(images):
            proxy_dict = get_proxy_dict()
            download_image(
                url=image,
                image_folder=self.output_dir + '/' + location_id,
                file_name="{}_loopnet_{}.jpg".format(location_id, index),
                proxy_dict=proxy_dict,
                headers=headers
            )