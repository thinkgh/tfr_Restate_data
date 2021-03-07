# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import os
import csv
import pathlib

import scrapy
import scrapy.exceptions as scrapy_except
import scrapy.crawler as crawler

import realestate_crawl.utils as utils

class BaseSpider(scrapy.Spider):
    name = ""
    NUMBER_FIELDS_ALLOWED = 5
    custom_settings = {}

    def __init__(self, input_file, **kwargs):
        self.input_file = pathlib.Path(input_file)
        self.delimiter = kwargs.get("delimiter", ";")
        self.field1 = kwargs.get("field1", "locationId")
        self.params = kwargs
        self.params["field2"] = self.params.get("field2", "Address")
        self.images = kwargs.get("images") == "true"

    def get_request(self, line: dict):
        pass

    def get_address_str(self, line: dict):
        values = []
        for i in range(2, self.NUMBER_FIELDS_ALLOWED + 1):
            field_name = f"field{i}"
            if field_name in self.params:
                values.append(line[self.params[field_name]])
        return ", ".join(values)
  
    def parse_detail_page(self, response: scrapy.http.HtmlResponse):
        data = self.get_data(response)
        if data:
            yield {
                "Location id": response.meta["location_id"],
                "url": response.url,
                **data
            }
        if self.images:
            image_links = self.get_images(response)
            if image_links:
                yield {
                    "location_id": response.meta["location_id"],
                    "images": image_links
                }

    def get_images(self, response: scrapy.http.HtmlResponse):
        pass

    def get_data(self, response: scrapy.http.HtmlResponse):
        return None

    def get_meta_for_request(self, line: dict):
        return {
            "location_id": line[self.field1]
        }

    def start_requests(self, **kwargs):
        with open(self.input_file) as f:
            csv_file = csv.DictReader(f, delimiter=self.delimiter)
            for line in csv_file:
                yield self.get_request(line)
