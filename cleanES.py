# 使用Python elasticsearch客户端
from elasticsearch import Elasticsearch
es = Elasticsearch(['localhost:9201'])
es.indices.delete(index='your_index_name', ignore=[400, 404])