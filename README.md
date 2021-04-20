# Scrape data, images from realtor.com, redfin.com, zillow.com

## Usage

Command for running crawlers: `scrapy crawl <crawler_name> -a input_file=<input_file> [-a images=] [-a delimiter=] [-a field1=] [-a field2=] [-a field3=] [-a field4=] [-a field5=]`

Params:

- `crawler_name`: this is name of crawler, one of these value: `realtor`, `redfin`, `zillow`
- `input_file`: this is path to csv file.   
- `images`: if you need to get images, set it to `true`, else skip it
- `delimiter`, `field1`, `field2`, `field3`, .. : These are delimiter and headers of input file.

By default:
- The header is: `locationId;Address`
- Delimiter is: `;`

If input file has same delimiter and headers (case sensitive), then skip params `delimiter`, `field1`, `field2`, `field3`, .. 

The params in `<` and `>` are required values. The params in `[` and `]` are optional values, we can skip it.

Example:
- scrapy crawl realtor -a input_file=input_csv/huy_example.csv
- scrapy crawl realtor -a input_file=input_csv/huy_example.csv -a images=true


Command for downloading images: `scrapy crawl download_images -a folder_name=<folder_name>`

Params:

- `folder_name`: This is folder name under `output/images_links`

Example:
- scrapy crawl download_images -a folder_name=huy_example.csv

## Output

The output include file csv contains data, image links (if we set `images=true`), and real images (if we run crawler `download_images`) 

### CSV output

The csv files are exported in folder `output/csv/`. 

The name of file are formatted: `<crawler_name> YYYY-MM-DD hh:mm:ss.csv`

- Fields for realtor: `Location id,url,Price,Beds,Baths,Rooms,House size,Stories,Lot size,Garage,Heating,Cooling,Year built,Year renovated,Property type,Style,Date updated,Fireplace,Flood factor`

### Images links output

The image links are saved in folder `output/images/<input_file_name>/`

### Images output

When running downloader, the images are saved in folder `output/images/<folder_name>/<location_id>`

# Get addresses from redfin, loopnet

## Usage

Command for running crawlers: `scrapy crawl <crawler_name> -a city=<city> -a state=<state> [-a ...]`

Params:

- `crawler_name`: this is name of crawler, one of these values: `get_redfin_addresses`, `get_loopnet_addresses`
- `city`, `state`: this is city, state. These are required params

Additional params: (If we don't add these params, if will get the default value)

- For redfin:
    - `min`: this is min price, accepts values in formatted like this: `200k`, `350k`, `2m` , `3m` ,... Default value is `350k`
    - `max`: this is max price, accepts values in formatted like min price. Defaul value is `2m`
    - `t`: this is property type, accepted values: `house`, `condo`, `townhouse`, `multifamily`, `land`, `other`. default is `house`. We can do a combination with many values, example: `house+condo`, `house+condo+townhouse`
    - `s`: this is last sold, acceped values: `1wk`, `1mo`, `3mo`, `6mo`, `1yr`, `2yr`, `3yr`, `4yr`, `5yr`. Default value is `3mo` 
    - `y`: this is max value of year built. Default is `1999`
    - `b`: this is basement, accepted values: `finished`, `unfinished`. Default is `finished`
    - `w`: this is for checkbox Waterfront Only. Accepted values: `yes`, `no`. Default is `no`
    - `p`: this is for checkbox Must Have Pool. Accepted values: `yes`, `no`. Default is `no`

- For loopnet:
    - `min`: min price, accepts values in formatted like this: `350000`, `2000000`,.. Default is `null`
    - `max`: min price, accepts values in formatted like this: `350000`, `2000000`,.. Default is `null`
    - `t`: this is property type, accepted values: `All`, `Office`, `Industrial`, `Retail`, `Restaurant`, `Shopping Center`, `Multifamily`, `Specialty`, `Health Care`, `Hospitality`, `Sports & Entertainment`, `Land`, `Residential Income`
    - `ymin`: this min of year built, default is `null`
    - `ymax`: this max of year built, default is `null`
    - `cmin`: this min of cap rate, accepted values: `20`, `40`,.. default is `null`
    - `cmax`: this max of cap rate, accepted values: `20`, `40`,.. default is `null`
    - `smin`: this min of Building Size (unit in square foot), accepted values: `45000`, `456000`,.. default is `null`
    - `smax`: this max of Building Size (unit in square foot), accepted values: `45000`, `456000`,.. default is `null`
    - `c`: this is Condos, accepted values: `include`, `only`, `exclude`. Default is `include`

Some sample commands:
- `scrapy crawl get_redfin_addresses -a city=Birmingham -a state=Al`
- `scrapy crawl get_loopnet_addresses -a city=mobile -a state=AL`
- `scrapy crawl get_loopnet_addresses -a city=mobile -a state=AL -a t=Retail -a min=350000 -a max=1000000`

## Output

The output files are csv, under forder `output/csv/` and are named by `<crawler_name> YYYY-MM-DD hh:mm:ss.csv`

# Search images and data from [norfolkair](https://air.norfolk.gov/) based on an address

## Usage

Command: `scrapy crawl norfolkair -a address=<address>`

Some sample commands:
- `scrapy crawl norfolkair -a address='Leicester Ave'`

## Output

The output files are csv, under forder `output/csv/` and are named by `norfolkair YYYY-MM-DD hh:mm:ss.csv`

## Additional infomation

- By default, scripts use proxy. But some script works well without proxy (example: `get_redfin_addresses`, `get_loopnet_addresses`). So if we want to disable proxy, set env variable `PROXY` to `false` : `export PROXY=false`
- Set env variable `LOG_LEVEL` to `DEBUG` for showing more info during script's running: `export LOG_LEVEL=DEBUG`
 