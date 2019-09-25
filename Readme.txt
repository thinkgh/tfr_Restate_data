You should have a folder with structure:
Project
|___images
|
|_addresses.csv
|_requirements.txt
|_william_spider.py
|_Readme.txt

Follow the steps bellow to install requirements:
1. Make sure you have python 3.6 or above installed
2. Create a virtual enviroment by running command "python3 -m venv scrapyenv"
3. Activate enviroment by running command "source scrapyenv/bin/activate"
4. Install all requirements by running command "pip install -r requirements.txt"

Follow the steps bellow to run:
1. Activate enviroment by running command "source scrapyenv/bin/activate" (Skip if followed no. 3 of requirements)
2. Run spider using "scrapy crawl william_demo_spider -o details.csv"
