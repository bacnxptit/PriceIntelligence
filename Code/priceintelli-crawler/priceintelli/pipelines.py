import logging
import os
from datetime import datetime, timezone
from itemadapter import ItemAdapter

try:
    import pymongo
except ImportError:
    pymongo = None


class MongoPipeline:
    def open_spider(self, spider):
        self.mongo_uri = getattr(
            spider,
            "mongo_uri",
            os.getenv(
                "MONGODB_URI",
                os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
            ),
        )
        self.mongo_db = getattr(
            spider,
            "mongo_db",
            os.getenv("MONGODB_DB", "imdb"),
        )
        # Dynamic collection name: e.g. iphone_fptshop or raw_prices
        default_col = getattr(spider, "collection_name", f"iphone_{spider.name}")
        self.collection_name = os.getenv("MONGO_COLLECTION", default_col)

        if pymongo is not None and self.mongo_uri:
            try:
                self.client = pymongo.MongoClient(self.mongo_uri, serverSelectionTimeoutMS=10000)
                self.db = self.client[self.mongo_db]
                logging.info(f"MongoDB connected for spider {spider.name} -> {self.mongo_db}.{self.collection_name}")
            except Exception as exc:
                logging.warning(f"MongoDB connection failed for {spider.name}: {exc}")
                self.client = None
                self.db = None
        else:
            self.client = None
            self.db = None

    def close_spider(self, spider):
        if hasattr(self, "client") and self.client is not None:
            self.client.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        data = dict(adapter.asdict())
        # Ensure crawled_at exists
        if "crawled_at" not in data or not data["crawled_at"]:
            data["crawled_at"] = datetime.now(timezone.utc)

        if hasattr(self, "db") and self.db is not None:
            try:
                col = getattr(spider, "collection_name", f"iphone_{spider.name}")
                self.db[col].insert_one(data)
            except Exception as exc:
                logging.warning(f"MongoDB insert failed for {spider.name}: {exc}")
        return item
