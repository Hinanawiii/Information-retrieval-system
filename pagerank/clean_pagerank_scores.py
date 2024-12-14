from pymongo import MongoClient
import logging
import os

def setup_logger():
    """设置日志"""
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 添加文件处理器
    file_handler = logging.FileHandler('logs/cleanup.log')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

def cleanup_pagerank():
    """清理MongoDB中的pagerank字段"""
    logger = setup_logger()
    
    try:
        # 连接MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['nku_search']
        collection = db['nku_pages']
        
        # 检查连接
        collection.find_one()
        logger.info("Successfully connected to MongoDB")
        
        # 统计有pagerank字段的文档数量
        count_before = collection.count_documents({'pagerank': {'$exists': True}})
        logger.info(f"Found {count_before} documents with pagerank field")
        
        if count_before > 0:
            # 执行更新操作，移除pagerank字段
            result = collection.update_many(
                {'pagerank': {'$exists': True}},
                {'$unset': {'pagerank': ""}}
            )
            
            logger.info(f"Removed pagerank field from {result.modified_count} documents")
        else:
            logger.info("No documents found with pagerank field")
        
        # 验证清理结果
        count_after = collection.count_documents({'pagerank': {'$exists': True}})
        logger.info(f"Verification: {count_after} documents still have pagerank field")
        
        client.close()
        logger.info("Cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise

if __name__ == "__main__":
    cleanup_pagerank()