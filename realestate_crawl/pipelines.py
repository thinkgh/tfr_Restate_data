# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import csv

from scrapy.exceptions import DropItem

from realestate_crawl import settings
import realestate_crawl.utils as utils


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
        if not item.get("images"):
            return item
        location_id = item["location_id"]
        for link in item["images"]:
            self.csv_write.writerow([location_id, link])
        self.output_file.flush()
        raise DropItem("Drop item with images link")

    def close_spider(self, spider):
        self.output_file.close()


class RedfinGetAddressesPipeline(object):
    rows = []
    addresses = []

    def process_item(self, item, spider):
        if "body" in item:
            with open(settings.CSV_OUT_DIR / f"{spider.name} {utils.get_datetime_now_str()}.csv", "wb") as f:
                f.write(item["body"])
        address = item.get("ADDRESS") 
        if address and address not in self.addresses:
            self.addresses.append(address)
            self.rows.append(item)
        return item

    def close_spider(self, spider):
        if self.rows:
            out_file = settings.CSV_OUT_DIR / f"{spider.name} {utils.get_datetime_now_str()}.csv" 
            spider.logger.info(f"Writing {len(self.rows)} lines to {out_file}")
            with open(out_file, "w") as f:
                writer = csv.DictWriter(f, fieldnames=self.rows[0].keys())
                writer.writeheader()
                writer.writerows(self.rows)
        else:
            spider.logger.info(f"There are no returned items")