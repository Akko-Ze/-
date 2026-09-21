import asyncio
import redis.asyncio as redis
import time
from distributed_books import settings


async def main():
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        while True:
            workers = await redis_client.hgetall("books:workers")
            current_time = int(time.time())

            for worker_id, last_heartbeat in workers.items():
                last_heartbeat = int(last_heartbeat)
                elapsed_time = current_time - last_heartbeat

                if elapsed_time <=15:
                    status = "alive"
                else:
                    status = "offline"

                print(f"{worker_id} | {status} | 最后心跳距今{elapsed_time}秒")
            await asyncio.sleep(5)
    finally:
        await redis_client.aclose()


if __name__ == '__main__':
    asyncio.run(main())