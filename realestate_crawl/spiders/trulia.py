# -*- coding: utf-8 -*-
import scrapy
from realestate_crawl.settings import IMAGES_OUT_DIR
from realestate_crawl.utils import mkdir, download_image
from realestate_crawl.spiders import *
import csv
from scrapy import Request
import urllib.request
import json
import urllib.parse
import requests

class TruliaSpider(BaseSpider):
    name = 'trulia'
    URL_SEARCH = 'https://www.trulia.com/graphql'

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'authority': 'www.trulia.com',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0',
            'Host': 'www.trulia.com',
            'Origin': 'https://www.trulia.com',
            'Referer': 'https://www.trulia.com/',
            'DNT': '1',
            'Accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,ru;q=0.8,vi;q=0.7',
            'cache-control': 'no-cache',
            'Content-Type':'application/json'
        },
        'DOWNLOADER_MIDDLEWARES' : {
            'realestate_crawl.middlewares.TruliaDownloaderMiddleWare': 543,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 544,
        }
    }

    def get_request(self, address):
        data = {
            "operationName": "searchBoxAutosuggest",
            "variables": {
            "query": address["address"],
                "searchType": "FOR_SALE",
                "mostRecentSearchLocations": []
            },
            "query": "query searchBoxAutosuggest($query: String!, $searchType: SEARCHAUTOCOMPLETE_SearchType, $mostRecentSearchLocations: [SEARCHDETAILS_LocationInput]) {\n  searchLocationSuggestionByQuery(query: $query, searchType: $searchType, mostRecentSearchLocations: $mostRecentSearchLocations) {\n    places {\n        __typename\n        ...on SEARCHAUTOCOMPLETE_Region{ title details searchEncodedHash }\n        ...on SEARCHAUTOCOMPLETE_Address { title details searchEncodedHash url }\n      }\n    schools { title subtitle details searchEncodedHash }\n    \n  }\n}"
        }
        return Request(
            url=self.URL_SEARCH,
            method='POST',
            body=json.dumps(data),
            callback=self.parse_search_real_url,
            meta={
                'body': json.dumps(data),
                **address
            },
            dont_filter=True,
            errback=self.errback
        )

    def parse_search_real_url(self, response):
        yield self.next_request_from_addresses_poll()

        try:
            j = json.loads(response.text)
            url = None
            try:
                first_result = j['data']['searchLocationSuggestionByQuery']['places'][0] 
                url = first_result['url']
                if response.meta.get('zip_code', "") not in first_result['title']:
                    url = None
            except:
                url = None

            if url:
                yield response.follow(
                    url, 
                    callback=self.parse_real_results, 
                    meta=response.meta,
                    errback=self.errback
                )
            else:
                self.set_no_images(response)
                print('No real url in', response.meta['location_id'])
        except:
            self.set_no_images(response)

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
                for photo in photos:
                    try:
                        url = photo['url']['mediumSrc']
                        photo_urls.append(url)
                    except:
                        pass

                if not photo_urls:
                    self.set_no_images(response)
                for i, photo_url in enumerate(photo_urls):
                    download_image(
                        url=photo_url, 
                        image_folder=self.output_dir + '/' + location_id,
                        file_name='{}_trulia_{}.jpg'.format(location_id, i)
                    )
                self.check_exist_images(self.output_dir + '/' + location_id, response)
            else:
                self.set_no_images(response)
                print('No photos')
                
            try:
                price = j['props']['homeDetails']['price']['formattedPrice']
            except:
                price = None
            
            year = None
            try:
                for attribute in j['props']['homeDetails']['features']['attributes']:
                    if 'built in' in attribute['formattedValue'].lower():
                        year = int(attribute['formattedValue'].split()[-1])
                        break
            except:
                year = None
            self.save_price_year_built(response, location_id, price, year)