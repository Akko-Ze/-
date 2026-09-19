# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import dataclass


# 这个装饰器可以改造类，简化用于存储数据的类的编写，自动生成__init__()等方法
@dataclass
class DistributedBooksItem:
    # define the fields for your item here like:
    # name: str | None = None
    UPC: str | None = None
    标题: str | None = None
    类别: str | None = None
    价钱: str | None = None
    库存: str | None = None
    评分: str | None = None
    描述: str | None = None
    税前价格: str | None = None
    税后价格: str | None = None
    税: str | None = None
    图片链接: str | None = None
    网页链接: str | None = None

