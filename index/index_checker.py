from elasticsearch import Elasticsearch
from pymongo import MongoClient
import logging
from datetime import datetime

logging.basicConfig(
    filename=f'logs/sync_checker_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SyncChecker:
    def __init__(self):
        # 使用实际的连接参数
        self.mongo_client = MongoClient("mongodb://localhost:27017/")
        self.es_client = Elasticsearch(["http://localhost:9201"])
        self.mongo_db = self.mongo_client['nku_search']  # 你的MongoDB数据库名
        self.mongo_collection = self.mongo_db['nku_pages']    # 你的集合名
        self.es_index = 'nku_search'                    # ES索引名

    def check_document_counts(self):
        """检查文档数量是否匹配"""
        mongo_count = self.mongo_collection.count_documents({})
        es_count = self.es_client.count(index=self.es_index)['count']
        
        logging.info(f"MongoDB documents: {mongo_count}")
        logging.info(f"Elasticsearch documents: {es_count}")
        
        return mongo_count == es_count, mongo_count, es_count

    def find_missing_documents(self):
        """找出在ES中缺失的MongoDB文档"""
        missing_in_es = []
        mismatched_docs = []
        
        # 获取所有MongoDB文档
        mongo_docs = self.mongo_collection.find({}, {'url': 1, '_id': 1})
        
        for doc in mongo_docs:
            # 使用URL作为文档ID在ES中搜索
            try:
                es_exists = self.es_client.exists(
                    index=self.es_index,
                    id=doc['url']  # ES使用URL作为文档ID
                )
                
                if not es_exists:
                    missing_in_es.append(str(doc['_id']))
                    
            except Exception as e:
                logging.error(f"Error checking document {doc['url']}: {str(e)}")
                missing_in_es.append(str(doc['_id']))

        return missing_in_es, mismatched_docs

    def sync_missing_documents(self, missing_docs):
        """同步缺失的文档到ES"""
        for doc_id in missing_docs:
            try:
                # 从MongoDB获取完整文档
                mongo_doc = self.mongo_collection.find_one({'_id': doc_id})
                if mongo_doc:
                    # 准备ES文档
                    es_doc = {
                        'url': mongo_doc['url'],
                        'title': mongo_doc['title'],
                        'content': mongo_doc['content'],
                        'content_type': mongo_doc['content_type'],
                        'department': mongo_doc['department'],
                        'outlinks': mongo_doc.get('outlinks', []),
                        'snapshot_time': mongo_doc['snapshot_time'],
                        'publish_time': mongo_doc.get('publish_time'),
                        'pagerank_score': mongo_doc.get('pagerank_score', 1.0)
                    }
                    
                    # 添加到ES，使用URL作为文档ID
                    self.es_client.index(
                        index=self.es_index,
                        id=mongo_doc['url'],
                        body=es_doc
                    )
                    logging.info(f"Successfully synced document {doc_id}")
            except Exception as e:
                logging.error(f"Error syncing document {doc_id}: {str(e)}")

    def update_pagerank_scores(self):
        """在MongoDB中更新或添加pagerank字段"""
        try:
            # 为没有pagerank_score字段的文档添加初始值
            result = self.mongo_collection.update_many(
                {"pagerank_score": {"$exists": False}},
                {"$set": {"pagerank_score": 1.0}}
            )
            logging.info(f"Added pagerank_score field to {result.modified_count} documents")
            return result.modified_count
        except Exception as e:
            logging.error(f"Error adding pagerank_score field: {str(e)}")
            return 0

    def verify_field_mapping(self):
        """验证字段映射是否正确"""
        try:
            # 获取ES的映射信息
            mapping = self.es_client.indices.get_mapping(index=self.es_index)
            logging.info("Current ES mapping:")
            logging.info(mapping)
            
            # 获取一个MongoDB文档作为样本
            sample_doc = self.mongo_collection.find_one()
            if sample_doc:
                logging.info("Sample MongoDB document fields:")
                logging.info(list(sample_doc.keys()))
                
        except Exception as e:
            logging.error(f"Error verifying field mapping: {str(e)}")

if __name__ == "__main__":
    checker = SyncChecker()
    
    # 验证字段映射
    checker.verify_field_mapping()
    
    # 检查文档数量
    counts_match, mongo_count, es_count = checker.check_document_counts()
    if not counts_match:
        logging.warning(f"Document counts don't match! MongoDB: {mongo_count}, ES: {es_count}")
    
    # 查找缺失文档
    missing_docs, mismatched = checker.find_missing_documents()
    if missing_docs:
        logging.warning(f"Found {len(missing_docs)} documents missing in Elasticsearch")
        user_input = input(f"Do you want to sync {len(missing_docs)} missing documents to ES? (y/n): ")
        if user_input.lower() == 'y':
            checker.sync_missing_documents(missing_docs)
    
    if mismatched:
        logging.warning(f"Found {len(mismatched)} documents with multiple matches in ES")
    
    # 更新PageRank分数
    updated_count = checker.update_pagerank_scores()
    logging.info(f"Updated pagerank scores for {updated_count} documents")