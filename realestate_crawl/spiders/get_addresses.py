import io
import csv
import json

import scrapy

import realestate_crawl.utils as utils
import realestate_crawl.settings as settings


class RedfinGetAddressesSpider(scrapy.Spider):
    AUTO_COMPLETE_URL_BASE = "https://www.redfin.com/stingray/do/location-autocomplete?location={}&v=2"

    name = "get_redfin_addresses"
    custom_settings = {
        "ITEM_PIPELINES": {
            "realestate_crawl.pipelines.RedfinGetAddressesPipeline": 1,
        },
        "RETRY_TIMES": 20,
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
        else:
            for div in response.css(".HomeCardContainer"):
                page_url = div.css("a::attr(href)").get()
                price = div.css(".homecardV2Price::text").get()
                home_stats = div.css(".HomeStatsV2 .stats::text").getall()
                beds = baths = sq_ft = ""
                try:
                    beds = home_stats[0].replace("Beds", "").replace("Bed", "").strip()
                    baths = home_stats[1].replace("Baths", "").replace("Bath", "").strip()
                    sq_ft = home_stats[2].replace("Sq. Ft.", "").strip()
                except Exception as e:
                    self.logger.error("Error when extracting beds, baths, ")
                address = div.css(".link-and-anchor::text").get()
                if not page_url:
                    continue
                yield {
                    "URL": response.urljoin(page_url), "ADDRESS": address,
                    "LAST_SOLD_PRICE": price,
                    "BEDS": beds, "BATHS": baths, "SQ. FT.": sq_ft
                }
            # Try to get next page
            current_a_tag = response.css(".selected.goToPage")
            if current_a_tag:
                next_page = current_a_tag.xpath("following-sibling::a[1]/@href").get()
                if next_page:
                    self.logger.info(f"Getting next page : {next_page}")
                    yield response.follow(next_page, callback=self.parse_search_filter)
                else:
                    self.logger.info("Reached end page")

    def parse_item(self, response):
        yield {
            "body": response.body
        }


class MergeRedfinGetAddressSpider(scrapy.Spider):
    name = "merge_get_redfin_addresses"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {},
        "ITEM_PIPELINES": {
            "realestate_crawl.pipelines.RedfinGetAddressesPipeline": 1,
        },
    }

    def start_requests(self, **kwargs):
        for f in self.settings["CSV_OUT_DIR"].iterdir():
            if not f.is_file() or not f.name.startswith("get_redfin_addresses"):
                continue
            yield scrapy.Request(f"file://{str(f.resolve())}")

    def parse(self, response):
        f = io.StringIO(response.text)
        csv_file = csv.DictReader(f)
        for line in csv_file:
            yield line


class LoopnetGetAddressesSpider(scrapy.Spider):
    LOOK_UP_URL = "https://www.loopnet.com/services/geography/lookup/?includeSectionHeaders=True"
    SEARCH_URL = "https://www.loopnet.com/services/search"
    PROPERTY_TYPES = {
        "All": 4095,
        "Office": 32,
        "Industrial": 1,
        "Retail": 2,
        "Restaurant": 2048,
        "Shopping Center": 4,
        "Multifamily": 8,
        "Specialty": 16,
        "Health Care": 64,
        "Hospitality": 128,
        "Sports & Entertainment": 256,
        "Land": 512,
        "Residential Income": 1024,
    }
    CONDOS_FILTER = {
        "include": 0,
        "only": 1,
        "exclude": 2,
    }

    name = "get_loopnet_addresses"
    custom_settings = {
        "ITEM_PIPELINES": {},
        "FEED_FORMAT": "csv",
        "FEED_URI": f"{settings.CSV_OUT_DIR}/{name} {utils.get_datetime_now_str()}.csv",
        "FEED_EXPORT_FIELDS": [
            "url", "address", "Sale Type", "Property Type", "Property Subtype", "Building Class", "Parking", "Zoning",
            "Frontage", "Opportunity Zone", "Year Built", "Price", "Price Per SF", "Cap Rate", "NOI",
            "Tenancy", "Building Height", "Building FAR", "Land Acres", "Amenities", "Parcel Number",
            "Land Assessment", "Improvements Assessment", "Total Assessment",
        ]
    }
    form_data = {
        "criteria": {
            "LNPropertyTypes": 0,
            "PropertyTypes": 0,
            "ApartmentStyleTypes": 0,
            "Country": "US",
            "State": "",
            "Market": "",
            "MSA": None,
            "County": "",
            "City": "",
            "PostalCode": "",
            "PageLocationLabel": "",
            "IncludeProximityCities": False,
            "AddressLine": None,
            "Distance": 2,
            "Radius": None,
            "CoordinateBounds": None,
            "Polygon": None,
            "HasValidCoordinates": None,
            "BuildingClass": 0,
            "BuildingSizeUom": "SquareFeet",
            "LotSizeUom": "Acres",
            "Editor": "Universal",
            "PreserveAddressForRadiusSavedSearch": False,
            "ListingSearchType": 1,
            "OnMarketDateRange": None,
            "Keywords": None,
            "PropertyGroupId": None,
            "IsForSale": True,
            "PriceRangeMin": None,
            "PriceRangeMax": None,
            "BuildingSizeRangeMin": None,
            "BuildingSizeRangeMax": None,
            "PriceRangeCurrency": None,
            "PriceRangeRateType": "Total",
            "LotSizeRangeMin": None,
            "LotSizeRangeMax": None,
            "UnitCountRangeMin": None,
            "UnitCountRangeMax": None,
            "CapRateRangeMin": "",
            "CapRateRangeMax": "",
            "YearBuiltRangeMin": None,
            "YearBuiltRangeMax": None,
            "TermLengthRangeMin": None,
            "TermLengthRangeMax": None,
            "NetLeased": False,
            "InContract": True,
            "Distressed": False,
            "Auction": False,
            "IsTenXAuctions": False,
            "AuctionIds": None,
            "Single": False,
            "Multiple": False,
            "InvestmentTypeCore": False,
            "InvestmentTypeValueAdd": False,
            "InvestmentTypeOpportunistic": False,
            "InvestmentTypeTripleNet": False,
            "InvestmentTypeOpportunityZone": False,
            "BusinessForSale": True,
            "VacantOwner": True,
            "Investment": True,
            "InOpportunityZone": None,
            "CondosFilter": 0,
            "PortfoliosFilter": 0,
            "ShoppingCenterFilter": 0,
            "BuildingParkFilter": 0,
            "IsForLease": False,
            "LeaseRateRangeMin": None,
            "LeaseRateRangeMax": None,
            "SpaceAvailableRangeMin": None,
            "SpaceAvailableRangeMax": None,
            "LeaseRateTerm": "y",
            "SpaceAvailableUom": "SquareFeet",
            "LeaseRateCurrency": None,
            "LeaseRatePerSizeUom": "SquareFeet",
            "SubLease": False,
            "RegionalMarket": None,
            "SubMarket": "",
            "MoveInDateIndicator": 0,
            "MoveInDateEnteredType": None,
            "MoveInDateEnteredRangeMin": None,
            "MoveInDateEnteredRangeMax": None,
            "ListingId": None,
            "DateIndicator": 0,
            "DateEnteredRangeMin": "",
            "DateEnteredRangeMax": "",
            "MinimumDate": "01/01/0001",
            "DateEnteredType": "RT",
            "DateFormat": "MM/dd/yyyy",
            "ViewMode": "None",
            "ListingIdPinClick": None,
            "IsUserFromUS": False,
            "ForceRemoveBoundary": True,
            "AgentFirstName": None,
            "AgentLastName": None,
            "ResultLimit": 500,
            "PageNumber": 1,
            "PageSize": 20,
            "LeaseRateUomTerm": "SquareFeetYear",
            "ExcludingInContract": False
        }
    }

    def __init__(self, city, state, **kwargs):
        self.city = city
        self.state = state
        self.filter = {
            "min_price": kwargs.get("min"),
            "max_price": kwargs.get("max"),
            "type": kwargs.get("t"),
            # Currently support for `For Sale`
            "need": kwargs.get("n"),
            "min_year_built": kwargs.get("ymin"),
            "max_year_built": kwargs.get("ymax"),
            "min_cap_rate": kwargs.get("cmin"),
            "max_cap_rate": kwargs.get("cmax"),
            "min_size": kwargs.get("smin"),
            "max_size": kwargs.get("smax"),
            "condos": kwargs.get("c", "include"),
        }

    def _fill_form_data(self):
        self.form_data["criteria"]["LNPropertyTypes"] = self.PROPERTY_TYPES.get(
            self.filter["type"])
        self.form_data["criteria"]["PriceRangeMin"] = self.filter["min_price"]
        self.form_data["criteria"]["PriceRangeMax"] = self.filter["max_price"]
        self.form_data["criteria"]["YearBuiltRangeMin"] = self.filter["min_year_built"]
        self.form_data["criteria"]["YearBuiltRangeMax"] = self.filter["max_year_built"]
        self.form_data["criteria"]["CapRateRangeMin"] = self.filter["min_cap_rate"]
        self.form_data["criteria"]["CapRateRangeMax"] = self.filter["max_cap_rate"]
        self.form_data["criteria"]["BuildingSizeRangeMin"] = self.filter["min_size"]
        self.form_data["criteria"]["BuildingSizeRangeMax"] = self.filter["max_size"]
        self.form_data["criteria"]["CondosFilter"] = self.CONDOS_FILTER.get(
            self.filter["condos"])

    def start_requests(self):
        yield scrapy.Request(
            self.LOOK_UP_URL,
            method="POST",
            body=json.dumps(
                {"i": f"{self.city} {self.state}", "l": [None, None]}
            ),
            headers={"content-type": "application/json"},
            callback=self.parse_lookup
        )

    def parse_lookup(self, response):
        try:
            j_data = json.loads(response.text)
            if len(j_data) < 1:
                self.logger.warn(f"No results in lookup: {j_data}")
                return
            address = j_data[1]
            bb = address["BoundingBox"]
            GeographyFilters = [{
                "ID": None,
                "BoundingBox": [
                    bb["UpperLeft"]["x"], bb["LowerRight"]["y"],
                    bb["LowerRight"]["x"], bb["UpperLeft"]["y"]
                ],
                "Centroid": [address["Location"]["x"], address["Location"]["y"]],
                "Display": address["Display"], "GeographyId": address["ID"],
                "Code": address["Address"]["State"], "GeographyType": address["GeographyType"],
                "Radius": 0, "RadiusLengthMeasure": 0, "SubmarketPropertyType": 0,
                "Address": None, "MatchType": address["MatchType"]
            }]
            # Fill form data with address
            self.form_data["GeographyFilters"] = GeographyFilters
            self.form_data["criteria"]["Country"] = address["Address"]["Country"]
            self.form_data["criteria"]["State"] = address["Address"]["State"]
            self.form_data["criteria"]["City"] = address["Address"]["City"]
            self.form_data["criteria"]["PageLocationLabel"] = address["Display"]
            # Fill form data with filter
            self._fill_form_data()
            yield scrapy.Request(
                self.SEARCH_URL, method="POST", body=json.dumps(self.form_data),
                headers={"content-type": "application/json"}, callback=self.parse_search
            )
        except Exception as e:
            self.logger.error(f"Error when parsing lookup: {e}")

    def parse_search(self, response):
        j_data = json.loads(response.text)
        try:
            url = j_data['UrlState']['Url']
        except Exception as e:
            self.logger.error(f"Error when parsing search: {e}")
            return
        yield scrapy.Request(url, callback=self.parse_listing)

    def parse_listing(self, response):
        for href in response.css(".placard-pseudo a::attr(ng-href)").getall():
            yield response.follow(href, callback=self.parse_item)
        next_page_url = response.css(
            '.paging a[data-automation-id="NextPage"]::attr(href)').get()
        if next_page_url:
            self.logger.info(f"Gettting next page: {next_page_url}")
            yield response.follow(next_page_url, callback=self.parse_listing)
        else:
            self.logger.info(f"No next page")

    def parse_item(self, response):
        try:
            address = response.url.split("/")[-3].replace("-", " ")
        except Exception as e:
            self.logger.error(
                f"Error when getting address from {response.url}: {e}")
        data = {
            "url": response.url,
            "address": address,
        }
        # Get property data using table.property-data
        for tr in response.css("table.property-data tr"):
            lables = filter(lambda x: x.strip(), tr.css("td::text").getall())
            values = filter(lambda x: x.strip(), tr.css(
                "span::text, td > div::text").getall())
            for label, value in zip(lables, values):
                data[label.strip()] = value.strip()
        # Get more property data
        labels, values = [], []
        for t in response.css(".property-facts__labels-item::text").getall():
            t = t.strip()
            if t not in labels:
                labels.append(t)
        for t in response.css(".property-facts__data-item-text::text").getall():
            if t not in values:
                values.append(t)
        for k, v in zip(labels, values):
            data[k] = v
        data["Amenities"] = ", ".join(response.css(
            ".features-and-amenities span::text").getall())
        yield data
