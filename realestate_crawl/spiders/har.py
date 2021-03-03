# -*- coding: utf-8 -*-
import re
import csv

import scrapy

from realestate_crawl.spiders import BaseSpider
from realestate_crawl.utils import format_proxy, mkdir, download_image


class HarSpider(BaseSpider):
    name = 'har'

    SEARCH_URL = 'https://www.har.com/search/dosearch?for_sale=1&quicksearch={}'

    count = 0

    def get_request(self, address):
        url_search = self.SEARCH_URL.format(address['address'].replace(' ', '+'))
        return scrapy.Request(
            url_search,
            meta=address,
            callback=self.parse_search,
            errback=self.errback
        )

    def parse_search(self, response):
        yield self.next_request_from_addresses_poll()
        self.count += 1
        print('Parsing search page for {}-th addresses'.format(self.count))
        divs = response.css('.prop_item')

        has_images = False
        if divs:
            detail_page_url = divs[0].css('.mpi_img_link::attr(href)').get()
            title = ' '.join(divs[0].css('.address *::text').getall())
            if detail_page_url and response.meta.get("zip_code", "") in title:
                has_images = True
                yield response.follow(
                    detail_page_url,
                    callback=self.parse_detail_page,
                    meta=response.meta
                )
        if not has_images:
            self.set_no_images(response)

    def get_price_and_year_built(self, response):
        price = year_built = None
        for block in response.css('.dc_blocks_2c'):
            label = block.css('.dc_label::text').get()
            value = block.css('.dc_value::text').get()
            if label == 'Listing Price:':
                price = value
            if label == 'Year Built:':
                search = re.search('\d+', value)
                if search:
                    try:
                        year_built = int(search.group().strip())
                    except:
                        pass
                break
        self.save_price_year_built(response.meta['location_id'], price, year_built)
    
    def parse_detail_page(self, response):
        self.get_price_and_year_built(response)
        slides = response.css('ul.slides')
        if slides:
            location_id = response.meta['location_id']
            image_urls = slides[0].css('li a::attr(href)').getall()
            for i, image_url in enumerate(image_urls):
                download_image(
                    url=image_url,
                    image_folder=self.output_dir + '/' + location_id,
                    file_name='{}_har_{}.jpg'.format(location_id, i)
                )
            self.check_exist_images(self.output_dir + '/' + location_id, response)
        else:
            print('No images')
            self.set_no_images(response)
        
