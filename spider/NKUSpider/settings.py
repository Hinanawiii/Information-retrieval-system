BOT_NAME = 'NKUSpider'

SPIDER_MODULES = ['NKUSpider.spiders']
NEWSPIDER_MODULE = 'NKUSpider.spiders'

# MongoDB设置
MONGO_URI = 'mongodb://localhost:27017'
MONGO_DATABASE = 'nku_search'

# 设置允许的域名范围
ALLOWED_DOMAINS = ['nankai.edu.cn']  # 只爬取南开域名下的网站

# 修改关键配置
ROBOTSTXT_OBEY = False  # 南开大学网站可能没有严格的robots.txt
DOWNLOAD_DELAY = 0.3    # 设置下载延迟
CONCURRENT_REQUESTS = 16 # 并发请求数

# 添加下载器中间件
DOWNLOADER_MIDDLEWARES = {
    'NKUSpider.middlewares.RandomUserAgentMiddleware': 556,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# 配置管道
ITEM_PIPELINES = {
    'NKUSpider.pipelines.MongoPipeline': 302,
}

# MongoDB配置
LOCAL_MONGO_HOST = '127.0.0.1'
LOCAL_MONGO_PORT = 27017
DB_NAME = 'nku_search'