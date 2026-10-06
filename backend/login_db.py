from dotenv import load_dotenv
import os
import psycopg

load_dotenv(".env")

url = os.getenv("DATABASE_URL")

if not url:
    raise RuntimeError("DATABASE_URL not found in .env")

url = url.replace("postgresql+psycopg://", "postgresql://", 1)

conn = psycopg.connect(url)

print()
print("================================")
print("CONNECTED TO POSTGRESQL")
print("================================")

while True:
    sql = input("repogourd=> ")

    if sql.strip().lower() in ("exit", "quit", "\\q"):
        break

    try:
        with conn.cursor() as cur:
            cur.execute(sql)

            if cur.description:
                for row in cur.fetchall():
                    print(row)
            else:
                print("OK")

            conn.commit()

    except Exception as e:
        conn.rollback()
        print("ERROR:", e)

conn.close()
print("Disconnected.")