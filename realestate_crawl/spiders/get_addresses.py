import scrapy

import realestate_crawl.utils as utils


class RedfinGetAddressesSpider(scrapy.Spider):
    AUTO_COMPLETE_URL_BASE = "https://www.redfin.com/stingray/do/location-autocomplete?location={}&v=2"

    name = "get_redfin_addresses"
    custom_settings = {
        "ITEM_PIPELINES" : {
            "realestate_crawl.pipelines.RedfinGetAddressesPipeline": 1,
        },
        "DOWNLOADER_MIDDLEWARES": {},
    }

    def __init__(self, city, state, **kwargs):
        self.city = city
        self.state = state
        self.filter = {
            "min": kwargs.get("min", "350k"),
            "max": kwargs.get("max", "2m"),
            "type": kwargs.get("t", "house"),
            "sold": kwargs.get("s", "3mo"),
            "year_built": kwargs.get("y", "1999"),
            "basement": kwargs.get("b", None),
            "waterfront": kwargs.get("w", "no"),
            "pool": kwargs.get("p", "no")
        }
    
    def start_requests(self):
        yield scrapy.Request(
            self.AUTO_COMPLETE_URL_BASE.format(self.city + " " + self.state),
            callback=self.parse_autocomplete
        )

    def _get_filter_str(self):
        filter_str = (
            f"/filter/property-type={self.filter['type']},min-price={self.filter['min']},"
            f"max-price={self.filter['max']},max-year-built={self.filter['year_built']},"
            f"include=sold-{self.filter['sold']}"
        )
        if self.filter["basement"]:
            filter_str += f",basement-type={self.filter['basement']}"
        if self.filter["waterfront"] == "yes":
            filter_str += ",water-front"
        if self.filter["pool"] == "yes":
            filter_str += ",has-pool"
        return filter_str
        

    def parse_autocomplete(self, response):
        data = utils.parse_json_string(response.text[4:])
        try:
            search_url = data["payload"]["exactMatch"]["url"]
            yield response.follow(
                search_url + self._get_filter_str(),
                callback=self.parse_search_filter
            )
        except Exception as e:
            self.logger.error("Error when getting search url: " + str(e))


    def parse_search_filter(self, response):
        download_url = response.css("#download-and-save::attr(href)").get()
        if download_url:
            yield response.follow(download_url, callback=self.parse_item)

    def parse_item(self, response):
        yield {
            "body": response.body
        }