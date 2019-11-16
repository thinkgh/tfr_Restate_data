# -*- coding: utf-8 -*-
import scrapy
from realestate_crawl.settings import OUTPUT_DIR, INPUT_DIR, IMAGES_OUT_DIR
from realestate_crawl.utils import format_proxy, mkdir
import csv
from scrapy import Request
import urllib.request
import json
import urllib.parse
import requests

class RedfinSpider(scrapy.Spider):
    redfin_search_url = "https://www.redfin.com/stingray/do/location-autocomplete?location={}&start=0&count=10&v=2&market=philadelphia&al=1&iss=false&ooa=true&mrs=false"
    name = 'redfin'
    allowed_domains = ['redfin.com']
    start_urls = ['http://redfin.com/']

    custom_settings = {
        'HTTPPROXY_ENABLED': True,
        "handle_httpstatus_list": [301, 302],
        "RETRY_HTTP_CODES": [403],
        "RETRY_TIMES": 10,
        'USER_AGENT': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        'DOWNLOADER_MIDDLEWARES': {
           'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,

        }
    }

    def start_requests(self):
        self.output_dir = IMAGES_OUT_DIR + '/' + self.file_name.split('.')[0]
        mkdir(self.output_dir)
        reqs = []
        with open(INPUT_DIR + '/' + self.file_name, 'r') as addr_file:
            addresses = csv.DictReader(addr_file)
            for address in addresses:
                addr = "{},{},{},{}".format(address['Address'], address['City'], address['State'], address['Zip'])
                url_search = self.redfin_search_url.format(urllib.parse.quote(addr))
                reqs.append(
                    Request(
                        url=url_search, 
                        callback=self.parse,
                        headers={'accept': 'application/json', 'cookie':'RF_BROWSER_ID=_-ZqlIfiRliiTvv4r_kIOg; RF_CORVAIR_LAST_VERSION=281.1.0; RF_BID_UPDATED=1; _gcl_au=1.1.1420189527.1568722855; RF_BROWSER_CAPABILITIES=%7B%22css-transitions%22%3Atrue%2C%22css-columns%22%3Atrue%2C%22css-generated-content%22%3Atrue%2C%22css-opacity%22%3Atrue%2C%22events-touch%22%3Afalse%2C%22geolocation%22%3Atrue%2C%22screen-size%22%3A4%2C%22screen-size-tiny%22%3Afalse%2C%22screen-size-small%22%3Afalse%2C%22screen-size-medium%22%3Afalse%2C%22screen-size-large%22%3Afalse%2C%22screen-size-huge%22%3Atrue%2C%22html-prefetch%22%3Atrue%2C%22html-range%22%3Atrue%2C%22html-form-validation%22%3Atrue%2C%22html-form-validation-with-required-notice%22%3Atrue%2C%22html-input-placeholder%22%3Atrue%2C%22html-input-placeholder-on-focus%22%3Atrue%2C%22ios-app-store%22%3Afalse%2C%22google-play-store%22%3Afalse%2C%22ios-web-view%22%3Afalse%2C%22android-web-view%22%3Afalse%2C%22activex-object%22%3Atrue%2C%22webgl%22%3Atrue%2C%22history%22%3Atrue%2C%22localstorage%22%3Atrue%2C%22sessionstorage%22%3Atrue%2C%22position-fixed-workaround%22%3Afalse%2C%22passive-event-listener%22%3Atrue%7D; G_ENABLED_IDPS=google; RF_GOOGLE_ONE_TAP_DISMISSED=lastDismissalDate%3D1568722860411; RF_VISITED=null; AKA_A2=A; unifiedLastSearch=name%3D130%252087th%2520St%26subName%3DStone%2520Harbor%252C%2520NJ%252C%2520USA%26url%3D%252FNJ%252FStone-Harbor%252F130-87th-St-08247%252Fhome%252F62511943%26id%3D9_62511943%26type%3D1%26isSavedSearch%3D%26countryCode%3DUS; RF_MARKET=philadelphia; RF_BUSINESS_MARKET=42; RF_LAST_SEARCHED_CITY=Stone%20Harbor; RF_LISTING_VIEWS=35317501'}, 
                        meta={
                            "address": dict(address)}
                    )
                )
        return reqs

    def parse(self, response):
        location_id = response.meta['address']['locationId']
        address = response.meta['address']['Address']
        print('location id:' ,location_id)
        resp = json.loads(response.body[4:])
        if 'sections' in resp['payload']:
            sections = resp['payload']['sections']
            if sections:
                url = sections[0]['rows'][0]['url']
                print(address, ':', url)
                yield response.follow(url, callback=self.parse_redfin_results, meta=response.meta)

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
            location_id = response.meta['address']['locationId']
            photos = resp['payload']['mediaBrowserInfo']['photos']
            if len(photos) > 0:
                for index, photo in enumerate(resp['payload']['mediaBrowserInfo']['photos']):
                    url = photo['photoUrls']['fullScreenPhotoUrl']
                    filename = "{}_redfin_{}.jpg".format(location_id, index)
                    self.download_image(url, filename, location_id, proxy_dict)
            else:
                img_src = response.css('.img-card.streetViewImage::attr(src)').get()
                if img_src:
                    self.download_image(img_src, '{}_redfin_0.jpg'.format(location_id), location_id, proxy_dict)

    def download_image(self, url, file_name, location_id, proxy_dict):
        print('Download :', url)
        downloaded = requests.get(url, proxies=proxy_dict)
        image_folder = self.output_dir + '/' + location_id
        mkdir(image_folder)
        with open(image_folder + "/{}".format(file_name), 'wb+') as out_file:
            out_file.write(downloaded.content)
