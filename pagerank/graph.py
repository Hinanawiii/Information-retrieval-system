from pymongo import MongoClient
import networkx as nx
import logging
from typing import Dict, Set, List
import json

class GraphBuilder:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        """
        初始化GraphBuilder
        
        Args:
            mongo_uri: MongoDB连接URI
        """
        self.client = MongoClient(mongo_uri)
        self.db = self.client['nku_search']
        self.collection = self.db['nku_pages']
        self.graph = nx.DiGraph()
        
        # 配置日志
        logging.basicConfig(
            filename='logs/graph_builder.log',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def build_graph(self) -> nx.DiGraph:
        """
        从MongoDB构建有向图
        
        Returns:
            构建好的NetworkX有向图
        """
        try:
            # 获取所有文档
            documents = self.collection.find({}, {'_id': 1, 'url': 1, 'outlinks': 1})
            
            # 构建URL到ID的映射
            url_to_id: Dict[str, str] = {}
            for doc in documents:
                url_to_id[doc['url']] = str(doc['_id'])
            
            # 重新获取文档（因为MongoDB游标已经用完）
            documents = self.collection.find({}, {'_id': 1, 'url': 1, 'outlinks': 1})
            
            # 添加节点和边
            for doc in documents:
                source_id = str(doc['_id'])
                self.graph.add_node(source_id)
                
                outlinks = doc.get('outlinks', [])
                for target_url in outlinks:
                    if target_url in url_to_id:
                        target_id = url_to_id[target_url]
                        self.graph.add_edge(source_id, target_id)
            
            self.logger.info(f"Graph built successfully with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
            return self.graph
            
        except Exception as e:
            self.logger.error(f"Error building graph: {str(e)}")
            raise

    def get_graph(self) -> nx.DiGraph:
        """
        获取构建好的图
        
        Returns:
            构建好的NetworkX有向图
        """
        return self.graph

    def save_graph(self, filepath: str):
        """
        将图结构保存到文件
        
        Args:
            filepath: 保存路径
        """
        try:
            # 将图转换为字典格式
            graph_data = nx.node_link_data(self.graph)
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Graph saved successfully to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving graph: {str(e)}")
            raise

    def load_graph(self, filepath: str):
        """
        从文件加载图结构
        
        Args:
            filepath: 图数据文件路径
        """
        try:
            # 从文件读取图数据
            with open(filepath, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            # 转换为NetworkX图
            self.graph = nx.node_link_graph(graph_data)
            
            self.logger.info(f"Graph loaded successfully from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error loading graph: {str(e)}")
            raise

    def __del__(self):
        """清理MongoDB连接"""
        self.client.close()