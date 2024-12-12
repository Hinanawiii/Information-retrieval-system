from elasticsearch import Elasticsearch
from pymongo import MongoClient
import logging
from datetime import datetime
import time
import os

class SearchEngine:
    def __init__(self, es_host='http://localhost:9201', mongo_host='mongodb://localhost:27017'):
        """
        初始化搜索引擎
        :param es_host: Elasticsearch服务器地址，需要包含协议、主机和端口
        :param mongo_host: MongoDB服务器地址
        """
        # 确保ES主机地址格式正确
        if not es_host.startswith(('http://', 'https://')):
            es_host = 'http://' + es_host

        try:
            self.es = Elasticsearch([es_host])
            self.mongo = MongoClient(mongo_host)
            self.db = self.mongo['nku_search']  # 或者使用您在 settings.py 中设置的 DB_NAME
            self.collection = self.db['nku_pages']  # 使用您在 pipeline 中定义的 collection_name
            
            # 检查ES连接
            if not self.es.ping():
                raise ConnectionError("无法连接到Elasticsearch服务器")
                
            # 检查MongoDB连接
            self.mongo.admin.command('ping')
            
        except Exception as e:
            logging.error(f"初始化连接失败: {str(e)}")
            raise
        
        # 配置日志
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'search_engine.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_index(self, index_name='nku_search'):
        """创建ES索引并设置mapping"""
        mapping = {
            "mappings": {
                "properties": {
                    "url": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "publish_time": {
                        "type": "date",
                        "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
                    },
                    "department": {
                        "type": "keyword"
                    },
                    "outlinks": {
                        "type": "keyword"
                    },
                    "anchor_texts": {
                        "type": "nested",
                        "properties": {
                            "url": {"type": "keyword"},
                            "text": {"type": "text", "analyzer": "ik_max_word"}
                        }
                    },
                    "snapshot_time": {
                        "type": "date",
                        "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
                    },
                    "content_type": {"type": "keyword"},
                    "pagerank_score": {"type": "float"}
                }
            },
            "settings": {
                "index": {
                    "number_of_shards": 5,
                    "number_of_replicas": 1,
                    "max_result_window": 10000
                }
            }
        }

        try:
            if self.es.indices.exists(index=index_name):
                self.logger.warning(f"索引 {index_name} 已存在！")
                return False

            self.es.indices.create(index=index_name, body=mapping)
            self.logger.info(f"成功创建索引: {index_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建索引失败: {str(e)}")
            return False

    def migrate_data(self, index_name='nku_search', batch_size=100):
        """从MongoDB迁移数据到Elasticsearch"""
        try:
            total_docs = self.collection.count_documents({})
            self.logger.info(f"开始迁移 {total_docs} 个文档")

            processed = 0
            batch = []
            start_time = time.time()
            
            for doc in self.collection.find():
                # 转换文档格式
                es_doc = {
                    'url': doc['url'],
                    'title': doc.get('title', ''),
                    'content': doc.get('content', ''),
                    'publish_time': doc.get('publish_time'),
                    'department': doc.get('department'),
                    'outlinks': doc.get('outlinks', []),
                    'content_type': doc.get('content_type', 'html'),
                    'snapshot_time': doc.get('snapshot_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                }
                
                # 转换anchor_texts
                if 'anchor_texts' in doc:
                    es_doc['anchor_texts'] = [
                        {'url': url, 'text': text}
                        for url, text in doc['anchor_texts'].items()
                    ]

                batch.append({
                    '_index': index_name,
                    '_id': doc['url'],
                    '_source': es_doc
                })
                
                if len(batch) >= batch_size:
                    self._bulk_index(batch)
                    processed += len(batch)
                    elapsed_time = time.time() - start_time
                    docs_per_second = processed / elapsed_time
                    self.logger.info(
                        f"已处理 {processed}/{total_docs} 文档 "
                        f"({(processed/total_docs*100):.2f}%) "
                        f"速度: {docs_per_second:.2f} 文档/秒"
                    )
                    batch = []
                    
            # 处理剩余的文档
            if batch:
                self._bulk_index(batch)
                processed += len(batch)
                
            total_time = time.time() - start_time
            self.logger.info(
                f"迁移完成。总计索引文档: {processed}，"
                f"耗时: {total_time:.2f}秒，"
                f"平均速度: {processed/total_time:.2f} 文档/秒"
            )
            
        except Exception as e:
            self.logger.error(f"迁移数据失败: {str(e)}")
            raise

    def _bulk_index(self, batch):
        """批量索引文档"""
        try:
            from elasticsearch.helpers import bulk
            success, failed = bulk(self.es, batch, stats_only=True)
            if failed:
                self.logger.warning(f"批量索引时有 {failed} 个文档失败")
        except Exception as e:
            self.logger.error(f"批量索引错误: {str(e)}")
            raise

    def update_document(self, doc_id, update_fields, index_name='nku_search'):
        """更新单个文档的特定字段"""
        try:
            self.es.update(
                index=index_name,
                id=doc_id,
                body={"doc": update_fields}
            )
            return True
        except Exception as e:
            self.logger.error(f"更新文档 {doc_id} 失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        try:
            self.mongo.close()
            self.logger.info("数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭数据库连接时出错: {str(e)}")

if __name__ == "__main__":
    try:
        # 使用示例
        engine = SearchEngine(
            es_host='http://localhost:9201',
            mongo_host='mongodb://localhost:27017'
        )
        
        # 创建索引
        if engine.create_index():
            # 迁移数据
            engine.migrate_data()
        
    except Exception as e:
        logging.error(f"程序执行出错: {str(e)}")
    finally:
        # 确保正确关闭连接
        if 'engine' in locals():
            engine.close()