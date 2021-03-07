import re
import sys
import csv
import json
import random

import scrapy
import requests

import realestate_crawl.utils as utils
import realestate_crawl.settings as settings
from realestate_crawl.spiders import BaseSpider


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
        "FEED_FORMAT": "csv",
        "FEED_URI": f"{settings.CSV_OUT_DIR}/{name} {utils.get_datetime_now_str()}.csv",
    }

    def _get_data_json(self, response):
        raw_text = response.css("#hdpApolloPreloadedData::text").get()
        if not raw_text:
            return
        try:
            ori_data = json.loads(raw_text)
            data = json.loads(ori_data["apiCache"])
            return list(data.values())[1]
        except Exception as e:
            self.logger.error("Error when getting json from text: " + str(e))
            return


    def get_request(self, line: dict):
        return scrapy.Request(
            url=self.zillow_url.format(self.get_address_str(line)),
            callback=self.parse_detail_page,
            meta=self.get_meta_for_request(line),
        )

    def get_images(self, response):
        if "We could not find this area" in response.text:
            return
        j = self._get_data_json(response)
        if not j:
            return
        return [d["url"] for d in j["property"]["hugePhotos"]]

    def get_data(self, response):
        if "We could not find this area" in response.text:
            return
        j = self._get_data_json(response)
        if not j:
            return
        property_data = j["property"]
        data = property_data.get("resoFacts")
        if data:
            data.update({
                "price": property_data.get("price"),
            })
        return data
