from scrapy.exporters import CsvItemExporter

import realestate_crawl.utils as utils

class MyCSVExporter(CsvItemExporter):

    def export_item(self, item):
        if not item or "images" in item:
            return
        super().export_item(item)
