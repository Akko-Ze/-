import psycopg


conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="distributed_books",
    user="postgres",
    password="123",
)

print("PostgreSQL连接成功")

conn.close()