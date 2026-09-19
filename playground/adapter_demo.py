from distributed_books.items import DistributedBooksItem
from itemadapter import ItemAdapter


item = DistributedBooksItem(
    标题="测试图书",
    价钱="£51.77",
    库存="In stock (22 available)",
    评分="Three",
)

adapter = ItemAdapter(item)
print(adapter.get("标题"))
print(adapter["价钱"])

