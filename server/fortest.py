from search import SearchEngine
import json

def get_index_mapping():
    search_engine = SearchEngine(es_host='http://localhost:9201', index_name='nku_search')
    # 获取映射并转换为字典
    mapping = search_engine.es.indices.get_mapping(index='nku_search').body
    print(json.dumps(mapping, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    get_index_mapping()