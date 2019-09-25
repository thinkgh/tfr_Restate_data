# -*- coding: utf-8 -*-
import scrapy
from realestate_crawl.settings import OUTPUT_DIR, INPUT_DIR
import csv
from realestate_crawl.utils import format_proxy

class HarSpider(scrapy.Spider):
    name = 'har'

    SEARCH_URL = 'https://www.har.com/search/dosearch?for_sale=1&quicksearch={}'

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': OUTPUT_DIR + '/output_{}.csv'.format(name),
        'HTTPPROXY_ENABLED': True,
        "handle_httpstatus_list": [301, 302],
        "RETRY_HTTP_CODES": [403],
        "DOWNLOAD_DELAY": 2,
        "RETRY_TIMES": 10,
        "IMAGES_STORE": 'images',
        'USER_AGENT': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        'DOWNLOADER_MIDDLEWARES': {
           'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,

        }
    }

    def start_requests(self):
        requests = []
        with open(INPUT_DIR + '/pilot_tm_addresses_round_2.csv', 'r') as f:
            addresses = csv.DictReader(f)
            for address in addresses:
                addr = "{}, {}, {} {}".format(address['Address'], address['City'], address['State'], address['Zip'])
                url_search = self.SEARCH_URL.format(addr.replace(' ', '+')) 
                request = scrapy.Request(
                    url_search,
                    meta={
                        'location_id': address['locationId']
                    },
                    callback=self.parse
                )
                requests.append(request)
        return requests

    def parse(self, response):
        pass