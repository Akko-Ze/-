import redis.asyncio as redis
from scrapy import signals


class WorkerStatsExtensions:
    def __init__(self, crawler):
        self.worker_id = crawler.settings.get('WORKER_ID')
        self.redis_client = redis.Redis.from_url(crawler.settings.get('REDIS_URL'), decode_responses=True)

    # crawler是scrapy提供的关于当前运行环境的一系列信息，包括crawler.settings等
    # 而用classmethod是因为目前还没有对象，无法通过对象.from_crawler()来使用这个函数
    # 所以@classmethod来装饰，而cls就相当于类本身，有了cls，就在scrapy启动时调用WorkerStatsExtensions.from_crawler(crawler)
    @classmethod
    def from_crawler(cls, crawler):
        # 这个cls(crawler)里之所以需要crawler是因为初始化时需要crawler这个参数
        extension = cls(crawler)

        crawler.signals.connect(
            extension.item_scraped,
            signal=signals.item_scraped
        )
        return extension

    async def item_scraped(self, item, response, spider):
        await self.redis_client.hincrby(
            "books:worker_items",
            self.worker_id,
            1,
        )



