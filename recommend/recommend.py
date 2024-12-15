import jieba
from elasticsearch import Elasticsearch
import json
import logging
import os

class UserBasedRecommender:
    def __init__(self, es_host='http://localhost:9201', index_name='nku_search'):
        """初始化推荐系统
        
        Args:
            es_host (str): Elasticsearch服务器地址
            index_name (str): 索引名称
        """
        # 确保ES主机地址格式正确
        if not es_host.startswith(('http://', 'https://')):
            es_host = 'http://' + es_host
            
        self.es = Elasticsearch([es_host])
        self.index_name = index_name
        
        # 加载停用词
        self.stopwords = set()
        try:
            stopwords_path = os.path.join(os.path.dirname(__file__), 'cn_stopwords.txt')
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                for line in f:
                    self.stopwords.add(line.strip())
        except Exception as e:
            logging.error(f"加载停用词文件失败: {str(e)}")
        
        # 配置日志
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'recommend.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _tokenize(self, text):
        """分词并去除停用词
        
        Args:
            text (str): 要分词的文本
            
        Returns:
            list: 分词结果列表
        """
        return [word for word in jieba.cut(text) if word not in self.stopwords]

    def get_user_recommendations(self, user_id, search_history, max_results=5):
        """基于用户搜索历史生成推荐
        
        Args:
            user_id (str): 用户ID
            search_history (list): 用户的搜索历史记录列表，每条记录应包含搜索词
            max_results (int): 返回的推荐数量
            
        Returns:
            list: 推荐文档列表
        """
        try:
            # 从搜索历史中提取关键词
            keywords = []
            for history in search_history:
                if isinstance(history, str):
                    search_text = history
                elif isinstance(history, dict):
                    search_text = history.get('text', '')
                else:
                    continue
                    
                # 对搜索词进行分词
                keywords.extend(self._tokenize(search_text))
            
            # 如果没有有效的关键词，返回空列表
            if not keywords:
                return []
            
            # 构建搜索查询
            should_queries = []
            for keyword in keywords:
                should_queries.extend([
                    {
                        "match": {
                            "title": {
                                "query": keyword,
                                "boost": 2.0  # 标题匹配的权重更高
                            }
                        }
                    },
                    {
                        "match": {
                            "content": {
                                "query": keyword,
                                "boost": 1.0
                            }
                        }
                    }
                ])
            
            # 构建完整的查询体
            body = {
                "query": {
                    "bool": {
                        "should": should_queries,
                        "minimum_should_match": 1
                    }
                },
                "size": max_results,
                "_source": ["url", "title", "department", "pagerank_score"],
                "sort": [
                    "_score",
                    {"pagerank_score": {"order": "desc"}}
                ]
            }
            
            # 执行搜索
            response = self.es.search(
                index=self.index_name,
                body=body
            )
            
            # 处理结果
            recommendations = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                recommendations.append({
                    'url': source['url'],
                    'title': source.get('title', ''),
                    'department': source.get('department', ''),
                    'score': hit['_score'],
                    'pagerank_score': source.get('pagerank_score', 0)
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成推荐时出错: {str(e)}")
            return []

# 使用示例
if __name__ == "__main__":
    # 初始化推荐系统
    recommender = UserBasedRecommender()
    
    # 测试用的搜索历史
    test_history = [
        {"text": "南开大学 计算机"},
        {"text": "人工智能"}
    ]
    
    # 获取推荐
    recommendations = recommender.get_user_recommendations(
        user_id="test_user",
        search_history=test_history
    )
    
    # 打印推荐结果
    print(json.dumps(recommendations, ensure_ascii=False, indent=2))