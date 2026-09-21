import redis.asyncio as redis
import scrapy
from redis.maint_notifications import MaintNotificationsConfig
from distributed_books.items import DistributedBooksItem
import asyncio
import time


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    # start_urls = ["https://books.toscrape.com"]

    # 持续心跳
    async def heartbeat(self, redis_client, worker_id):
        while True:
            await redis_client.hset("books:workers", worker_id, int(time.time()))
            await asyncio.sleep(5)

    async def start(self):
        # worker_id
        worker_id = self.settings.get("WORKER_ID")

        # decode_responses是要对responses解码，因为redis里是字节流，需要解码为字符串
        # 注意：此处的redis是异步的redis客户端
        redis_client = redis.Redis.from_url(
            self.settings.get("REDIS_URL"),
            decode_responses=True,
            socket_timeout=None,
        )

        # redis_client操作redis,不阻塞执行heartbeat
        asyncio.create_task(self.heartbeat(redis_client, worker_id))

        self.logger.info(f"【{worker_id}】已启动心跳")
        self.logger.info(f"【{worker_id}】 worker正在等待Redis起始任务...")

        while True:
            # 把blpop阻塞式函数放到一个线程里，防止阻塞整个事件循环，只阻塞这一个线程,当然，这只是同步的redis客户端
            # asyncio.to_thread(
            #     redis_client.blpop,
            #     "books:start_urls",
            #     0
            # )

            # 可以使用redis.asyncio异步客户端，这样就不用to_thread()了
            result = await redis_client.blpop("books:start_urls", 0)
            _, url = result

            self.logger.info(f"从redis获取起始url:{url}")

            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        # 直接开始写spider函数

        # 返回selectorList()选择器列表，不等同于列表，但功能类似
        books = response.css("article.product_pod")
        for book in books:
            book_url = book.css("div.image_container a::attr(href)").get()
            image_url_rela = book.css("div.image_container a img::attr(src)").get()
            # response.urljoin()拼接相对路径成绝对路径
            image_url = response.urljoin(image_url_rela)

            yield response.follow(
                book_url,
                callback=self.parse_detail,
                # 需要传递的参数
                meta={"image_url": image_url}
            )

        # 翻页操作
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)


    def parse_detail(self, response):
        image_url = response.meta["image_url"]
        table = response.css("table.table")
        rating = response.css("div.product_main p.star-rating::attr(class)").get()

        # 收集item
        item = DistributedBooksItem(
            UPC=table.css("tr:nth-child(1) td::text").get(),
            标题=response.css("div.product_main h1::text").get(),
            类别=response.css("ul.breadcrumb li:nth-child(3) a::text").get(),
            价钱=response.css("div.product_main p.price_color::text").get(),
            库存=" ".join(response.css("div.product_main p.instock::text").getall()).strip(),
            评分=rating.split()[-1] if rating else "",
            描述=(response.css("div#product_description + p::text").get() or "").strip(),
            税前价格=(table.css("tr:nth-child(3) td::text").get() or "").strip(),
            税后价格=(table.css("tr:nth-child(4) td::text").get() or "").strip(),
            税=(table.css("tr:nth-child(5) td::text").get() or "").strip(),
            图片链接=image_url,
            网页链接=response.url,
        )

        # 准备传走item给pipelines，然后调用process_item()
        yield item