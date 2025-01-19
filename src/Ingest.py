import json
import sys
from threading import Semaphore
import traceback
import requests
import tempfile
import gzip
import fastapi
from concurrent.futures import ThreadPoolExecutor
import tracemalloc
import shutil

from .lib.Database import (
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

        for station in station_docs:
            if "outfitting" in station and station["outfitting"]:
                if "modules" in station["outfitting"]:
                    moduleIds = [
                        module["moduleId"]
                        for module in station["outfitting"]["modules"]
                    ]
                    # find for duplicates
                    duplicates = []
                    for moduleId in moduleIds:
                        if moduleIds.count(moduleId) > 1:
                            duplicates.append(moduleId)

                    if duplicates:
                        print(
                            f"Duplicate modules in station {station['name']} in system {item['name']}: {duplicates}"
                        )
                        # remove duplicates
                        station["outfitting"]["modules"] = [
                            module
                            for module in station["outfitting"]["modules"]
                            if module["moduleId"] not in duplicates
                        ]

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
            # delete all stations
            cur.execute(
                f"DELETE FROM stations WHERE id = ANY(%s)",
                ([station["id"] for station in station_docs],),
            )
            # delete all bodies
            cur.execute(
                f"DELETE FROM bodies WHERE id = ANY(%s)",
                ([body["id"] for body in body_docs],),
            )

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

    # Create temp folder
    tmpdir = tempfile.mkdtemp()

    # Download from URL into temp folder
    print(f"Downloading galaxy data to {tmpdir}...")
    tmpfile = f"{tmpdir}/input.json.gz"
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(tmpfile, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    total_length = int(response.headers["Content-Length"])
    print(f"Downloaded {total_length} bytes")

    percentage = 0
    count = 0
    tracemalloc.start()
    # stream read from gzipped file
    with open(tmpfile, "rb") as filein:
        with gzip.GzipFile(tmpfile, mode="r") as fileunzipped:
            # Read line by line using readline
            while True:
                line = fileunzipped.readline()
                if not line:
                    break
                count += 1
                # if count == 1000:
                #    snapshot_before = tracemalloc.take_snapshot()
                # if count == 10000:
                #    snapshot_after = tracemalloc.take_snapshot()
                #    top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
                #    print("[ Top 10 differences ]")
                #    for stat in top_stats[:10]:
                #        print(stat)
                #    break

                uncompressed_frac = filein.tell() / total_length
                process_frac = (
                    1  # TODO we need to know the size of the uncompressed file so far
                )
                new_percentage = round(uncompressed_frac * process_frac * 100, 2)
                if percentage != new_percentage:
                    print(f"Progress: {new_percentage} %, {count} systems")
                    percentage = new_percentage

                semaphores.acquire(True, 120)
                future = pool.submit(ingest_item, line)
                future.add_done_callback(lambda _: semaphores.release())

    print("Wait for all tasks to finish...")
    pool.shutdown(wait=True)

    print("Done ingesting!")
    print("Cleaning up...")
    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    try:
        # url = "https://downloads.spansh.co.uk/galaxy_1day.json.gz"
        # url = "https://downloads.spansh.co.uk/galaxy_populated.json.gz"
        # url = "http://localhost:8080/galaxy_populated.json.gz"
        ingest("https://downloads.spansh.co.uk/galaxy_1day.json.gz")
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
