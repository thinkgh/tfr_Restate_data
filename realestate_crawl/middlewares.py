# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import random
import scrapy
from realestate_crawl.utils import format_proxy
import requests
from scrapy.http import HtmlResponse

class RealestateCrawlSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        spider.set_no_images(response)
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RealestateCrawlDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    count_error_dict = {}
    MAX_TRY_ALLOW_FOR_PROXY = 8

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        if 'need_proxy' in request.meta:
            request.meta['proxy'] = format_proxy()
        return None

    def get_key_for_count_error_dict(self, request):
        if 'real_url' in request.meta:
            return request.meta['real_url']
        return request.url

    def get_request_for_block(self, url, request):
        return scrapy.Request(url=url, method=request.method, body=request.body, dont_filter=True, meta=request.meta, callback=request.callback, errback=request.errback)

    def process_response(self, request, response, spider):
        key = self.get_key_for_count_error_dict(request)
        if response.status < 200 or response.status > 300:
            if key in self.count_error_dict:
                self.count_error_dict[key] += 1
            else:
                self.count_error_dict[key] = 0
            
            if self.count_error_dict[key] < self.MAX_TRY_ALLOW_FOR_PROXY:
                self._add_need_proxy_to_meta_request(request)

                if spider.name == 'zillow' and 'www.zillowstatic.com/vstatic/80d5e73/static/css/z-pages/captcha.css' in response.text:
                    url = request.meta['real_url']
                else:
                    url = request.url
                print('Send request again because of blocking IP:', url)
                return self.get_request_for_block(url, request)
            else:
                print('Reach max allow via proxy')
                spider.set_no_images(request)
                del self.count_error_dict[key]
                return spider.next_request_from_addresses_poll() 
        else:
            if key in self.count_error_dict:
                del self.count_error_dict[key]
        return response
        
    def _add_need_proxy_to_meta_request(self, request):
        request.meta['need_proxy'] = True

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        spider.set_no_images(request)
        return spider.next_request_from_addresses_poll()

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class TruliaDownloaderMiddleWare(RealestateCrawlDownloaderMiddleware):
    def get_key_for_count_error_dict(self, request):
        return request.meta['body']

class LoopnetDownloaderMiddleWare(RealestateCrawlDownloaderMiddleware):
    def get_key_for_count_error_dict(self, request):
        return request.meta['body']

    def get_request_for_block(self, url, request):
        return request

class DownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        request.meta['proxy'] = format_proxy()
        return None

    def process_response(self, request, response, spider):
        return response

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
