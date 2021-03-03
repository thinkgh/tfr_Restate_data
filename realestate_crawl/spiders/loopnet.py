import re
import sys
import csv
import json
import random
import requests

from scrapy import Spider, Request, Item, Field, FormRequest
import urllib.request
import urllib.parse
from realestate_crawl.settings import IMAGES_OUT_DIR
from realestate_crawl.utils import download_image, get_proxy_dict, mkdir
from realestate_crawl.spiders import *

class LoopnetSpider(BaseSpider):
    name = "loopnet"

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES' : {
            'realestate_crawl.middlewares.LoopnetDownloaderMiddleWare': 543,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 544,
        }
    }

    def get_request(self, address):
        data = {
            "geography": address["address"].replace(" ", "+"),
            "listingtypes": "1",
            "categories": "",
            "advancedSearch": "",
            "fullAddress": ""
        }
        return FormRequest(
            "https://www.loopnet.com/search",
            formdata=data,
            meta={
                'location_id': address["location_id"],
                'address_obj': address['address_obj'],
                'body': json.dumps(data),
            }, 
            callback=self.parse_loopnet,
            errback=self.errback,
        )

    def get_price_and_built_year(self, response):
        price = built_year = None
        try:
            context = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').get().strip())
            try:
                price = context['about']['price']
            except:
                pass
            try:
                text = ' '.join(response.css('.property-facts__data-item-text::text').getall())
                built_year_search = re.search('\s(\d{4})/?\d*\s', text)
                if built_year_search:
                    built_year = int(built_year_search.group(1))
            except:
                pass
        except:
            pass
        self.save_price_year_built(response.meta['location_id'], price, built_year)
        
    def parse_loopnet(self, response):
        yield self.next_request_from_addresses_poll()
        images = response.css(
            '.mosaic-carousel-container ::attr(data-src)').extract()
        if images:
            self.get_price_and_built_year(response)
            headers = { 
                'Referer': response.url,
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
            }
            location_id = response.meta['location_id']
            for index, image in enumerate(images):
                download_image(
                    url=image,
                    image_folder=self.output_dir + '/' + location_id,
                    file_name="{}_loopnet_{}.jpg".format(location_id, index),
                    headers=headers
                )
            self.check_exist_images(self.output_dir + '/' + location_id, response)
        else:
            self.set_no_images(response)