from elasticsearch import Elasticsearch
from pymongo import MongoClient
import logging
from datetime import datetime

logging.basicConfig(
    filename=f'logs/index_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class IndexCleanup:
    def __init__(self):
        self.mongo_client = MongoClient("mongodb://localhost:27017/")
        self.es_client = Elasticsearch(["http://localhost:9201"])
        self.mongo_db = self.mongo_client['nku_search']
        self.mongo_collection = self.mongo_db['nku_pages']
        self.es_index = 'nku_search'

    def cleanup_elasticsearch(self):
        """清理ES中的重复文档"""
        try:
            # 获取所有文档
            result = self.es_client.search(
                index=self.es_index,
                body={
                    "size": 10000,
                    "_source": ["url"],
                    "query": {"match_all": {}}
                }
            )

            # 收集URL和文档ID
            url_docs = {}
            for hit in result['hits']['hits']:
                url = hit['_source']['url']
                if url in url_docs:
                    # 删除重复的文档
                    self.es_client.delete(
                        index=self.es_index,
                        id=hit['_id']
                    )
                    logging.info(f"Deleted duplicate document with ID: {hit['_id']}")
                else:
                    url_docs[url] = hit['_id']
            
            return len(url_docs)
        except Exception as e:
            logging.error(f"Error in cleanup_elasticsearch: {str(e)}")
            return 0

    def merge_pagerank_fields(self):
        """合并MongoDB中的pagerank和pagerank_score字段"""
        try:
            # 查找同时具有pagerank和pagerank_score字段的文档
            docs = self.mongo_collection.find({
                "pagerank": {"$exists": True},
                "pagerank_score": {"$exists": True}
            })

            updated = 0
            for doc in docs:
                # 使用pagerank字段的值更新pagerank_score
                self.mongo_collection.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {"pagerank_score": doc["pagerank"]},
                        "$unset": {"pagerank": ""}
                    }
                )
                updated += 1

            logging.info(f"Merged {updated} pagerank fields")
            return updated
        except Exception as e:
            logging.error(f"Error in merge_pagerank_fields: {str(e)}")
            return 0

    def sync_pagerank_to_es(self):
        """将MongoDB中的pagerank_score同步到ES"""
        try:
            docs = self.mongo_collection.find({}, {"url": 1, "pagerank_score": 1})
            updated = 0

            for doc in docs:
                if "pagerank_score" in doc:
                    try:
                        self.es_client.update(
                            index=self.es_index,
                            id=doc["url"],
                            body={
                                "doc": {
                                    "pagerank_score": doc["pagerank_score"]
                                }
                            }
                        )
                        updated += 1
                    except Exception as e:
                        logging.warning(f"Failed to update document {doc['url']}: {str(e)}")

            logging.info(f"Updated {updated} documents with pagerank scores in ES")
            return updated
        except Exception as e:
            logging.error(f"Error in sync_pagerank_to_es: {str(e)}")
            return 0

    def verify_counts(self):
        """验证文档计数"""
        mongo_count = self.mongo_collection.count_documents({})
        es_count = self.es_client.count(index=self.es_index)['count']
        return mongo_count, es_count

if __name__ == "__main__":
    cleanup = IndexCleanup()
    
    # 1. 清理ES中的重复文档
    print("Cleaning up duplicate documents in Elasticsearch...")
    unique_docs = cleanup.cleanup_elasticsearch()
    print(f"Found {unique_docs} unique documents")

    # 2. 合并MongoDB中的pagerank字段
    print("\nMerging pagerank fields in MongoDB...")
    merged = cleanup.merge_pagerank_fields()
    print(f"Merged {merged} pagerank fields")

    # 3. 同步pagerank scores到ES
    print("\nSyncing pagerank scores to Elasticsearch...")
    updated = cleanup.sync_pagerank_to_es()
    print(f"Updated {updated} documents in Elasticsearch")

    # 4. 验证最终计数
    mongo_count, es_count = cleanup.verify_counts()
    print(f"\nFinal document counts:")
    print(f"MongoDB: {mongo_count}")
    print(f"Elasticsearch: {es_count}")