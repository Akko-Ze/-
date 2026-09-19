# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# ItemAdapter是可以统一操作不同类型的item的一个类，例如spider传过来dataclass、field()、字典，都可以使用ItemAdapter(item)来使用
from itemadapter import ItemAdapter
import re
import psycopg


class DistributedBooksPipeline:
    # 评分映射表
    rating_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5,
    }

    def process_item(self, item):
        # 用ItemAdapter统一包装item，方便统一操作,就可以像字典一样操作，更改和接收
        adapter = ItemAdapter(item)

        # 清洗价格
        adapter['价钱'] = self.clean_price(adapter.get('价钱'))
        adapter['税前价格'] = self.clean_price(adapter.get('税前价格'))
        adapter['税后价格'] = self.clean_price(adapter.get('税后价格'))
        adapter['税'] = self.clean_price(adapter.get('税'))

        # 清洗评分
        adapter['评分'] = self.clean_rating(adapter.get('评分'))

        # 清洗库存
        adapter['库存'] = self.clean_stock(adapter.get('库存'))

        return item

    def clean_price(self, value):
        if not value:
            return None

        value = value.replace("£", "").strip()

        try:
            return float(value)
        except ValueError:
            return None

    def clean_rating(self, value):
        if not value:
            return None
        return self.rating_map.get(value)

    def clean_stock(self, value):
        if not value:
            return None

        match = re.search(r"(\d+)\s+available", value)
        if match:
            return int(match.group(1))

        return 0


class PostgresPipeline:
    # 因为pipeline不像spider那样直接有self.settings,需要通过from_crawler()拿到crawler.settings
    @classmethod
    def from_crawler(cls, crawler):
        # 相当于执行pipeline = PostgresPipeline()
        pipeline = cls()

        pipeline.db_host = crawler.settings.get("POSTGRES_HOST")
        pipeline.db_port = crawler.settings.get("POSTGRES_PORT")
        pipeline.db_name = crawler.settings.get("POSTGRES_DB")
        pipeline.db_user = crawler.settings.get("POSTGRES_USER")
        pipeline.db_password = crawler.settings.get("POSTGRES_PASSWORD")

        return pipeline


    def open_spider(self):
        self.conn = psycopg.connect(
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
        )
        self.cursor = self.conn.cursor()

    def process_item(self, item):
        adapter = ItemAdapter(item)

        # execute()只是在内存中执行了指令，并没有固化到硬盘上
        # on conflict (a) do nothing:a字段有冲突也忽略
        self.cursor.execute(
            """
            insert into books(upc, title, category, price, stock, rating, description, price_excl_tax, price_incl_tax,
                              tax, image_url, book_url)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) on conflict (upc) do nothing
            """,
            (
                adapter.get("UPC"),
                adapter.get("标题"),
                adapter.get("类别"),
                adapter.get("价钱"),
                adapter.get("库存"),
                adapter.get("评分"),
                adapter.get("描述"),
                adapter.get("税前价格"),
                adapter.get("税后价格"),
                adapter.get("税"),
                adapter.get("图片链接"),
                adapter.get("网页链接"),
            )
        )

        # 把execute()执行的指令内容固化到硬盘上
        self.conn.commit()
        return item

    def close_spider(self):
        self.cursor.close()
        self.conn.close()

