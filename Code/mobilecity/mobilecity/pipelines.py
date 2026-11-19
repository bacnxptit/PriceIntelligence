# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo
import logging
from itemadapter import ItemAdapter


class MobilecityPipeline:
    collection_name = "iphone_mobilecity"
    
    def open_spider(self, spider):
            self.client = pymongo.MongoClient(
                "mongodb+srv://nguyenxuanbac28092005_db_user:zFZRzSH61TZ0kSxT@cluster0.ceq4y3n.mongodb.net/?appName=Cluster0"
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