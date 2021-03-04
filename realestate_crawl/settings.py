import os
import sys
import pathlib


BOT_NAME = 'realestate_crawl'

SPIDER_MODULES = ['realestate_crawl.spiders']
NEWSPIDER_MODULE = 'realestate_crawl.spiders'

# Folders for output result
PROJECT_DIR = pathlib.Path(__file__).parent.parent
OUTPUT_DIR = os.getenv('OUTPUT_DIR', PROJECT_DIR / 'output')
if type(OUTPUT_DIR) == str:
   OUTPUT_DIR = pathlib.Path(OUTPUT_DIR)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
IMAGES_OUT_DIR = OUTPUT_DIR / 'image_links'
IMAGES_OUT_DIR.mkdir(exist_ok=True, parents=True)
CSV_OUT_DIR = OUTPUT_DIR / 'csv'
CSV_OUT_DIR.mkdir(exist_ok=True, parents=True)
DOWNLOADED_IMG_DIR = OUTPUT_DIR / 'images'
DOWNLOADED_IMG_DIR.mkdir(exist_ok=True, parents=True)

HTTPPROXY_ENABLED = True

# For retry
RETRY_TIMES = 10
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 405, 403]

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
   'realestate_crawl.middlewares.DownloaderMiddleware': 543,
   'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 544,
}

# Configure item pipelines
ITEM_PIPELINES = {
   'realestate_crawl.pipelines.ImageLinksPipeline': 1,
}

# Set request filter
DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'

# Log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = str(PROJECT_DIR / "log.txt") if os.getenv("LOG_FILE") == "true" else None


FEED_EXPORTERS = {
   "csv": "realestate_crawl.exporter.MyCSVExporter",
}