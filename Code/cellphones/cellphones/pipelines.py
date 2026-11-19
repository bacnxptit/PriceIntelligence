import os
import logging
from itemadapter import ItemAdapter

try:
    import pymongo
except ImportError:
    pymongo = None


class CellphonesPipeline:
    collection_name = "iphone_cellphones"

    def open_spider(self, spider):
        self.mongo_uri = getattr(
            spider,
            "mongo_uri",
            os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
        )
        self.mongo_db = getattr(spider, "mongo_db", "imdb")

        if pymongo is not None and self.mongo_uri:
            try:
                self.client = pymongo.MongoClient(self.mongo_uri)
                self.db = self.client[self.mongo_db]
                logging.info("Connected to MongoDB for CellphonesPipeline")
            except Exception as exc:
                logging.warning("MongoDB connection could not be established: %s", exc)
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
        try:
            if hasattr(self, "db") and self.db is not None:
                self.db[self.collection_name].insert_one(dict(adapter.asdict()))
        except Exception as exc:
            logging.warning("MongoDB save failed for %s: %s", spider.name, exc)
        return item
