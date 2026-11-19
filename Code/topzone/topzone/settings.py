# Scrapy settings for topzone project

BOT_NAME = "topzone"

SPIDER_MODULES = ["topzone.spiders"]
NEWSPIDER_MODULE = "topzone.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure concurrency and throttling
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 1.0

# Configure headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

# Configure item pipelines
ITEM_PIPELINES = {
    "topzone.pipelines.TopzonePipeline": 300,
}

# UTF-8 feed encoding for JSON/CSV outputs
FEED_EXPORT_ENCODING = "utf-8"
