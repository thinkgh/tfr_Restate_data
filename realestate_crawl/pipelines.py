# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import csv
from realestate_crawl import settings


class ImageLinksPipeline(object):
    def open_spider(self, spider):
        output_dir = settings.IMAGES_OUT_DIR / spider.input_file.name
        output_dir.mkdir(exist_ok=True, parents=True)
        output_file = output_dir / f"{spider.name}.txt"
        write_headers = True
        if output_file.exists():
            write_headers = False
        self.output_file = open(output_file, "a")
        self.csv_write = csv.writer(self.output_file)
        if write_headers:
            self.csv_write.writerow(["id", "link"])

    def process_item(self, item, spider):
        if "images" not in item:
            return item
        location_id = item["location_id"]
        for link in item["images"]:
            self.csv_write.writerow([location_id, link])
        self.output_file.flush()
        return item

    def close_spider(self, spider):
        self.output_file.close()
