import os
import logging

import pymongo
from itemadapter import ItemAdapter


class ViettelstorePipeline:
    collection_name = "iphone_viettelstore"

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(
            os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        )
        self.db = self.client["imdb"]

    def close_spider(self, spider):
        if hasattr(self, "client"):
            self.client.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        try:
            if hasattr(self, "db") and self.db is not None:
                self.db[self.collection_name].insert_one(dict(adapter.asdict()))
        except Exception as exc:
            logging.warning("MongoDB save failed for %s: %s", spider.name, exc)
        return item