# -*- coding: utf-8 -*-
import scrapy
from scrapy import Item, Field

class NKUSpiderItem(scrapy.Item):
    collection = 'nku_pages'  # MongoDB集合名称

    url = Field()         # 页面URL
    title = Field()       # 页面标题
    content = Field()     # 页面内容
    publish_time = Field() # 发布时间（如果有）
    department = Field()   # 所属部门/学院（从URL或面包屑导航提取）
    outlinks = Field()     # 页面包含的外链（用于PageRank）
    anchor_texts = Field() # 链接的锚文本（字典格式，key为URL，value为锚文本）
    snapshot_time = Field()# 抓取时间
    content_type = Field() # 内容类型（html/doc/pdf等）
    raw_html = Field()     # 原始HTML（用于快照功能）