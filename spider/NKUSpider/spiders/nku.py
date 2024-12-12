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
    allowed_domains = ['nankai.edu.cn']
    
    def __init__(self, *args, **kwargs):
        super(NKUSpider, self).__init__(*args, **kwargs)
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['nku_search']
        self.collection = self.db['nku_pages']
        self.jump_num = 0
        
        # 定义不同类型的起始URL
        self.start_urls_dict = {
            'news': 'https://news.nankai.edu.cn',
            'main': 'https://www.nankai.edu.cn',
            'jwc': 'https://jwc.nankai.edu.cn',
            # 可以添加更多分类
        }

    def start_requests(self):
        for category, url in self.start_urls_dict.items():
            yield Request(url, callback=self.parse, meta={'category': category})

    def parse(self, response):
        try:
            # 检查是否已爬取
            if self.collection.find_one({'url': response.url}):
                self.jump_num += 1
                logging.info(f"URL已存在，跳过：{response.url}, 已跳过{self.jump_num}个")
                return

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
            outlinks = {}
            for link in response.css('a'):
                href = link.attrib.get('href', '')
                if href and 'nankai.edu.cn' in href:
                    if not href.startswith('http'):
                        href = response.urljoin(href)
                    text = self.clean_text(link.css('::text').get())
                    outlinks[href] = text if text else ''
            
            item['outlinks'] = list(outlinks.keys())
            item['anchor_texts'] = outlinks
            
            # 保存原始HTML
            item['raw_html'] = response.text
            
            # 提取部门信息
            department = re.search(r'//([^/]+)\.nankai\.edu\.cn', response.url)
            item['department'] = department.group(1) if department else 'unknown'

            # 返回item并继续爬取外链
            yield item
            
            for url in item['outlinks']:
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