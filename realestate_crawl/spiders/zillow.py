import re
import sys
import csv
import json
import random
import requests

from scrapy import Spider, Request, Item, Field, FormRequest
import urllib.request
import urllib.parse
from realestate_crawl.settings import OUTPUT_DIR, IMAGES_OUT_DIR
from realestate_crawl.utils import format_proxy, download_image, mkdir
from realestate_crawl.spiders import *

class ZillowSpider(BaseSpider):
    zillow_url = "https://www.zillow.com/homes/{}_rb/"

    name = "zillow"

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'authority': 'www.zillow.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,ru;q=0.8,vi;q=0.7',
            'cache-control': 'no-cache',
        },
        # 'FEED_FORMAT': 'csv',
        # 'FEED_URI': OUTPUT_DIR + '/zillow.csv',
    }

    def get_request(self, address):
        url = self.zillow_url.format(address["address"].replace(' ', '-'))
        return Request(
            url=url, 
            callback=self.parse_zillow, 
            meta={
                'real_url': url,
                **address
            },
            errback=self.errback
        )

    def parse_zillow(self, response):
        yield self.next_request_from_addresses_poll()
        raw_urls = re.findall(r"mediumImageLink.*?(\[.*?\])", response.text)
        has_image = False
        location_id = response.meta['location_id']
        if raw_urls:
            try:
                zillow_img_urls = json.loads(raw_urls[1].replace('\\', ''))
                for index, img in enumerate(zillow_img_urls):
                    if 'url' in img:
                        has_image = True
                        download_image(
                            url=img['url'],
                            image_folder=self.output_dir + '/' + location_id,
                            file_name='{}_zillow_{}.jpg'.format(location_id, index)
                        )
                self.check_exist_images(self.output_dir + '/' + location_id, response)
            except:
                pass
        if not has_image:
            self.set_no_images(response)

        raw_text = response.css("#hdpApolloPreloadedData ::text").re('.*')
        if raw_text:
            zillow_raw_text = raw_text[0].replace("\\", "")
            # sq_ft = re.findall('livingArea\":(.*?),', zillow_raw_text)[0]
            year_built = re.findall('yearBuilt\":(.*?),', zillow_raw_text)[0]
            # home_type = re.findall('homeType\":(.*?),', zillow_raw_text)[0]
            # bed_room = re.findall('bedrooms\":(.*?),', zillow_raw_text)[0]
            # bathroom = re.findall('bathrooms\":(.*?),', zillow_raw_text)[0]
            price = re.findall('price\":(.*?),', zillow_raw_text)[0]
            # lot_size = re.findall('lotSize\":(.*?),', zillow_raw_text)[0]
            # item = {
            #     "locationId": response.meta['location_id'],
            #     "sq_ft": sq_ft,
            #     "year_built": year_built,
            #     "home_type": home_type,
            #     "bed_room": bed_room,
            #     "bathroom": bathroom,
            #     "price": price,
            #     "lot_size": lot_size,
            # }
            # item = self.extract_facts(response.css('.fact-group'), item)
            # item = self.extract_cat(response.css('.category-container'), item)
            # yield item
            if price:
                price_search = re.search('\d+', price)
                if price_search:
                    price = int(price_search.group())
                else:
                    price = None
            else:
                price = None
            self.save_price_year_built(response.meta['location_id'], price, year_built)

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