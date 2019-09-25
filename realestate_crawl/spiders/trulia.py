# -*- coding: utf-8 -*-
import scrapy
from realestate_crawl.settings import OUTPUT_DIR

class TruliaSpider(scrapy.Spider):
    name = 'trulia'
    allowed_domains = ['trulia.com']
    start_urls = ['http://trulia.com/']

    URL_SEARCH_FORMAT = ''

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

    def parse(self, response):
        pass
