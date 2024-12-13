from pymongo import MongoClient

# 连接MongoDB
client = MongoClient('localhost', 27017)
db = client['nku_search']
collection = db['nku_pages']

# 查询有pagerank_score字段的文档数量
docs_with_pagerank = collection.count_documents({"pagerank_score": {"$exists": True}})
print(f"包含PageRank分数的文档数: {docs_with_pagerank}")

# 查看一些样本文档的分数
sample_docs = collection.find(
    {"pagerank_score": {"$exists": True}},
    {"url": 1, "pagerank_score": 1, "_id": 0}
).limit(5)

print("\n示例文档的PageRank分数:")
for doc in sample_docs:
    print(f"URL: {doc['url']}")
    print(f"PageRank: {doc['pagerank_score']}")
    print("-" * 50)

client.close()