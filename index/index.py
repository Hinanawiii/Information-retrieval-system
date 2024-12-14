from elasticsearch import Elasticsearch
from pymongo import MongoClient
import logging
from datetime import datetime
import time
import os
import json
import hashlib

class SearchEngine:
    def __init__(self, es_host='http://localhost:9201', mongo_host='mongodb://localhost:27017'):
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

        try:
            if not es_host.startswith(('http://', 'https://')):
                es_host = 'http://' + es_host

            self.es = Elasticsearch([es_host])
            self.mongo = MongoClient(mongo_host)
            self.db = self.mongo['nku_search']
            self.collection = self.db['nku_pages']
            
            if not self.es.ping():
                raise ConnectionError("无法连接到Elasticsearch服务器")
            self.mongo.admin.command('ping')
            
        except Exception as e:
            self.logger.error(f"初始化连接失败: {str(e)}")
            raise

    def get_doc_id(self, url):
        """使用URL的MD5哈希作为文档ID"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

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
                    "department": {"type": "keyword"},
                    "outlinks": {"type": "keyword"},
                    "anchor_texts": {
                        "type": "nested",
                        "properties": {
                            "url": {"type": "keyword"},
                            "text": {"type": "text", "analyzer": "ik_max_word"}
                        }
                    },
                    "content_type": {"type": "keyword"},
                    "pagerank_score": {"type": "float"}
                }
            },
            "settings": {
                "index": {
                    "number_of_shards": 1,  # 减少分片数提高性能
                    "number_of_replicas": 1,
                    "refresh_interval": "30s",  # 延长刷新间隔提高索引性能
                    "max_result_window": 10000
                }
            }
        }

        try:
            # 如果索引存在，先删除
            if self.es.indices.exists(index=index_name):
                self.logger.warning(f"索引 {index_name} 已存在，正在删除...")
                self.es.indices.delete(index=index_name)
            
            self.es.indices.create(index=index_name, body=mapping)
            self.logger.info(f"成功创建索引: {index_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建索引失败: {str(e)}")
            return False

    def migrate_data(self, index_name='nku_search', batch_size=500):
        """从MongoDB迁移数据到Elasticsearch"""
        try:
            total_docs = self.collection.count_documents({})
            self.logger.info(f"开始迁移 {total_docs} 个文档")

            # 先打印一个示例文档
            sample_doc = self.collection.find_one()
            if sample_doc:
                self.logger.info("MongoDB文档示例：")
                self.print_document_sample(sample_doc)
            
            processed = 0
            success_count = 0
            failed_docs = []
            batch = []
            start_time = time.time()
            
            for doc in self.collection.find():
                try:
                    # 使用MD5哈希作为文档ID
                    doc_id = self.get_doc_id(doc['url'])
                    
                    # 类型检查和转换
                    outlinks = doc.get('outlinks', [])
                    if not isinstance(outlinks, list):
                        self.logger.warning(f"文档 {doc['url']} 的 outlinks 不是列表类型，而是 {type(outlinks)}，将设置为空列表")
                        outlinks = []
                    
                    # 转换文档格式
                    es_doc = {
                        'url': doc['url'],
                        'title': str(doc.get('title', '')),
                        'content': str(doc.get('content', '')),
                        'department': str(doc.get('department', '')),
                        'outlinks': outlinks,
                        'content_type': str(doc.get('content_type', 'text/html')),
                        'pagerank_score': float(doc.get('pagerank_score', 1.0))
                    }
                    
                    # 转换anchor_texts
                    if 'anchor_texts' in doc and isinstance(doc['anchor_texts'], dict):
                        es_doc['anchor_texts'] = [
                            {'url': str(url), 'text': str(text)}
                            for url, text in doc['anchor_texts'].items()
                        ]
                    else:
                        es_doc['anchor_texts'] = []

                    # 对于第一个文档，打印转换后的格式
                    if processed == 0:
                        self.logger.info("转换后的ES文档示例：")
                        self.logger.info(json.dumps(es_doc, ensure_ascii=False, indent=2)[:500])

                    batch.append({
                        '_index': index_name,
                        '_id': doc_id,
                        '_source': es_doc
                    })
                    
                    if len(batch) >= batch_size:
                        batch_success, batch_failed = self._bulk_index(batch)
                        success_count += batch_success
                        processed += len(batch)
                        
                        elapsed_time = time.time() - start_time
                        docs_per_second = processed / elapsed_time
                        self.logger.info(
                            f"已处理 {processed}/{total_docs} 文档 "
                            f"({(processed/total_docs*100):.2f}%) "
                            f"成功: {success_count} "
                            f"速度: {docs_per_second:.2f} 文档/秒"
                        )
                        batch = []
                
                except Exception as e:
                    self.logger.error(f"处理文档时出错 {doc.get('url', 'Unknown URL')}: {str(e)}")
                    self.logger.error(f"文档内容: {json.dumps(doc, ensure_ascii=False)[:500]}...")
                    failed_docs.append(doc.get('url', 'Unknown URL'))
                    continue
                    
            # 处理剩余的文档
            if batch:
                batch_success, batch_failed = self._bulk_index(batch)
                success_count += batch_success
                processed += len(batch)
                
            total_time = time.time() - start_time
            self.logger.info(
                f"迁移完成。成功索引文档: {success_count}，"
                f"失败文档: {len(failed_docs)}，"
                f"耗时: {total_time:.2f}秒，"
                f"平均速度: {processed/total_time:.2f} 文档/秒"
            )
            
            # 记录失败的文档
            if failed_docs:
                failed_file = os.path.join('logs', f'failed_updates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
                with open(failed_file, 'w', encoding='utf-8') as f:
                    for url in failed_docs:
                        f.write(f"{url}\n")
                self.logger.warning(f"失败的文档URL已记录到: {failed_file}")
            
            return success_count, len(failed_docs)
            
        except Exception as e:
            self.logger.error(f"迁移数据失败: {str(e)}")
            raise

    def print_document_sample(self, doc):
        """打印文档示例，用于调试"""
        try:
            sample = {
                'url': doc.get('url', ''),
                'title': str(doc.get('title', ''))[:50],  # 只取前50个字符
                'content_type': doc.get('content_type', ''),
                'department': doc.get('department', ''),
                'outlinks_count': len(doc.get('outlinks', [])),
                'anchor_texts_count': len(doc.get('anchor_texts', {})),
                'publish_time': doc.get('publish_time', ''),
                'snapshot_time': doc.get('snapshot_time', '')
            }
            self.logger.info(f"文档示例:\n{json.dumps(sample, ensure_ascii=False, indent=2)}")
        except Exception as e:
            self.logger.error(f"打印文档示例时出错: {str(e)}")

    def _bulk_index(self, batch):
        """批量索引文档，返回成功和失败的计数，并记录详细错误信息"""
        try:
            # 使用 bulk API 的原始响应而不是 helpers.bulk
            body = []
            for item in batch:
                body.append(json.dumps({"index": {"_index": item["_index"], "_id": item["_id"]}}))
                body.append(json.dumps(item["_source"]))
            
            body = "\n".join(body) + "\n"
            response = self.es.bulk(body=body)
            
            # 分析响应中的错误
            success_count = 0
            failed_items = []
            
            if response["errors"]:
                for i, item in enumerate(response["items"]):
                    if "error" in item["index"]:
                        error_info = item["index"]["error"]
                        error_type = error_info.get("type", "unknown")
                        error_reason = error_info.get("reason", "unknown")
                        doc_id = item["index"]["_id"]
                        
                        # 找到对应的源文档
                        source_doc = batch[i]["_source"]
                        
                        # 记录详细错误信息
                        self.logger.error(
                            f"文档索引失败:\n"
                            f"文档ID: {doc_id}\n"
                            f"URL: {source_doc.get('url', 'unknown')}\n"
                            f"错误类型: {error_type}\n"
                            f"错误原因: {error_reason}\n"
                            f"文档内容片段: {str(source_doc)[:200]}..."
                        )
                        failed_items.append(i)
                    else:
                        success_count += 1
                
                self.logger.warning(f"批量索引完成：成功 {success_count} 个，失败 {len(failed_items)} 个")
            else:
                success_count = len(batch)
                
            return success_count, len(failed_items)
            
        except Exception as e:
            self.logger.error(f"批量索引发生异常: {str(e)}\n"
                            f"第一个文档示例: {json.dumps(batch[0]['_source'], ensure_ascii=False)[:200]}...")
            return 0, len(batch)

    def close(self):
        """关闭数据库连接"""
        try:
            self.mongo.close()
            self.logger.info("数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭数据库连接时出错: {str(e)}")

if __name__ == "__main__":
    try:
        engine = SearchEngine(
            es_host='http://localhost:9201',
            mongo_host='mongodb://localhost:27017'
        )
        
        # 创建索引（会先删除已存在的索引）
        if engine.create_index():
            # 迁移数据
            success, failed = engine.migrate_data(batch_size=500)
            print(f"迁移完成：成功 {success} 文档，失败 {failed} 文档")
        
    except Exception as e:
        logging.error(f"程序执行出错: {str(e)}")
    finally:
        if 'engine' in locals():
            engine.close()