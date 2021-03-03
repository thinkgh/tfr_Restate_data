import re
import sys
import csv
import json
import random
import requests

import scrapy

import realestate_crawl.utils as utils
from realestate_crawl.spiders import BaseSpider
import realestate_crawl.settings as settings


class RealtorSpider(BaseSpider):
    REALTOR_SEARCH_URL = "https://parser-external.geo.moveaws.com/suggest?input={}&client_id=rdc-home&limit=10&area_types=address%2Cneighborhood%2Ccity%2Ccounty%2Cpostal_code%2Cstreet%2Cbuilding%2Cschool%2Cschool_district%2Cuniversity%2Cpark%2Cstate%2Cmlsid&lat=-1&long=-1"
    DETAIL_URL_BASE = "https://www.realtor.com/realestateandhomes-detail/{}_{}_{}_{}_M{}-{}"

    name = "realtor"

    custom_settings = {
        "COMPRESSION_ENABLED": False,
        "FEED_FORMAT": "csv",
        "FEED_URI": f"{settings.CSV_OUT_DIR}/realtor {utils.get_datetime_now_str()}.csv",
        "FEED_EXPORT_FIELDS": [
            "Location id", "url", "Price", "Beds", "Baths", "Rooms", "House size", "Stories",
            "Lot size", "Garage", "Heating", "Cooling", "Year built", "Year renovated",
            "Property type", "Style", "Date updated", "Fireplace", "Flood factor",
        ]
    }

    def get_request(self, line):
        return scrapy.Request(
            url=self.REALTOR_SEARCH_URL.format(self.get_address_str(line)),
            callback=self.parse_search,
            meta=self.get_meta_for_request(line),
        )

    def parse_search(self, response):
        try:
            resp = json.loads(response.body)
            first_result = resp["autocomplete"][0]
        except Exception as e:
            self.logger.error("Error when getting first result:", e)
            return
        try:
            if first_result.get("area_type") == 'address':
                line = first_result['line'].replace(' ', '-')
                city = first_result['city'].replace(' ', '-')
                state_code = first_result['state_code']
                postal_code = first_result['postal_code']
                mpr_id = first_result['mpr_id']
                detail_url = self.DETAIL_URL_BASE.format(
                    line, city, state_code, postal_code,
                    mpr_id[0:-5], mpr_id[-5:]
                )
                yield response.follow(
                    detail_url,
                    callback=self.parse_detail_page,
                    meta=response.meta,
                )
        except Exception as e:
            self.logger.error("Error when pasring result:", e)

    def get_images(self, response: scrapy.http.HtmlResponse):
        images = response.css('#ldpHeroCarousel img::attr(data-src)').getall()
        for index, img in enumerate(images):
            # Skip small image
            if 'w60' not in img:
                self.download_image(img, response.meta["location_id"] , index=index)

    def get_data(self, response):
        data = {}
        li_texts = response.css("#ldp-detail-public-records li::text").getall()
        for text in li_texts:
            text_split = text.split(":")
            if len(text_split) != 2:
                self.logger.warn("It is weird in get data:", text)
                continue
            data[text_split[0]] = text_split[1].strip()
        data["Beds"] = response.css("#ldp-property-meta li[data-label=property-meta-beds] > span::text").get()
        data["Baths"] = response.css("#ldp-property-meta li[data-label=property-meta-bath] > span::text").get()
        data["House size"] = utils.get_text_of_selector(
            response.css("#ldp-property-meta li[data-label=property-meta-sqft] ::text").getall()
        )
        data["Flood factor"] = response.css(".ldp-flood-score > b::text").get()

        price = response.css("span.price::text").get()
        if not price:
            price_text = utils.get_text_of_selector(
                response.css(".ldp-header-price span *::text").getall()
            )
            if price_text:
                price = utils.search_with_pattern(r"[$,\d]+", price_text, group=0)
        data["Price"] = price

        return data
