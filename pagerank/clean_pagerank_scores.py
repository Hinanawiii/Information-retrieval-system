from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import logging

def clean_pagerank_scores(es_host='http://localhost:9201', index_name='nku_search'):
    """清除所有文档的pagerank_score字段"""
    es = Elasticsearch([es_host])
    
    try:
        # 更新脚本
        update_body = {
            "script": {
                "source": "ctx._source.remove('pagerank_score')",
                "lang": "painless"
            },
            "query": {
                "exists": {
                    "field": "pagerank_score"
                }
            }
        }
        
        # 执行更新
        result = es.update_by_query(
            index=index_name,
            body=update_body,
            conflicts='proceed'  # 遇到冲突时继续进行
        )
        
        print(f"更新完成：处理了 {result['total']} 个文档，更新了 {result['updated']} 个文档")
        
    except Exception as e:
        print(f"清除PageRank分数时出错: {str(e)}")

if __name__ == "__main__":
    clean_pagerank_scores()