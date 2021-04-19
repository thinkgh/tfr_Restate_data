import urllib.parse as url_prs

import scrapy
import realestate_crawl.utils as utils
import realestate_crawl.settings as settings


class Norfolkair(scrapy.Spider):
    name = "norfolkair"
    custom_settings = {
        "ITEM_PIPELINES": {},
        "DOWNLOADER_MIDDLEWARES": {},
        "FEED_FORMAT": "csv",
        "FEED_URI": f"{settings.CSV_OUT_DIR}/{name} {utils.get_datetime_now_str()}.csv",
        "FEED_EXPORTERS": {},
    }

    HOME_URL = "https://air.norfolk.gov/"
    SEARCH_API = f"{HOME_URL}data/search"
    ITEM_API = f"{HOME_URL}data/propertycard"
    IMAGE_API_BASE = f"{HOME_URL}images-api.php?type=photo&id=%s&json=1"
    FIRST_PAGE = 1

    def __init__(self, address):
        self.address = address

    def _get_search_data(self, address, page):
        page = str(page)
        return {
            "filters[term]": address,
            "filters[page]": page,
            "page": page,
            "limit": "21",
            "debug[currentURL]": f"{self.HOME_URL}#/search?term={url_prs.quote(address)}&page={page}",
            'debug[previousURL"]': self.HOME_URL,
        }

    def _get_item_data(self, parcel_id):
        return {
            "parcelid": parcel_id,
            "card": "", 
            "year": "", 
            "debug[currentURL]": f"{self.HOME_URL}#/property/{parcel_id}",
            'debug[previousURL"]': self.HOME_URL, 
        }

    def _get_next_page(self, pages):
        active_page = None
        for p in pages:
            if p["active"] == True:
                active_page = p["page"]
                break
        if active_page and active_page < len(pages):
            return active_page + 1
        return None

    def _get_search_form_request(self, page):
        return scrapy.FormRequest(
            self.SEARCH_API,
            formdata=self._get_search_data(self.address, page),
            meta={"page": page}
        )

    def start_requests(self):
        yield self._get_search_form_request(self.FIRST_PAGE)

    def parse(self, response):
        """
        Parse for searching API
        """
        json_data = utils.parse_json_string(response.text)
        if not json_data:
            self.logger.warn("No json data when searching")
            return
        search_results = json_data.get("searchResults", [])
        self.logger.info(f"Total results in page {response.meta['page']}: {len(search_results)}")
        for result in search_results:
            parcel_id = result.get("ParcelIdentifier")
            if not parcel_id:
                self.logger.warn(f"Can not find id in result: {result}")
                continue
            # Request for item
            yield scrapy.FormRequest(
                self.ITEM_API,
                formdata=self._get_item_data(parcel_id),
                callback=self.parse_item,
                meta={"parcel_id": parcel_id}
            )
        # Try next page
        next_page = self._get_next_page(json_data.get("pages"))
        if next_page:
            self.logger.info(f"Getting next page {next_page}")
            yield self._get_search_form_request(next_page)

    def parse_item(self, response):
        """
        Parse for item API
        """
        parcel_id = response.meta["parcel_id"]
        json_data = utils.parse_json_string(response.text)
        if not json_data:
            self.logger.warn(f"No json data in item API for {parcel_id}")
            return
        try:
            parcel = json_data["parcel"]
            data = parcel["header"]
            section_0 = parcel["sections"]["0"]
            for sec in section_0:
                if sec:
                    data.update(sec[0])
            # Get images
            yield scrapy.Request(
                self.IMAGE_API_BASE % (parcel_id),
                callback=self.parse_images,
                meta={"data": data}
            )
        except Exception as e:
            self.logger.error(f"Error when extracting data from item API {parcel_id}")

    def parse_images(self, response):
        """
        Parse for images API
        """
        data = response.meta["data"]
        images = utils.parse_json_string(response.text)
        if images is None:
            self.logger.warn(f"No json data in images API")
            return
        data.update({
            "images": " , ".join(images)
        })
        yield data
