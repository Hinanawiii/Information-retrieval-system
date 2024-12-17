# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from ..items import NKUSpiderItem
import re
from datetime import datetime
from pymongo import MongoClient
import logging

class NKUSpider(scrapy.Spider):
    name = 'nku_spider'
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
    custom_settings = {
    'RETRY_TIMES': 5,  # 增加重试次数
    'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],  # 扩展重试状态码
    'DOWNLOAD_TIMEOUT': 15,  # 增加超时时间
    'CONCURRENT_REQUESTS': 8,  # 降低并发请求数
    'DOWNLOAD_DELAY': 1,  # 增加下载延迟
    'DEPTH_LIMIT': 5,  # 增加爬取深度限制
    'DEPTH_PRIORITY': 1,  # 优先爬取浅层页面
    'CLOSESPIDER_ITEMCOUNT': 100000,
    'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleLifoDiskQueue',
    'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.LifoMemoryQueue',
    'LOG_LEVEL': 'DEBUG'  # 设置更详细的日志级别
    }
    
    def __init__(self, *args, **kwargs):
        super(NKUSpider, self).__init__(*args, **kwargs)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['nku_search']
        self.collection = self.db['nku_pages']
        self.jump_num = 0
        
        # 扩展起始URL
        self.start_urls_dict = {
            'main': 'https://www.sina.com.cn/',           # 新浪首页
            'news': 'https://news.sina.com.cn/',          # 新闻中心
            'finance': 'https://finance.sina.com.cn/',     # 财经
            'sports': 'https://sports.sina.com.cn/',       # 体育
            'ent': 'https://ent.sina.com.cn/',            # 娱乐
            'tech': 'https://tech.sina.com.cn/',          # 科技
            'edu': 'https://edu.sina.com.cn/',            # 教育
            'fashion': 'https://fashion.sina.com.cn/',     # 时尚
            'auto': 'https://auto.sina.com.cn/',          # 汽车
            'games': 'https://games.sina.com.cn/',        # 游戏
            'mil': 'https://mil.news.sina.com.cn/',       # 军事
            'video': 'https://video.sina.com.cn/',        # 视频
            'travel': 'https://travel.sina.com.cn/',      # 旅游
            'cj': 'https://cj.sina.com.cn/',              # 创事记
            'history': 'https://history.sina.com.cn/',    # 历史
            'sports_nba': 'https://sports.sina.com.cn/nba/',  # NBA专区
            'finance_stock': 'https://finance.sina.com.cn/stock/', # 股票
            'news_world': 'https://news.sina.com.cn/world/',   # 国际新闻
            'news_china': 'https://news.sina.com.cn/china/',   # 国内新闻
            'society': 'https://news.sina.com.cn/society/'     # 社会新闻
        }

    def start_requests(self):
        for category, url in self.start_urls_dict.items():
            yield Request(url, callback=self.parse, meta={'category': category})

    def parse(self, response):
        try:
            outlinks = {}
            for link in response.css('a'):
                href = link.attrib.get('href', '')
                if href:
                    # 处理相对URL
                    if not href.startswith('http'):
                        href = response.urljoin(href)
                    
                    # 检查是否是澎湃新闻的URL
                    if 'sina.com' in href:
                        text = self.clean_text(link.css('::text').get())
                        outlinks[href] = text if text else ''

            # 检查是否已爬取
            if self.collection.find_one({'url': response.url}):
                self.jump_num += 1
                logging.info(f"URL已存在，跳过：{response.url}, 已跳过{self.jump_num}个")
                
            else:
                item = NKUSpiderItem()
                
                # 基本信息提取
                item['url'] = response.url
                item['title'] = self.clean_text(response.css('title::text').get())
                item['snapshot_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                item['content_type'] = response.headers.get('Content-Type', b'').decode()
                
                # 内容提取和清洗
                content = ' '.join([
                    self.clean_text(text)
                    for text in response.css('body ::text').getall()
                    if self.clean_text(text)
                ])
                item['content'] = content
                
                # 提取发布时间
                date_pattern = r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}'
                date_match = re.search(date_pattern, response.text)
                item['publish_time'] = date_match.group() if date_match else None
                        # 提取链接和锚文本
                '''         
            outlinks = {}
            for link in response.css('a'):
                href = link.attrib.get('href', '')
                if href and 'nankai.edu.cn' in href:
                    if not href.startswith('http'):
                        href = response.urljoin(href)
                    text = self.clean_text(link.css('::text').get())
                    outlinks[href] = text if text else ''
                    '''
                # 在parse方法中的链接提取部分
                item['outlinks'] = list(outlinks.keys())
                item['anchor_texts'] = outlinks
                
                # 保存原始HTML
                item['raw_html'] = response.text
                
                # 提取部门信息
                department = re.search(r'//([^/]+)\.nankai\.edu\.cn', response.url)
                item['department'] = department.group(1) if department else 'unknown'

                # 返回item并继续爬取外链
                yield item

            for url in outlinks.keys():
                yield Request(url, callback=self.parse, meta=response.meta)

        except Exception as e:
            logging.error(f'Error parsing {response.url}: {str(e)}')

    def clean_text(self, text):
        if not text:
            return ''
        text = re.sub(r'\u3000', '', text)
        text = re.sub(r'[ \xa0?]+', ' ', text)
        text = re.sub(r'\s*\n\s*', '\n', text)
        text = re.sub(r'\s*(\s)', r'\1', text)
        return text.strip()

    def closed(self, reason):
        self.client.close()