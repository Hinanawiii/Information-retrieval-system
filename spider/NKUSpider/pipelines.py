# -*- coding: utf-8 -*-
import pymongo
from itemadapter import ItemAdapter

class MongoPipeline:
    collection_name = 'nku_pages'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=f'mongodb://{crawler.settings["LOCAL_MONGO_HOST"]}:{crawler.settings["LOCAL_MONGO_PORT"]}',
            mongo_db=crawler.settings['DB_NAME']
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        # 创建URL索引以加快查重速度
        self.db[self.collection_name].create_index('url', unique=True)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        try:
            self.db[self.collection_name].insert_one(adapter.asdict())
        except pymongo.errors.DuplicateKeyError:
            spider.logger.debug(f"重复URL: {adapter['url']}")
        except Exception as e:
            spider.logger.error(f"MongoDB插入错误: {str(e)}")
        return item