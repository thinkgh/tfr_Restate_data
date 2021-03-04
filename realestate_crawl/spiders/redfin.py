# -*- coding: utf-8 -*-
import csv
import json
import collections as coll

import scrapy
import requests

import realestate_crawl.utils as utils
import realestate_crawl.settings as settings
from realestate_crawl.spiders import BaseSpider
import realestate_crawl.map as mp
import realestate_crawl.constant as const


class RedfinSpider(BaseSpider):
    SEARCH_URL = "https://www.redfin.com/stingray/do/location-autocomplete?location={}&start=0&count=10&v=2&market=philadelphia&al=1&iss=false&ooa=true&mrs=false"

    name = 'redfin'
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            'accept': 'application/json',
            "cookie": "RF_CORVAIR_LAST_VERSION=356.0.0; RF_BROWSER_ID=YnxQTsdbTsK-Is6eoWOfIA; RF_VISITED=false; RF_BID_UPDATED=1; RF_MARKET=houston; RF_BUSINESS_MARKET=22; AKA_A2=A; _gcl_au=1.1.28871832.1614816368; run_fs_for_user=603; _uetsid=6b7518d07c7d11eb97a9f5e3f843aed3; _uetvid=6b75ce207c7d11eb8dc8c9a05d47d79a; AMP_TOKEN=%24NOT_FOUND; _ga=GA1.2.36233513.1614816369; _gid=GA1.2.1419259929.1614816369; RF_LAST_SEARCHED_CITY=Houston; FEED_COUNT=0%3Af; G_ENABLED_IDPS=google; RF_BROWSER_CAPABILITIES=%7B%22screen-size%22%3A3%2C%22ie-browser%22%3Afalse%2C%22events-touch%22%3Afalse%2C%22ios-app-store%22%3Afalse%2C%22google-play-store%22%3Afalse%2C%22ios-web-view%22%3Afalse%2C%22android-web-view%22%3Afalse%7D"
        },
        "DOWNLOADER_MIDDLEWARES": {

        },
        "FEED_FORMAT": "csv",
        "FEED_URI": f"{settings.CSV_OUT_DIR}/{name} {utils.get_datetime_now_str()}.csv",
        "FEED_EXPORT_FIELDS": const.REDFIN_FIELDS,
    }

    def get_request(self, line: dict):
        url_search = self.SEARCH_URL.format(self.get_address_str(line))
        return scrapy.Request(
            url=url_search,
            callback=self.parse_search,
            meta=self.get_meta_for_request(line),
        )

    def parse_search(self, response):
        try:
            resp = json.loads(response.body[4:])
            url = resp['payload']['sections'][0]["rows"][0]["url"]
        except Exception as e:
            self.logger.error("Error when getting url: " + str(e))
            return
        yield response.follow(url, callback=self.parse_detail_page, meta=response.meta)

    def get_images(self, response):
        links = []
        try:
            body = response.xpath(
                'string(//body)').re_first(r"root\.__reactServerState\.InitialContext = (.+);")
            resp = json.loads(body)
            resp = json.loads(resp['ReactServerAgent.cache']['dataCache']
                              ['/stingray/api/home/details/aboveTheFold']['res']['text'][4:])
            photos = resp['payload']['mediaBrowserInfo']['photos']
        except Exception as e:
            self.logger.error("Error when getting photos:" + str(e))
        if photos and type(photos) == list:
            for photo in photos:
                image_url = None
                try:
                    image_url = photo['photoUrls']['fullScreenPhotoUrl']
                except Exception as e:
                    self.logger.error(
                        "Error when getting image url: " + str(e))
                if image_url:
                    links.append(image_url)
        else:
            img_src = response.css(
                '.img-card.streetViewImage::attr(src)').get()
            if img_src:
                links.append(img_src)
        return links

    def get_data(self, response):
        data = coll.defaultdict(lambda: "")
        # Get basic info
        data["Price"] = response.css(".RedfinEstimateValueHeader .value::text").get()
        for div in response.css("#basicInfo .table-row"):
            label = div.css(".table-label::text").get()
            value = div.css(".table-value::text").get()
            if not label:
                continue
            data[label] = value

        # Get detail info
        for div in response.css("#propertyDetails-collapsible .entryItemContent"):
            title = div.xpath("../../h3/text()").get()
            if title:
                suffix = title + "_"
            else:
                suffix = ""
            text = utils.get_text_of_selector(div.css("*::text").getall())
            text_split = text.split(":")
            if len(text_split) == 2:
                k = suffix + text_split[0]
                k = mp.REDFIN_KEY_MAP.get(k, k)
                data[k] = text_split[1].strip()
                continue
            if title:
                k = mp.REDFIN_KEY_MAP.get(title, title)
                data[k] += text + "\n"
            else:
                self.logger.warn("No title for: " + text)

        return data
