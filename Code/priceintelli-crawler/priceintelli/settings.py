import os

BOT_NAME = "priceintelli"

SPIDER_MODULES = ["priceintelli.spiders"]
NEWSPIDER_MODULE = "priceintelli.spiders"

ROBOTSTXT_OBEY = False

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

CONCURRENT_REQUESTS = 16
DOWNLOAD_TIMEOUT = 15

ITEM_PIPELINES = {
    "priceintelli.pipelines.MongoPipeline": 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# ============================================================
# SCRAPEOPS MONITORING INTEGRATION
# ============================================================
SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")

if SCRAPEOPS_API_KEY and SCRAPEOPS_API_KEY != "YOUR_API_KEY":
    EXTENSIONS = {
        "scrapeops_scrapy.extension.ScrapeOpsMonitor": 500,
    }
    DOWNLOADER_MIDDLEWARES = {
        "scrapeops_scrapy.middleware.retry.RetryMiddleware": 550,
        "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    }
