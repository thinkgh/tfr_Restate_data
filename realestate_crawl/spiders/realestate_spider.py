import re
import sys
import csv
import json
import random
import requests

from scrapy import Spider, Request, Item, Field, FormRequest
import urllib.request
import urllib.parse
from realestate_crawl.settings import IMAGES_OUT_DIR, INPUT_DIR, OUTPUT_DIR
from realestate_crawl.utils import format_proxy

class WilliamSpider(Spider):
    redfin_search_url = "https://www.redfin.com/stingray/do/location-autocomplete?location={}&start=0&count=10&v=2&market=knoxville&al=1&iss=false&ooa=true&mrs=false"
    realtor_search_url = "https://www.realtor.com/validate_geo?location={}"
    loopnet_search_url = "https://www.loopnet.com/search"
    zillow_url = "https://www.zillow.com/homes/{}_rb"
    
    name = "william_demo_spider"

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': OUTPUT_DIR + '/output.csv',
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
        reqs = []
        with open(INPUT_DIR + '/pilot_tm_addresses_round_2.csv', 'r') as addr_file:
            addresses = csv.DictReader(addr_file)
            for address in addresses:
                addr = "{}, {}, {} {}".format(address['Address'], address['City'], address['State'], address['Zip'])
                reqs.append(FormRequest(url="https://www.loopnet.com/search", formdata={
                    "geography": addr.replace(" ", "+"),
                    "listingtypes": "2",
                    "categories": "",
                    "advancedSearch": "",
                    "fullAddress": ""
                }, meta={"proxy": format_proxy(),
                    "address": dict(address)
                }, callback=self.parse_loopnet))

                reqs.append(Request(url=self.redfin_search_url.format(urllib.parse.quote(addr)), callback=self.parse_redfin_search,
                            headers={'accept': 'application/json'}, meta={
                                # "proxy": format_proxy(),
                                 "address": dict(address)}))

                reqs.append(Request(url=self.realtor_search_url.format(urllib.parse.quote(addr)), callback=self.parse_realtor_search, meta={
                    # "proxy": format_proxy(),
                    "address": dict(address)
                }))

                reqs.append(Request(url=self.zillow_url.format(addr.replace(' ', '-')), callback=self.parse_zillow, meta={
                    "proxy": format_proxy(),
                    "address": dict(address)
                }))
        return reqs

    def parse_loopnet(self, response):
        proxy = format_proxy()
        proxy_dict = {
            "http": proxy,
            "https": proxy,
            "ftp": proxy
        }
        images = response.css('.mosaic-carousel-container ::attr(data-src)').extract()
        for index, image in enumerate(images):
            filename = "{}_{}_loopnet.jpg".format(response.meta['address']['locationId'], index)
            downloaded = requests.get(image, proxies=proxy_dict)
            with open(IMAGES_OUT_DIR +"/{}".format(filename), 'wb+') as out_file:
                out_file.write(downloaded.content)

    def parse_zillow(self, response):
        proxy = format_proxy()
        proxy_dict = {
            "http": proxy,
            "https": proxy,
            "ftp": proxy
        }
        raw_urls = re.findall(r"mediumImageLink.*?(\[.*?\])", response.text)
        if raw_urls:
            zillow_img_urls = json.loads(raw_urls[1].replace('\\', ''))
            for index, img in enumerate(zillow_img_urls):
                filename = "{}_{}_zillow.jpg".format(response.meta['address']['locationId'], index)
                downloaded = requests.get(img["url"], proxies=proxy_dict)
                with open(IMAGES_OUT_DIR + "/{}".format(filename), 'wb+') as out_file:
                    out_file.write(downloaded.content)

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
            item[sel.css('.fact-label ::text').extract_first()] = sel.css(".fact-value ::text").extract_first()
        return item

    def extract_cat(self, sels, item):
        for sel in sels:
            item[sel.css('.category-name ::text').extract_first()] = " ".join(sel.css('.category-facts ::text').extract())
        return item

    def parse_realtor_search(self, response):
        resp = json.loads(response.body)
        if 'url' in resp:
            yield response.follow(resp['url'], callback=self.parse_realtor_result, meta=response.meta)
    
    def parse_realtor_result(self, response):
        proxy = format_proxy()
        proxy_dict = {
            "http": proxy,
            "https": proxy,
            "ftp": proxy
        }
        for index, img in enumerate(response.css('#ldpHeroCarousel img::attr(data-src)').extract()):
            filename = "{}_{}_realtor.jpg".format(response.meta['address']['locationId'], index)
            downloaded = requests.get(img, proxies=proxy_dict)
            with open(IMAGES_OUT_DIR + "/{}".format(filename), 'wb+') as out_file:
                out_file.write(downloaded.content)

    def parse_redfin_search(self, response):
        resp = json.loads(response.body[4:])
        if 'exactMatch' in resp['payload']:
            yield response.follow(resp['payload']['exactMatch']['url'], callback=self.parse_redfin_results, meta=response.meta)

    def parse_redfin_results(self, response):
        proxy = format_proxy()
        proxy_dict = {
            "http": proxy,
            "https": proxy,
            "ftp": proxy
        }
        body = response.xpath('string(//body)').re_first(r"root\.__reactServerState\.InitialContext = (.+);")
        if body:
            resp = json.loads(body)
            resp = json.loads(resp['ReactServerAgent.cache']['dataCache']['/stingray/api/home/details/aboveTheFold']['res']['text'][4:])
            for index, photo in enumerate(resp['payload']['mediaBrowserInfo']['photos']):
                url = photo['photoUrls']['fullScreenPhotoUrl']
                filename = "{}_{}_redfin.jpg".format(response.meta['address']['locationId'], index)
                downloaded = requests.get(url, proxies=proxy_dict)
                with open(IMAGES_OUT_DIR + "/{}".format(filename), 'wb+') as out_file:
                    out_file.write(downloaded.content)
