# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import csv

import scrapy

import realestate_crawl.settings as settings

class ImageDownloadSpider(scrapy.Spider):
    name = "download_images"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {},
        "ITEM_PIPELINES": {},
        "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",
    }

    def __init__(self, folder_name):
        self.folder_name = settings.IMAGES_OUT_DIR / folder_name

    def start_requests(self, **kwargs):
        if not self.folder_name.exists():
            self.logger.error(f"{self.folder_name} doesn't exist")
            return
        for f_path in self.folder_name.iterdir():
            if not f_path.is_file():
                continue
            with open(f_path) as f:
                csv_file = csv.DictReader(f)
                for line in csv_file:
                    if not line.get("id") or not line.get("link"):
                        break
                    yield scrapy.Request(
                        line["link"],
                        meta={
                            "location_id": line["id"],
                            "source": f_path.name.split(".")[0],
                        }
                    )

    def parse(self, response):
        folder_out = settings.DOWNLOADED_IMG_DIR / self.folder_name.name / response.meta["location_id"]
        folder_out.mkdir(parents=True, exist_ok=True)
        with open(folder_out / f"{response.meta['source']}_{response.url.split('/')[-1]}", "wb") as f:
            f.write(response.body)
