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