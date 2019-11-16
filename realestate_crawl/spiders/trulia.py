# -*- coding: utf-8 -*-
import scrapy
from realestate_crawl.settings import INPUT_DIR, IMAGES_OUT_DIR
from realestate_crawl.utils import format_proxy, mkdir, download_image, get_proxy_dict
import csv
from scrapy import Request
import urllib.request
import json
import urllib.parse
import requests

class TruliaSpider(scrapy.Spider):
    name = 'trulia'
    URL_SEARCH = 'https://www.trulia.com/graphql'

    custom_settings = {
        'HTTPPROXY_ENABLED': True,
        'HTTPERROR_ALLOW_ALL': True,
        "handle_httpstatus_list": [301, 302, 403],
        "RETRY_TIMES": 10,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0',
            'Host': 'www.trulia.com',
            'Origin': 'https://www.trulia.com',
            'Referer': 'https://www.trulia.com/',
            'DNT': '1',
            'TE': 'Trailers',
            'Accept': '*/*',
            'Content-Type':'application/json'
        },
        'DOWNLOADER_MIDDLEWARES': {
           'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,

        }
    }

    data = {
        'operationName': 'searchHomesByFreeText',
        'variables': {'query': '103 STILL WATER DRIVE,PORT ARANSAS,TX,78373',
        'searchType': 'FOR_SALE',
        'searchDetails': {'searchType': 'FOR_SALE', 'location': {}}},
        'query': 'query searchHomesByFreeText($query: String!, $searchDetails: SEARCHDETAILS_Input) {\n  searchHomesByFreeText(query: $query, searchDetails: $searchDetails) {\n    currentUrl\n    exactAddressDetails {\n      url\n    }\n  }\n}'
    }

    def start_requests(self):
        self.output_dir = IMAGES_OUT_DIR + '/' + self.file_name.split('.')[0]
        mkdir(self.output_dir)
        reqs = []
        with open(INPUT_DIR + '/' + self.file_name, 'r') as addr_file:
            addresses = csv.DictReader(addr_file)
            for address in addresses:
                addr = "{},{},{},{}".format(address['Address'], address['City'], address['State'], address['Zip'])
                self.data['variables']['query'] = addr
                reqs.append(
                    Request(
                        url=self.URL_SEARCH,
                        method='POST',
                        body=json.dumps(self.data),
                        callback=self.parse_search_real_url,
                        meta={
                            'proxy': format_proxy(),
                            'location_id': address['locationId'],
                            'body': json.dumps(self.data)
                        },
                        dont_filter=True
                    )
                )
        return reqs

    def parse_search_real_url(self, response):
        status = response.status
        if status > 300 or status < 200:
            print(status, 'Try again', response.url)
            print(response.text)
            yield Request(
                url=response.url,
                method='POST',
                callback = self.parse_search_real_url,
                body=response.meta['body'],
                meta = {
                    "proxy": format_proxy(),
                    "location_id": response.meta['location_id'],
                    'body': response.meta['body']
                },
                dont_filter=True
            )
            return
        
        j = json.loads(response.text)
        url = None
        try:
            url = j['data']['searchHomesByFreeText']['exactAddressDetails']['url']
        except:
            pass
        if url:
            response.meta['proxy'] = format_proxy()
            yield response.follow(
                url, 
                callback=self.parse_real_results, 
                meta=response.meta
            )
        else:
            print('No real url in', response.meta['location_id'])

    def parse_real_results(self, response):
        location_id = response.meta['location_id']
        print('Parsing result for {}'.format(location_id))
        script_tag = response.css('#__NEXT_DATA__::text').get()
        if script_tag:
            j = json.loads(script_tag)
            photos = []
            try:
                photos = j['props']['homeDetails']['media']['photos']
            except:
                pass
            if photos:
                location_id = response.meta['location_id']
                photo_urls = []
                proxy_dict = get_proxy_dict()
                for photo in photos:
                    try:
                        url = photo['url']['mediumSrc']
                        photo_urls.append(url)
                    except:
                        pass
                for i, photo_url in enumerate(photo_urls):
                    download_image(
                        url=photo_url, 
                        image_folder=self.output_dir + '/' + location_id,
                        file_name='{}_trulia_{}.jpg'.format(location_id, i),
                        proxy_dict=proxy_dict
                    )
            else:
                print('No photos')
