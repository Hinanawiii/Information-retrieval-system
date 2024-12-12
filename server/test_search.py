from search import SearchEngine
import json

def print_results(results, search_type):
    """打印搜索结果的辅助函数"""
    print(f"\n=== {search_type} 搜索结果 ===")
    print(f"找到 {results['total']} 个结果，耗时 {results['took']}ms")
    print("\n前几个结果:")
    for i, result in enumerate(results['results'][:3], 1):
        print(f"\n结果 {i}:")
        print(f"标题: {result['title']}")
        print(f"网址: {result['url']}")
        if 'title_highlight' in result:
            print(f"标题高亮: {result['title_highlight']}")
        if 'content_highlight' in result:
            print(f"内容高亮: {result['content_highlight']}")
        print("-" * 50)

def test_search_functions():
    # 初始化搜索引擎
    search_engine = SearchEngine(
        es_host='http://localhost:9201',
        index_name='nku_search'
    )

    try:
        # 1. 测试基本搜索
        print("\n测试基本搜索...")
        results = search_engine.basic_search(
            query="计算机",
            page=1,
            size=3
        )
        print_results(results, "基本")

        # 2. 测试通配符搜索
        print("\n测试通配符搜索...")
        results = search_engine.wildcard_search(
            query="计算*",
            page=1,
            size=3
        )
        print_results(results, "通配符")

        # 3. 测试短语搜索
        print("\n测试短语搜索...")
        results = search_engine.phrase_search(
            query="南开大学计算机",
            page=1,
            size=3
        )
        print_results(results, "短语")

        # 4. 测试带过滤条件的搜索
        print("\n测试带过滤条件的搜索...")
        results = search_engine.basic_search(
            query="计算机",
            page=1,
            size=3,
            department="计算机学院",
            start_date="2023-01-01"
        )
        print_results(results, "过滤")

        # 5. 测试搜索建议
        print("\n测试搜索建议...")
        suggestions = search_engine.suggest_search("计算")
        print("搜索建议:", suggestions)

        # 6. 测试获取部门列表
        print("\n测试获取部门列表...")
        departments = search_engine.get_departments()
        print("可用部门:", departments)

    except Exception as e:
        print(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    test_search_functions()