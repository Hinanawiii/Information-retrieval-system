from pymongo import MongoClient, UpdateOne
import networkx as nx
from typing import Dict
import logging
from graph import GraphBuilder
from tqdm import tqdm

class PageRankCalculator:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        """
        初始化PageRank计算器
        
        Args:
            mongo_uri: MongoDB连接URI
        """
        self.client = MongoClient(mongo_uri)
        self.db = self.client['nku_search']
        self.collection = self.db['nku_pages']
        
        # 配置日志
        import os
        
        # 确保日志目录存在
        os.makedirs('logs', exist_ok=True)
        
        # 初始化logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # 添加文件处理器
        file_handler = logging.FileHandler('logs/pagerank.log')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        self.logger = logging.getLogger(__name__)

    def calculate_pagerank(self, damping_factor: float = 0.85, max_iterations: int = 100, 
                         tolerance: float = 1.0e-6) -> Dict[str, float]:
        """
        计算PageRank值
        
        Args:
            damping_factor: 阻尼系数，通常为0.85
            max_iterations: 最大迭代次数
            tolerance: 收敛阈值
            
        Returns:
            包含每个页面ID和对应PageRank值的字典
        """
        try:
            # 构建图
            graph_builder = GraphBuilder()
            graph = graph_builder.build_graph()
            
            # 使用NetworkX计算PageRank
            pagerank_scores = nx.pagerank(
                graph,
                alpha=damping_factor,
                max_iter=max_iterations,
                tol=tolerance
            )
            
            self.logger.info("PageRank calculation completed successfully")
            return pagerank_scores
            
        except Exception as e:
            self.logger.error(f"Error calculating PageRank: {str(e)}")
            raise

    def update_mongodb(self, pagerank_scores: Dict[str, float], batch_size: int = 500):
        """
        更新MongoDB中的PageRank值
        
        Args:
            pagerank_scores: PageRank计算结果
            batch_size: 批量更新的大小
        """
        try:
            updates = []
            for doc_id, score in pagerank_scores.items():
                # 将字符串ID转换为ObjectId
                from bson.objectid import ObjectId
                update = UpdateOne(
                    {'_id': ObjectId(doc_id)},  # 转换为ObjectId
                    {'$set': {'pagerank_score': score}},
                    upsert=False
                )
                updates.append(update)
                
                # 当累积到一定数量时执行批量更新
                if len(updates) >= batch_size:
                    result = self.collection.bulk_write(updates)
                    self.logger.info(f"Batch update completed: {result.modified_count} documents modified")
                    updates = []
            
            # 处理剩余的更新
            if updates:
                result = self.collection.bulk_write(updates)
                self.logger.info(f"Final batch update completed: {result.modified_count} documents modified")
            
            # 验证更新
            sample_doc = self.collection.find_one({'pagerank_score': {'$exists': True}})
            if sample_doc and 'pagerank_score' in sample_doc:
                self.logger.info(f"Verification: Found document with pagerank_score = {sample_doc['pagerank_score']}")
            else:
                self.logger.warning("Verification: Could not find any documents with pagerank_score field")
            
            # 统计有pagerank_score字段的文档数量
            docs_with_pagerank = self.collection.count_documents({'pagerank_score': {'$exists': True}})
            self.logger.info(f"Total documents with pagerank field: {docs_with_pagerank}")
            
        except Exception as e:
            self.logger.error(f"Error updating MongoDB: {str(e)}")
            raise

    def run_pagerank_pipeline(self):
        """
        运行完整的PageRank计算和更新流程
        """
        try:
            # 检查MongoDB连接
            try:
                self.collection.find_one()
                self.logger.info("Successfully connected to MongoDB")
            except Exception as e:
                self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
                raise
            
            # 获取文档数量
            doc_count = self.collection.count_documents({})
            self.logger.info(f"Found {doc_count} documents in collection")
            
            # 计算PageRank
            self.logger.info("Starting PageRank calculation...")
            pagerank_scores = self.calculate_pagerank()
            self.logger.info(f"PageRank calculation completed for {len(pagerank_scores)} pages")
            
            # 输出一些PageRank统计信息
            scores = list(pagerank_scores.values())
            if scores:
                self.logger.info(f"PageRank statistics:")
                self.logger.info(f"  Max score: {max(scores):.6f}")
                self.logger.info(f"  Min score: {min(scores):.6f}")
                self.logger.info(f"  Average score: {sum(scores)/len(scores):.6f}")
            
            # 更新MongoDB
            self.logger.info("Updating MongoDB with PageRank scores...")
            self.update_mongodb(pagerank_scores)
            
            self.logger.info("PageRank pipeline completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in PageRank pipeline: {str(e)}")
            raise

    def close(self):
        """清理MongoDB连接"""
        if hasattr(self, 'client'):
            self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

if __name__ == "__main__":
    with PageRankCalculator() as calculator:
        calculator.run_pagerank_pipeline()