from elasticsearch import Elasticsearch
from pymongo import MongoClient
import logging
from datetime import datetime
import os

class IndexChecker:
    def __init__(self, es_host='http://localhost:9201', mongo_host='mongodb://localhost:27017'):
        self.es = Elasticsearch([es_host])
        self.mongo = MongoClient(mongo_host)
        self.db = self.mongo['nku_search']
        self.collection = self.db['nku_pages']
        
        # 创建logs目录
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 配置日志记录
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'index_checker.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def check_stats(self, index_name='nku_search'):
        """检查索引状态"""
        try:
            # 检查索引是否存在
            if not self.es.indices.exists(index=index_name):
                self.logger.error(f"索引 {index_name} 不存在！")
                return

            # 获取索引统计信息
            stats = self.es.indices.stats(index=index_name)
            docs_count = stats['_all']['total']['docs']['count']
            store_size = stats['_all']['total']['store']['size_in_bytes'] / 1024 / 1024  # 转换为MB

            # 获取 MongoDB 文档数量
            mongo_count = self.collection.count_documents({})

            self.logger.info(f"Elasticsearch 索引统计:")
            self.logger.info(f"文档数量: {docs_count}")
            self.logger.info(f"索引大小: {store_size:.2f} MB")
            self.logger.info(f"\nMongoDB 统计:")
            self.logger.info(f"文档数量: {mongo_count}")

            # 检查映射
            mapping = self.es.indices.get_mapping(index=index_name)
            self.logger.info(f"\n索引映射:")
            self.logger.info(mapping)

        except Exception as e:
            self.logger.error(f"检查状态时出错: {str(e)}")

    def update_index(self, index_name='nku_search', batch_size=50):
        """增量更新索引
        只索引MongoDB中比Elasticsearch最新文档更新的文档
        """
        try:
            # 获取ES中最新文档的时间
            last_doc = self.es.search(
                index=index_name,
                body={
                    "sort": [{"snapshot_time": {"order": "desc"}}],
                    "size": 1
                }
            )
            
            if last_doc['hits']['hits']:
                last_time = last_doc['hits']['hits'][0]['_source']['snapshot_time']
                # 查找更新的文档
                query = {"snapshot_time": {"$gt": last_time}}
            else:
                query = {}  # 如果ES为空，则索引所有文档

            # 获取需要更新的文档数量
            total_docs = self.collection.count_documents(query)
            if total_docs == 0:
                self.logger.info("没有新文档需要索引")
                return 0, 0

            self.logger.info(f"发现 {total_docs} 个新文档需要索引")

            # 初始化计数器和失败文档列表
            processed = 0
            failed_docs = []
            batch = []
            
            # 批量处理新文档
            for doc in self.collection.find(query):
                es_doc = {
                    '_index': index_name,
                    '_id': doc['url'],
                    '_source': {
                        'url': doc['url'],
                        'title': str(doc.get('title', '')).strip(),
                        'content': str(doc.get('content', '')).strip(),
                        'content_type': doc.get('content_type', 'html'),
                        'department': doc.get('department', ''),
                        'outlinks': doc.get('outlinks', []),
                        'snapshot_time': doc.get('snapshot_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    }
                }

                batch.append(es_doc)
                if len(batch) >= batch_size:
                    success, failures = self._bulk_index(batch)
                    processed += success
                    failed_docs.extend(failures)
                    self.logger.info(
                        f"处理进度: {processed}/{total_docs} "
                        f"({(processed/total_docs*100):.2f}%)"
                    )
                    batch = []

            # 处理剩余的文档
            if batch:
                success, failures = self._bulk_index(batch)
                processed += success
                failed_docs.extend(failures)

            # 记录最终结果
            self.logger.info(
                f"增量更新完成。成功: {processed} 个文档，"
                f"失败: {len(failed_docs)} 个文档"
            )

            # 如果有失败的文档，保存到单独的日志文件
            if failed_docs:
                log_dir = 'logs'
                failed_log_path = os.path.join(
                    log_dir, 
                    f'failed_updates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                )
                with open(failed_log_path, 'w', encoding='utf-8') as f:
                    for doc in failed_docs:
                        f.write(f"文档ID: {doc['id']}, 错误原因: {doc['error']}\n")
                self.logger.info(f"失败文档详情已保存到: {failed_log_path}")

            return processed, len(failed_docs)

        except Exception as e:
            self.logger.error(f"更新索引时出错: {str(e)}")
            return 0, 0

    def _bulk_index(self, batch):
        """批量索引文档，记录失败的文档并继续处理"""
        try:
            from elasticsearch.helpers import bulk
            
            # 使用不抛出异常的模式进行批量索引
            success, errors = bulk(
                self.es,
                batch,
                raise_on_error=False,      # 不抛出异常
                raise_on_exception=False,   # 不因连接问题等异常停止
                stats_only=False           # 返回详细错误信息
            )
            
            # 处理失败的文档
            failed_docs = []
            if errors:
                for error in errors:
                    doc_id = error.get('index', {}).get('_id')
                    error_reason = error.get('index', {}).get('error', {}).get('reason', 'Unknown error')
                    failed_docs.append({
                        'id': doc_id,
                        'error': error_reason
                    })
                    
                self.logger.warning(f"本批次中 {len(failed_docs)} 个文档索引失败")
                for doc in failed_docs:
                    self.logger.warning(f"文档 ID: {doc['id']}, 错误原因: {doc['error']}")
            
            # 返回成功数量和失败文档列表
            return len(batch) - len(failed_docs), failed_docs
            
        except Exception as e:
            self.logger.error(f"批量索引过程发生错误: {str(e)}")
            # 出现异常时，将整个批次标记为失败
            failed_docs = [{
                'id': doc['_id'],
                'error': str(e)
            } for doc in batch]
            return 0, failed_docs

    def close(self):
        """关闭连接"""
        try:
            self.mongo.close()
            self.logger.info("数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭数据库连接时出错: {str(e)}")

if __name__ == "__main__":
    checker = IndexChecker()
    try:
        # 检查当前状态
        checker.check_stats()
        
        # 更新索引
        processed, failed = checker.update_index()
        print(f"索引更新完成：成功 {processed} 个文档，失败 {failed} 个文档")
    finally:
        checker.close()