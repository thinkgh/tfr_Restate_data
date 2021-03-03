# -*- coding: utf-8 -*-
import csv
import json

import scrapy
import requests

import realestate_crawl.utils as utils
import realestate_crawl.settings as settings
from realestate_crawl.spiders import BaseSpider


class RedfinSpider(BaseSpider):
    SEARCH_URL = "https://www.redfin.com/stingray/do/location-autocomplete?location={}&start=0&count=10&v=2&market=philadelphia&al=1&iss=false&ooa=true&mrs=false"

    name = 'redfin'
    custom_settings = {
        "FEED_FORMAT": "csv",
        "FEED_URI": f"{settings.CSV_OUT_DIR}/{name} {utils.get_datetime_now_str()}.csv",
        "FEED_EXPORT_FIELDS": [
        ]
    }
    
    def get_request(self, line: dict):
        url_search = self.SEARCH_URL.format(self.get_address_str(line))
        return scrapy.Request(
            url=url_search,
            callback=self.parse_search,
            headers={'accept': 'application/json', 'cookie':'RF_BROWSER_ID=_-ZqlIfiRliiTvv4r_kIOg; RF_CORVAIR_LAST_VERSION=281.1.0; RF_BID_UPDATED=1; _gcl_au=1.1.1420189527.1568722855; RF_BROWSER_CAPABILITIES=%7B%22css-transitions%22%3Atrue%2C%22css-columns%22%3Atrue%2C%22css-generated-content%22%3Atrue%2C%22css-opacity%22%3Atrue%2C%22events-touch%22%3Afalse%2C%22geolocation%22%3Atrue%2C%22screen-size%22%3A4%2C%22screen-size-tiny%22%3Afalse%2C%22screen-size-small%22%3Afalse%2C%22screen-size-medium%22%3Afalse%2C%22screen-size-large%22%3Afalse%2C%22screen-size-huge%22%3Atrue%2C%22html-prefetch%22%3Atrue%2C%22html-range%22%3Atrue%2C%22html-form-validation%22%3Atrue%2C%22html-form-validation-with-required-notice%22%3Atrue%2C%22html-input-placeholder%22%3Atrue%2C%22html-input-placeholder-on-focus%22%3Atrue%2C%22ios-app-store%22%3Afalse%2C%22google-play-store%22%3Afalse%2C%22ios-web-view%22%3Afalse%2C%22android-web-view%22%3Afalse%2C%22activex-object%22%3Atrue%2C%22webgl%22%3Atrue%2C%22history%22%3Atrue%2C%22localstorage%22%3Atrue%2C%22sessionstorage%22%3Atrue%2C%22position-fixed-workaround%22%3Afalse%2C%22passive-event-listener%22%3Atrue%7D; G_ENABLED_IDPS=google; RF_GOOGLE_ONE_TAP_DISMISSED=lastDismissalDate%3D1568722860411; RF_VISITED=null; AKA_A2=A; unifiedLastSearch=name%3D130%252087th%2520St%26subName%3DStone%2520Harbor%252C%2520NJ%252C%2520USA%26url%3D%252FNJ%252FStone-Harbor%252F130-87th-St-08247%252Fhome%252F62511943%26id%3D9_62511943%26type%3D1%26isSavedSearch%3D%26countryCode%3DUS; RF_MARKET=philadelphia; RF_BUSINESS_MARKET=42; RF_LAST_SEARCHED_CITY=Stone%20Harbor; RF_LISTING_VIEWS=35317501'}, 
            meta=self.get_meta_for_request(line),
        )

    def parse_search(self, response):
        try:
            resp = json.loads(response.body[4:])
            url = resp['payload']['sections'][0]["rows"][0]["url"]
        except Exception as e:
            self.logger.error("Error when getting url:", e)
            return
        yield response.follow(url, callback=self.parse_detail_page, meta=response.meta)

    def get_images(self, response):
        location_id = response.meta['location_id']
        try:
            body = response.xpath('string(//body)').re_first(r"root\.__reactServerState\.InitialContext = (.+);")
            resp = json.loads(body)
            resp = json.loads(resp['ReactServerAgent.cache']['dataCache']['/stingray/api/home/details/aboveTheFold']['res']['text'][4:])
            photos = resp['payload']['mediaBrowserInfo']['photos']
        except Exception as e:
            self.logger.error("Error when getting photos:", e)
        if photos and type(photos) == list:
            for index, photo in enumerate(photos):
                image_url = None
                try:
                    image_url = photo['photoUrls']['fullScreenPhotoUrl']
                except Exception as e:
                    self.logger.error("Error when getting image url:", e)
                if image_url:
                    self.download_image(
                        photo['photoUrls']['fullScreenPhotoUrl'],
                        location_id,
                        index=index
                    )
        else:
            img_src = response.css('.img-card.streetViewImage::attr(src)').get()
            if img_src:
                self.download_image(img_src, location_id)

    def get_data(self, response):
        pass
