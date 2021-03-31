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

    def _get_output_file_name(self, spider):
        return f"{spider.city}_{spider.state}_{spider.name} {utils.get_datetime_now_str()}.csv"

    def _get_output_file(self, spider):
        if spider.name == "merge_get_redfin_addresses":
            out_folder = settings.CSV_OUT_DIR / "merge"
            out_folder.mkdir(exist_ok=True, parents=True)
        else:
            out_folder = settings.CSV_OUT_DIR
        return out_folder / self._get_output_file_name(spider)
        

    def process_item(self, item, spider):
        if "body" in item:
            with open(self._get_output_file(spider) , "wb") as f:
                f.write(item["body"])
        address = item.get("ADDRESS") 
        if address and address not in self.addresses:
            self.addresses.append(address)
            self.rows.append(item)
        return item

    def close_spider(self, spider):
        if self.rows:
            out_file = self._get_output_file(spider)
            spider.logger.info(f"Writing {len(self.rows)} lines to {out_file}")
            retry_rows = []
            with open(out_file, "w") as f:
                writer = csv.DictWriter(f, fieldnames=self.rows[0].keys())
                writer.writeheader()
                for row in self.rows:
                    try:
                        writer.writerow(row)
                    except Exception as e:
                        spider.logger.error(f"Error when saving row {row}: {e}")
                        retry_rows.append(row)
            if not retry_rows:
                return
            # Try to write another csv file with error rows
            with open(self._get_output_file(spider), "w") as f:
                writer = csv.DictWriter(f, fieldnames=retry_rows[0].keys())
                writer.writeheader()
                writer.writerows(retry_rows)
        else:
            spider.logger.info(f"There are no returned items")