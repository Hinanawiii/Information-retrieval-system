from elasticsearch import Elasticsearch
import networkx as nx
import logging
import os
from typing import Dict, Set, Optional

class WebGraph:
    def __init__(self, es_host: str = 'http://localhost:9201', index_name: str = 'nku_search'):
        """
        初始化Web图构建器
        :param es_host: Elasticsearch主机地址
        :param index_name: 索引名称
        """
        self.es = Elasticsearch([es_host])
        self.index_name = index_name
        self.graph = nx.DiGraph()
        self.url_to_id = {}  # 存储URL到文档ID的映射
        
        # 配置日志
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'graph_builder.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def build_graph(self, batch_size: int = 1000) -> nx.DiGraph:
        """
        从ES构建网页关系图
        :param batch_size: ES查询的批量大小
        :return: 构建好的有向图
        """
        try:
            # 使用scroll API获取所有文档
            query = {
                "_source": ["url", "outlinks"],
                "query": {
                    "match_all": {}
                }
            }
            
            # 初始化scroll
            page = self.es.search(
                index=self.index_name,
                body=query,
                scroll='5m',
                size=batch_size
            )
            
            scroll_id = page['_scroll_id']
            hits = page['hits']['hits']
            
            processed = 0
            total_docs = page['hits']['total']['value']
            self.logger.info(f"开始构建图,总文档数: {total_docs}")
            
            while hits:
                for hit in hits:
                    url = hit['_source']['url']
                    outlinks = hit['_source'].get('outlinks', [])
                    doc_id = hit['_id']
                    
                    # 保存URL到文档ID的映射
                    self.url_to_id[url] = doc_id
                    
                    # 添加节点和边
                    self.graph.add_node(url)
                    for outlink in outlinks:
                        if outlink != url:  # 避免自环
                            self.graph.add_node(outlink)
                            self.graph.add_edge(url, outlink)
                    
                    processed += 1
                    if processed % 1000 == 0:
                        self.logger.info(f"已处理 {processed}/{total_docs} 文档")
                
                # 获取下一批结果
                page = self.es.scroll(scroll_id=scroll_id, scroll='5m')
                scroll_id = page['_scroll_id']
                hits = page['hits']['hits']
            
            self.logger.info(f"图构建完成. 节点数: {self.graph.number_of_nodes()}, "
                           f"边数: {self.graph.number_of_edges()}, "
                           f"URL映射数: {len(self.url_to_id)}")
            
            return self.graph
            
        except Exception as e:
            self.logger.error(f"构建图时出错: {str(e)}")
            raise

    def get_dangling_nodes(self) -> Set[str]:
        """获取没有出链的节点"""
        return {node for node in self.graph.nodes() 
                if self.graph.out_degree(node) == 0}

    def get_orphan_nodes(self) -> Set[str]:
        """获取没有入链的节点"""
        return {node for node in self.graph.nodes() 
                if self.graph.in_degree(node) == 0}

    def get_graph_statistics(self) -> Dict:
        """获取图的统计信息"""
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'dangling_nodes': len(self.get_dangling_nodes()),
            'orphan_nodes': len(self.get_orphan_nodes()),
            'is_strongly_connected': nx.is_strongly_connected(self.graph),
            'weakly_connected_components': nx.number_weakly_connected_components(self.graph),
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'mapped_urls': len(self.url_to_id)
        }
        return stats

    def preprocess_graph(self, remove_orphans: bool = True) -> None:
        """预处理图,可选择性地移除孤立节点"""
        if remove_orphans:
            orphans = self.get_orphan_nodes()
            self.graph.remove_nodes_from(orphans)
            self.logger.info(f"已移除 {len(orphans)} 个孤立节点")
        
        # 确保图是连通的
        if not nx.is_weakly_connected(self.graph):
            largest_cc = max(nx.weakly_connected_components(self.graph), key=len)
            self.graph = self.graph.subgraph(largest_cc).copy()
            self.logger.info("已提取最大连通分量")

    def save_graph(self, filepath: str) -> None:
        """保存图到文件"""
        nx.write_gpickle(self.graph, filepath)
        self.logger.info(f"图已保存到: {filepath}")

    def load_graph(self, filepath: str) -> Optional[nx.DiGraph]:
        """从文件加载图"""
        try:
            self.graph = nx.read_gpickle(filepath)
            self.logger.info(f"已从 {filepath} 加载图")
            return self.graph
        except Exception as e:
            self.logger.error(f"加载图时出错: {str(e)}")
            return None

    def get_url_id_mapping(self) -> Dict[str, str]:
        """获取URL到文档ID的映射"""
        return self.url_to_id.copy()