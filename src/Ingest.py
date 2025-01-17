import json
import readline
import sys
from threading import Semaphore
import traceback
import requests
import ijson
import gzip
import fastapi
from concurrent.futures import ThreadPoolExecutor
import tracemalloc

from lib.Database import (
    body_to_tables,
    create_tables,
    pg_connection,
    station_to_tables,
    system_to_tables,
)

snapshot_before = None


def ingest_item(line: bytes):
    item = json.loads(line.decode("utf-8").strip().strip(","))
    print("Ingesting system:", item["name"])
    try:
        item["id"] = item["id64"]

        station_docs = item.pop("stations", [])
        # item["station_ids"] = [station["id"] for station in station_docs]
        for station in station_docs:
            station["systemId"] = item["id64"]
            station["systemName"] = item["name"]
            station["id"] = station["id"]
            station["coords"] = item["coords"]

            if not "landingPads" in station:
                station["landingPads"] = {"small": 0, "medium": 0, "large": 0}

        body_docs = item.pop("bodies", [])
        # item["body_ids"] = [body["id64"] for body in body_docs]
        for body in body_docs:
            body["systemId"] = item["id64"]
            body["systemName"] = item["name"]
            body["coords"] = item["coords"]
            body["id"] = body["id64"]
            body_stations = body.pop("stations", [])

            for station in body_stations:
                station["systemId"] = item["id64"]
                station["systemName"] = item["name"]
                station["bodyId"] = body["id64"]
                station["bodyName"] = body["name"]
                station["coords"] = body["coords"]
                station["id"] = station["id"]

                if not "landingPads" in station:
                    station["landingPads"] = {"small": 0, "medium": 0, "large": 0}

            station_docs.extend(body_stations)
        # print("Count Bodies:", len(body_docs))
        # print("Count Stations:", len(station_docs))

        # insert
        try:
            tables: dict[str, list[dict]] = {}
            for table, rows in system_to_tables(item).items():
                if table not in tables:
                    tables[table] = []
                tables[table].extend(rows)
            for station in station_docs:
                for table, rows in station_to_tables(station).items():
                    if table not in tables:
                        tables[table] = []
                    tables[table].extend(rows)
            for body in body_docs:
                for table, rows in body_to_tables(body).items():
                    if table not in tables:
                        tables[table] = []
                    tables[table].extend(rows)
        except Exception as e:
            print("Error inserting", item["name"], e, file=sys.stderr)
            print(item, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            # raise e
            return

        # db cursor and start transaction
        with pg_connection() as (conn, cur):
            cur.execute(f"DELETE FROM systems WHERE id = %s", (item["id"],))

            # batch insert
            try:
                for table, rows in tables.items():
                    if not rows:
                        continue
                    cur.executemany(
                        f"INSERT INTO {table} ({','.join(rows[0].keys())}) VALUES ({','.join(['%s']*len(rows[0].keys()))})",
                        [tuple(row.values()) for row in rows],
                    )
            except Exception as e:
                print("Error inserting", item["name"], e, file=sys.stderr)
                print(item, file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                # rollback transaction if error occurs
                conn.rollback()
                # raise e
            conn.commit()

    except Exception as e:
        print("Error ingesting", item["name"], e, file=sys.stderr)
        print(item, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        # raise e


def ingest(url: str):
    # Setup postgres
    print("initializing db...")
    create_tables()
    print("initialized!")

    # setup task pool
    print("initializing task pool...")
    pool = ThreadPoolExecutor(10)
    semaphores = Semaphore(10)
    print("initialized!")

    # Stream download from URL
    print("Downloading galaxy data...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    print("Streaming!")

    total_length = int(response.headers["Content-Length"])

    percentage = 0
    count = 0
    tracemalloc.start()
    # Wrap the response with gzip decompression
    with gzip.GzipFile(fileobj=response.raw, mode="rb") as f:
        # Read line by line using readline
        while True:
            line = f.readline()
            if not line:
                break
            count += 1
            # if count == 100:
            #    snapshot_before = tracemalloc.take_snapshot()
            # if count == 1000:
            #    snapshot_after = tracemalloc.take_snapshot()
            #    top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
            #    print("[ Top 10 differences ]")
            #    for stat in top_stats[:10]:
            #        print(stat)
            #    break

            new_percentage = round(response.raw.tell() * 100 / total_length, 2)
            if percentage != new_percentage:
                print(f"Progress: {new_percentage} %, {count} systems")
                percentage = new_percentage

            semaphores.acquire(True, 120)
            future = pool.submit(ingest_item, line)
            future.add_done_callback(lambda _: semaphores.release())

    print("Wait for all tasks to finish...")
    pool.shutdown(wait=True)

    print("Done ingesting!")


if __name__ == "__main__":
    try:
        # url = "https://downloads.spansh.co.uk/galaxy_1day.json.gz"
        # url = "https://downloads.spansh.co.uk/galaxy_populated.json.gz"
        # url = "http://localhost:8080/galaxy_populated.json.gz"
        ingest("http://localhost:8080/galaxy_1day.json.gz")
        exit(0)

        executor = ThreadPoolExecutor(2)
        app = fastapi.FastAPI()

        @app.post("/ingest")
        def ingest_endpoint(body: dict):
            executor.submit(ingest, body.get("url"))
            return {"status": "starting ingestion job", "url": body.get("url")}

        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=5000)
    except Exception as e:
        print(e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        exit(2)
# curl -X POST localhost:5002/ingest -H "Content-Type: application/json" -d '{"url":"https://downloads.spansh.co.uk/galaxy_populated.json.gz"}'
