from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from NKUSpider.spiders.nku import NKUSpider

if __name__ == '__main__':
    process = CrawlerProcess(get_project_settings())
    process.crawl(NKUSpider)
    process.start()