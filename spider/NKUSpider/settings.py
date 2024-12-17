BOT_NAME = 'NKUSpider'

SPIDER_MODULES = ['NKUSpider.spiders']
NEWSPIDER_MODULE = 'NKUSpider.spiders'

# MongoDB设置
MONGO_URI = 'mongodb://localhost:27017'
MONGO_DATABASE = 'nku_search'

# 设置允许的域名范围
allowed_domains = [
        'nankai.edu.cn',
        'cc.nankai.edu.cn',
        'news.nankai.edu.cn',
        'jwc.nankai.edu.cn',
        'graduate.nankai.edu.cn',
        'research.nankai.edu.cn',
        'math.nankai.edu.cn',
        'cs.nankai.edu.cn',        # 计算机学院
        'business.nankai.edu.cn',  # 商学院
        'physics.nankai.edu.cn',   # 物理学院
        'chem.nankai.edu.cn',      # 化学学院
        'history.nankai.edu.cn',   # 历史学院
        'literature.nankai.edu.cn',# 文学院
        'law.nankai.edu.cn',       # 法学院
        'spss.nankai.edu.cn',      # 社会科学学院
        'env.nankai.edu.cn',       # 环境科学与工程学院
        'sfl.nankai.edu.cn',       # 外国语学院
        'thepaper.cn',
        'ifeng.com',
        'sina.com.cn',  # 新浪新闻的主域名
        'news.sina.com.cn',
        'finance.sina.com.cn',
        'sports.sina.com.cn',
        'ent.sina.com.cn',
        'tech.sina.com.cn',
        'qq.com',           # 腾讯主域名
        'news.qq.com',      # 新闻
        'finance.qq.com',   # 财经
        'sports.qq.com',    # 体育
        'new.qq.com',       # 新版新闻
        'tech.qq.com' 
    ]

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