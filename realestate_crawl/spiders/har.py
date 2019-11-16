# -*- coding: utf-8 -*-
import scrapy
from realestate_crawl.settings import INPUT_DIR, IMAGES_OUT_DIR
import csv
from realestate_crawl.utils import format_proxy, mkdir, download_image


class HarSpider(scrapy.Spider):
    name = 'har'

    SEARCH_URL = 'https://www.har.com/search/dosearch?for_sale=1&quicksearch={}'

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

    count = 0

    def start_requests(self):
        requests = []
        with open(INPUT_DIR + '/' + self.file_name, 'r') as f:
            addresses = csv.DictReader(f)
            for address in addresses:
                addr = "{},{},{},{}".format(
                    address['Address'], address['City'], address['State'], address['Zip'])
                url_search = self.SEARCH_URL.format(addr.replace(' ', '+'))
                request = scrapy.Request(
                    url_search,
                    meta={
                        'location_id': address['locationId']
                    },
                    callback=self.parse_search
                )
                requests.append(request)
        return requests

    def parse_search(self, response):
        self.count += 1
        print('Parsing search page for {}-th addresses'.format(self.count))
        divs = response.css('.prop_item')
        if divs:
            detail_page_url = divs[0].css('.mpi_img_link::attr(href)').get()
            if detail_page_url:
                yield response.follow(
                    detail_page_url,
                    callback=self.parse_detail_page,
                    meta=response.meta
                )

    def parse_detail_page(self, response):
        slides = response.css('ul.slides')
        if slides:
            location_id = response.meta['location_id']
            image_urls = slides[0].css('li a::attr(href)').getall()
            for i, image_url in enumerate(image_urls):
                download_image(
                    url=image_url,
                    image_folder=IMAGES_OUT_DIR + '/' + location_id,
                    file_name='{}_har_{}.jpg'.format(location_id, i)
                )
        else:
            print('No images')
