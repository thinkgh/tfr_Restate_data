import io
import csv
import json

import scrapy

import realestate_crawl.utils as utils


class RedfinGetAddressesSpider(scrapy.Spider):
    AUTO_COMPLETE_URL_BASE = "https://www.redfin.com/stingray/do/location-autocomplete?location={}&v=2"

    name = "get_redfin_addresses"
    custom_settings = {
        "ITEM_PIPELINES" : {
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

    def parse_item(self, response):
        yield {
            "body": response.body
        }

    
class MergeRedfinGetAddressSpider(scrapy.Spider):
    name = "merge_get_redfin_addresses"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {},
        "ITEM_PIPELINES" : {
            "realestate_crawl.pipelines.MergeRedfinGetAddressesPipeline": 1,
        },
    }
    rows = []

    def start_requests(self, **kwargs):
        for f in self.settings["CSV_OUT_DIR"].iterdir():
            if not f.is_file() or not f.name.startswith("get_redfin_addresses"):
                continue
            yield scrapy.Request(f"file://{str(f.resolve())}")

    def parse(self, response):
        f = io.StringIO(response.text)
        csv_file = csv.DictReader(f)
        for line in csv_file:
            if line.get("ADDRESS") not in self.rows:
                self.rows.append(line)


class LoopnetGetAddressesSpider(scrapy.Spider):
    LOOK_UP_URL = "https://www.loopnet.com/services/geography/lookup/?includeSectionHeaders=true"
    SEARCH_URL = "https://www.loopnet.com/services/search"

    name = "get_loopnet_addresses"
    custom_settings = {
        "ITEM_PIPELINES" : {},
        "DOWNLOADER_MIDDLEWARES": {},
    }
    form_data = {
        # "pageguid":"22e46074-cc62-4dc0-b49b-13b192b880b3",
        "criteria":{
            "LNPropertyTypes":34,"LNIndustrialSubtypes":0,"LNRetailSubtypes":0,"LNShoppingCenterSubtypes":0,
            "LNMultiFamilySubtypes":0,"LNSpecialtySubtypes":0,"LNOfficeSubtypes":0,"LNHealthCareSubtypes":0,
            "LNHospitalitySubtypes":0,"LNSportsAndEntertainmentSubtypes":0,"LNLandSubtypes":0,"PropertyTypes":8,
            "HospitalitySubtypes":0,"IndustrialSubtypes":32,"LandTypes":0,"OfficeSubtypes":0,"GeneralRetailSubtypes":8386423,
            "FlexSubtypes":4,"SportsAndEntertainmentSubtypes":0,"SpecialtySubtypes":32,"MultifamilySubtypes":0,
            "HealthcareSubtypes":0,"ShoppingCenterTypes":0,"ApartmentStyleTypes":0,"Country":"US","State":"AL",
            "Market":None,"MSA":None,"County":None,"City":"Mobile","PostalCode":None,
            # "GeographyFilters":[{
            #     "ID":None,"BoundingBox":[-88.409866,30.524192,-87.9485468,30.844163],
            #     "Centroid":[-88.1792064,30.6841775],"Display":"Mobile","GeographyId":39866,
            #     "Code":"AL","GeographyType":2,"Radius":0,"RadiusLengthMeasure":0,"SubmarketPropertyType":0,"Address":None,"MatchType":3
            # }],
            "PageLocationLabel":"Mobile, AL","IncludeProximityCities":False,"AddressLine":None,"Distance":0,
            "Radius":None,"CoordinateBounds":None,"Polygon":None,"HasValidCoordinates":None,"BuildingClass":0,
            "BuildingSizeUom":"SquareFeet","LotSizeUom":"Acres",
            # "SubCategoryList":[802,803,804,806,808,8056,915,916,903,913,912,914,406,12120],
            "Editor":"Default","PreserveAddressForRadiusSavedSearch":False,"ListingSearchType":1,"OnMarketDateRange":None,
            "Keywords":None,"Sorting":[],"PropertyGroupId":None,"IsForSale":True,"PriceRangeMin":"3,500","PriceRangeMax":None,
            "BuildingSizeRangeMin":None,"BuildingSizeRangeMax":None,"PriceRangeCurrency":None,"PriceRangeRateType":"Total",
            "LotSizeRangeMin":None,"LotSizeRangeMax":None,"UnitCountRangeMin":None,"UnitCountRangeMax":None,"CapRateRangeMin":None,
            "CapRateRangeMax":None,"YearBuiltRangeMin":None,"YearBuiltRangeMax":None,"TermLengthRangeMin":None,
            "TermLengthRangeMax":None,"NetLeased":False,"InContract":True,"Distressed":False,"Auction":False,
            "IsTenXAuctions":False,"AuctionIds":None,"Single":False,"Multiple":False,"InvestmentTypeCore":False,
            "InvestmentTypeValueAdd":False,"InvestmentTypeOpportunistic":False,"InvestmentTypeTripleNet":False,
            "InvestmentTypeOpportunityZone":False,"BusinessForSale":True,"VacantOwner":True,"Investment":True,
            "InOpportunityZone":None,"CondosFilter":0,"PortfoliosFilter":0,"ShoppingCenterFilter":0,"BuildingParkFilter":0,
            "IsForLease":False,"LeaseRateRangeMin":None,"LeaseRateRangeMax":None,"SpaceAvailableRangeMin":None,
            "SpaceAvailableRangeMax":None,"LeaseRateTerm":None,"SpaceAvailableUom":None,"LeaseRateCurrency":None,
            "LeaseRatePerSizeUom":None,"SubLease":False,"RegionalMarket":None,"SubMarket":None,"MoveInDateIndicator":0,
            "MoveInDateEnteredType":None,"MoveInDateEnteredRangeMin":None,"MoveInDateEnteredRangeMax":None,"ListingId":None,
            "DateIndicator":0,"DateEnteredRangeMin":"01/01/0001","DateEnteredRangeMax":"01/01/0001","MinimumDate":"01/01/0001",
            "DateEnteredType":"RT","DateFormat":"MM/dd/yyyy","ViewMode":"None","ListingIdPinClick":None,"IsUserFromUS":False,
            "ForceRemoveBoundary":False,"AgentFirstName":None,"AgentLastName":None,"ResultLimit":500,"PageNumber":1,"PageSize":20,
            # "Timeout":0,"Origin":1, "StateKey":"00594511f4241f2a32351c8fd1f9c7c0"
        }
    }

    def __init__(self, city, state, **kwargs):
        self.city = city
        self.state = state
        self.filter = {
            "min": kwargs.get("min", "350k"),
            "max": kwargs.get("max", "2m"),
            "type": kwargs.get("t", "retail"),
            "need": kwargs.get("n", "For Sale"),
            "sold": kwargs.get("s", "3mo"),
            "year_built": kwargs.get("y", "1999"),
            "basement": kwargs.get("b", None),
            "waterfront": kwargs.get("w", "no"),
            "condos": kwargs.get("c", "no"),
            "min_cap_rate": kwargs.get("cmin"),
            "max_cap_rate": kwargs.get("cmax"),
            "min_size": kwargs.get("smin"),
            "max_size": kwargs.get("smax"),
        }
    
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
                "Address": None,"MatchType": address["MatchType"]
            }]
            self.form_data["GeographyFilters"] = GeographyFilters
            self.form_data["criteria"]["Country"] = address["Address"]["Country"]
            self.form_data["criteria"]["State"] = address["Address"]["State"]
            self.form_data["criteria"]["City"] = address["Address"]["City"]
            self.form_data["criteria"]["PageLocationLabel"] = address["Display"]
            yield scrapy.Request(
                self.SEARCH_URL, method="POST", body=json.dumps(self.form_data),
                headers={"content-type": "application/json"}, callback=self.parse_search
            )
        except Exception as e:
            self.logger.error(f"Error when parsing lookup: {e}")

    def parse_search(self, response):
        j_data = json.loads(response.text)
        self.logger.info(f"url: {j_data['UrlState']['Url']}")

    def parse_item(self, response):
        pass
