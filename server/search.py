#search.py
from elasticsearch import Elasticsearch
from datetime import datetime
import logging
import os

class SearchEngine:
    def __init__(self, es_host='http://localhost:9200', index_name='nku_search'):
        """初始化搜索引擎
        
        Args:
            es_host (str): Elasticsearch服务器地址
            index_name (str): 要搜索的索引名称
        """
        # 确保ES主机地址格式正确
        if not es_host.startswith(('http://', 'https://')):
            es_host = 'http://' + es_host
            
        self.es = Elasticsearch([es_host])
        self.index_name = index_name
        
        # 配置日志
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'search.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def basic_search(self, query, page=1, size=10, **kwargs):
        try:
            # 构建搜索条件
            must_conditions = []
            
            # 基础全文搜索
            if query:
                text_query = {
                    "bool": {
                        "should": [
                            # 标题匹配，赋予最高权重
                            {
                                "match": {
                                    "title": {
                                        "query": query,
                                        "boost": 4.0,
                                        "analyzer": "ik_max_word"
                                    }
                                }
                            },
                            # 内容匹配
                            {
                                "match": {
                                    "content": {
                                        "query": query,
                                        "boost": 1.0,
                                        "analyzer": "ik_max_word"
                                    }
                                }
                            },
                            # 锚文本匹配
                            {
                                "nested": {
                                    "path": "anchor_texts",
                                    "query": {
                                        "match": {
                                            "anchor_texts.text": {
                                                "query": query,
                                                "boost": 2.0,
                                                "analyzer": "ik_max_word"
                                            }
                                        }
                                    },
                                    "score_mode": "avg"  # 使用平均分数
                                }
                            },
                            # 短语匹配，提高精确匹配的权重
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["title^3", "content"],
                                    "type": "phrase",
                                    "boost": 2.0
                                }
                            }
                        ]
                    }
                }
                
                # 使用 function_score 查询结合 PageRank
                main_query = {
                    "function_score": {
                        "query": text_query,
                        "functions": [
                            {
                                "field_value_factor": {
                                    "field": "pagerank_score",
                                    "factor": 0.2,        # PageRank 权重因子
                                    "modifier": "log1p",  # 使用 log1p 来平滑高分数
                                    "missing": 0
                                }
                            }
                        ],
                        "boost_mode": "sum",     # 将相关性分数和 PageRank 分数相加
                        "score_mode": "multiply", # 如果有多个函数，将它们的分数相乘
                        "min_score": 0.1         # 设置最小分数阈值
                    }
                }
                
                must_conditions.append(main_query)
            
            # 部门筛选
            if kwargs.get('department'):
                must_conditions.append({
                    "term": {
                        "department": kwargs['department']
                    }
                })
            
            # 日期范围筛选（如果有的话）
            date_range = {}
            if kwargs.get('start_date'):
                date_range['gte'] = kwargs['start_date']
            if kwargs.get('end_date'):
                date_range['lte'] = kwargs['end_date']
            if date_range:
                must_conditions.append({
                    "range": {
                        "publish_time": date_range
                    }
                })
            
            # 构建完整的查询体
            body = {
                "query": {
                    "bool": {
                        "must": must_conditions
                    }
                },
                "from": (page - 1) * size,
                "size": size,
                "_source": {
                    "excludes": ["anchor_texts", "outlinks"]  # 排除不需要返回的大字段
                },
                "highlight": {
                    "fields": {
                        "title": {
                            "pre_tags": ["<em>"],
                            "post_tags": ["</em>"]
                        },
                        "content": {
                            "pre_tags": ["<em>"],
                            "post_tags": ["</em>"],
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                }
            }
            
            # 添加自定义排序
            if kwargs.get('sort_by'):
                sort_order = kwargs.get('sort_order', 'desc')
                body["sort"] = [{kwargs['sort_by']: sort_order}]
            
            # 执行搜索
            response = self.es.search(
                index=self.index_name,
                body=body
            )
            
            # 处理结果
            hits = response['hits']
            results = []
            for hit in hits['hits']:
                source = hit['_source']
                result = {
                    'url': source['url'],
                    'title': source.get('title', ''),
                    'content': source.get('content', ''),
                    'department': source.get('department', ''),
                    'score': hit['_score'],
                    'pagerank_score': source.get('pagerank_score', 0)
                }
                
                # 添加高亮结果
                if 'highlight' in hit:
                    if 'title' in hit['highlight']:
                        result['title_highlight'] = ' ... '.join(hit['highlight']['title'])
                    if 'content' in hit['highlight']:
                        result['content_highlight'] = ' ... '.join(hit['highlight']['content'])
                
                results.append(result)
            
            return {
                'total': hits['total']['value'],
                'took': response['took'],
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"搜索出错: {str(e)}")
            raise

    def wildcard_search(self, query, page=1, size=10):
        """通配符搜索功能，支持 * 和 ? 通配符
        
        Args:
            query (str): 搜索关键词，可包含通配符 * 和 ?
            page (int): 页码，从1开始
            size (int): 每页结果数
            
        Returns:
            dict: 搜索结果，包含总数、耗时和文档列表
        """
        try:
            body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "wildcard": {
                                    "title": {
                                        "value": f"*{query}*",
                                        "boost": 2.0
                                    }
                                }
                            },
                            {
                                "wildcard": {
                                    "content": {
                                        "value": f"*{query}*",
                                        "boost": 1.0
                                    }
                                }
                            }
                        ]
                    }
                },
                "from": (page - 1) * size,
                "size": size,
                "highlight": {
                    "fields": {
                        "title": {
                            "pre_tags": ["<em>"],
                            "post_tags": ["</em>"]
                        },
                        "content": {
                            "pre_tags": ["<em>"],
                            "post_tags": ["</em>"],
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                }
            }
            
            # 执行搜索
            response = self.es.search(
                index=self.index_name,
                body=body
            )
            
            # 处理结果
            hits = response['hits']
            results = []
            for hit in hits['hits']:
                source = hit['_source']
                result = {
                    'url': source['url'],
                    'title': source.get('title', ''),
                    'content': source.get('content', ''),
                    'department': source.get('department', ''),
                    'publish_time': source.get('publish_time', ''),
                    'score': hit['_score'],
                    'pagerank_score': source.get('pagerank_score', 0),
                    'snapshot_time': source.get('snapshot_time', '')
                }
                
                # 添加高亮结果
                if 'highlight' in hit:
                    if 'title' in hit['highlight']:
                        result['title_highlight'] = ' ... '.join(hit['highlight']['title'])
                    if 'content' in hit['highlight']:
                        result['content_highlight'] = ' ... '.join(hit['highlight']['content'])
                
                results.append(result)
            
            return {
                'total': hits['total']['value'],
                'took': response['took'],
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"通配符搜索出错: {str(e)}")
            raise

    def phrase_search(self, query, page=1, size=10):
        """短语搜索功能，要求关键词按照确切顺序出现
        
        Args:
            query (str): 搜索短语
            page (int): 页码，从1开始
            size (int): 每页结果数
            
        Returns:
            dict: 搜索结果，包含总数、耗时和文档列表
        """
        try:
            body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match_phrase": {
                                    "title": {
                                        "query": query,
                                        "boost": 2.0,
                                        "slop": 0  # 短语中的词必须完全相邻
                                    }
                                }
                            },
                            {
                                "match_phrase": {
                                    "content": {
                                        "query": query,
                                        "boost": 1.0,
                                        "slop": 1  # 允许词之间有一个词的间隔
                                    }
                                }
                            }
                        ]
                    }
                },
                "from": (page - 1) * size,
                "size": size,
                "highlight": {
                    "fields": {
                        "title": {
                            "type": "unified",
                            "pre_tags": ["<em>"],
                            "post_tags": ["</em>"]
                        },
                        "content": {
                            "type": "unified",
                            "pre_tags": ["<em>"],
                            "post_tags": ["</em>"],
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                }
            }
            
            # 执行搜索
            response = self.es.search(
                index=self.index_name,
                body=body
            )
            
            # 处理结果
            hits = response['hits']
            results = []
            for hit in hits['hits']:
                source = hit['_source']
                result = {
                    'url': source['url'],
                    'title': source.get('title', ''),
                    'content': source.get('content', ''),
                    'department': source.get('department', ''),
                    'publish_time': source.get('publish_time', ''),
                    'score': hit['_score'],
                    'pagerank_score': source.get('pagerank_score', 0),
                    'snapshot_time': source.get('snapshot_time', '')
                }
                
                # 添加高亮结果
                if 'highlight' in hit:
                    if 'title' in hit['highlight']:
                        result['title_highlight'] = ' ... '.join(hit['highlight']['title'])
                    if 'content' in hit['highlight']:
                        result['content_highlight'] = ' ... '.join(hit['highlight']['content'])
                
                results.append(result)
            
            return {
                'total': hits['total']['value'],
                'took': response['took'],
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"短语搜索出错: {str(e)}")
            raise
        try:
            body = {
                "suggest": {
                    "title_suggest": {
                        "prefix": prefix,
                        "completion": {
                            "field": "title.keyword",
                            "size": size,
                            "skip_duplicates": True
                        }
                    }
                }
            }
            
            response = self.es.search(
                index=self.index_name,
                body=body
            )
            
            suggestions = []
            for suggestion in response['suggest']['title_suggest'][0]['options']:
                suggestions.append(suggestion['text'])
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"获取搜索建议时出错: {str(e)}")
            return []

    def suggest_search(self, prefix, size=5):
        """搜索建议功能，基于前缀提供搜索建议
        
        Args:
            prefix (str): 用户输入的前缀
            size (int): 返回建议的数量
            
        Returns:
            list: 搜索建议列表
        """
        try:
            body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "prefix": {
                                    "title.keyword": {
                                        "value": prefix,
                                        "boost": 2.0
                                    }
                                }
                            },
                            {
                                "prefix": {
                                    "title": {
                                        "value": prefix
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": size,
                "_source": ["title"],  # 只返回标题字段
                "collapse": {
                    "field": "title.keyword"  # 去重
                }
            }
            
            response = self.es.search(
                index=self.index_name,
                body=body
            )
            
            # 提取建议
            suggestions = []
            for hit in response['hits']['hits']:
                suggestions.append(hit['_source']['title'])
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"获取搜索建议时出错: {str(e)}")
            return []
        
    def get_departments(self):
        """获取所有可用的部门列表
        
        Returns:
            list: 部门名称列表
        """
        try:
            body = {
                "size": 0,
                "aggs": {
                    "departments": {
                        "terms": {
                            "field": "department",
                            "size": 100
                        }
                    }
                }
            }
            
            response = self.es.search(
                index=self.index_name,
                body=body
            )
            
            departments = []
            for bucket in response['aggregations']['departments']['buckets']:
                departments.append(bucket['key'])
            
            return departments
            
        except Exception as e:
            self.logger.error(f"获取部门列表时出错: {str(e)}")
            return []

if __name__ == "__main__":
    # 使用示例
    search_engine = SearchEngine()
    
    # 基础搜索示例
    results = search_engine.basic_search(
        query="计算机",
        page=1,
        size=10,
        department="计算机学院",
        start_date="2024-01-01",
        sort_by="publish_time",
        sort_order="desc"
    )
    
    print(f"找到 {results['total']} 个结果，耗时 {results['took']}ms")