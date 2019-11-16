import re
import sys
import csv
import json
import random
import requests

from scrapy import Spider, Request, Item, Field, FormRequest
import urllib.request
import urllib.parse
from realestate_crawl.settings import INPUT_DIR, OUTPUT_DIR, IMAGES_OUT_DIR
from realestate_crawl.utils import format_proxy, download_image, mkdir


class ZillowSpider(Spider):
    zillow_url = "https://www.zillow.com/homes/{}_rb"

    name = "zillow"

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': OUTPUT_DIR + '/zillow.csv',
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
                    Request(
                        url=self.zillow_url.format(addr.replace(' ', '-')), 
                        callback=self.parse_zillow, 
                        meta={
                            "proxy": format_proxy(),
                            "address": dict(address)
                        }
                    )
                )
        return reqs

    def parse_zillow(self, response):
        if 'www.zillowstatic.com/vstatic/80d5e73/static/css/z-pages/captcha.css' in response.text:
            print(response.url)
            yield Request(
                        url=response.url, 
                        callback=self.parse_zillow, 
                        meta={
                            "proxy": format_proxy(),
                            "address": response.meta['address']
                        }
                    )
            return
        raw_urls = re.findall(r"mediumImageLink.*?(\[.*?\])", response.text)

        location_id = response.meta['address']['locationId']
        if raw_urls:
            print(raw_urls)
            zillow_img_urls = json.loads(raw_urls[1].replace('\\', ''))
            for index, img in enumerate(zillow_img_urls):
                if 'url' in img:
                    proxy = format_proxy()
                    proxy_dict = {
                        "http": proxy,
                        "https": proxy,
                        "ftp": proxy
                    }
                    download_image(
                        url=img['url'],
                        image_folder=self.output_dir + '/' + location_id,
                        file_name='{}_zillow_{}.jpg'.format(location_id, index),
                        proxy_dict=proxy_dict
                    )

        raw_text = response.css("#hdpApolloPreloadedData ::text").re('.*')
        if raw_text:
            zillow_raw_text = raw_text[0].replace("\\", "")
            sq_ft = re.findall('livingArea\":(.*?),', zillow_raw_text)[0]
            year_built = re.findall('yearBuilt\":(.*?),', zillow_raw_text)[0]
            home_type = re.findall('homeType\":(.*?),', zillow_raw_text)[0]
            bed_room = re.findall('bedrooms\":(.*?),', zillow_raw_text)[0]
            bathroom = re.findall('bathrooms\":(.*?),', zillow_raw_text)[0]
            price = re.findall('price\":(.*?),', zillow_raw_text)[0]
            lot_size = re.findall('lotSize\":(.*?),', zillow_raw_text)[0]
            item = {
                "locationId": response.meta['address']['locationId'],
                "sq_ft": sq_ft,
                "year_built": year_built,
                "home_type": home_type,
                "bed_room": bed_room,
                "bathroom": bathroom,
                "price": price,
                "lot_size": lot_size,
            }
            item = self.extract_facts(response.css('.fact-group'), item)
            item = self.extract_cat(response.css('.category-container'), item)
            yield item

    def extract_facts(self, sels, item):
        for sel in sels:
            item[sel.css('.fact-label ::text').extract_first()
                 ] = sel.css(".fact-value ::text").extract_first()
        return item

    def extract_cat(self, sels, item):
        for sel in sels:
            item[sel.css('.category-name ::text').extract_first()
                 ] = " ".join(sel.css('.category-facts ::text').extract())
        return item