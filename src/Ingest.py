import bz2
from datetime import date
import json
import time
import traceback
from typing import Any, Callable

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel


from .Database import create_tables, pg_connection

from .ingest.ScanBaryCentre import convert_scanbarycentre
from .ingest.Scan import convert_scan
from .ingest.FSDJump import convert_fsd_jump
from .ingest.Docked import convert_docked
from .ingest.ApproachSettlement import convert_approach_settlement
from .ingest.CarrierJump import convert_carrier_jump
from .ingest.Market import convert_market
from .ingest.Outfitting import convert_outfitting
from .ingest.Shipyard import convert_shipyard
from .ingest.SAASignals import convert_saa_signals_found
from .ingest.FSSSignalDiscovered import convert_fss_signal_discovered
from .ingest.FSSBodySignals import convert_fss_body_signals


from .models.eddn.ScanBaryCentre import ScanBaryCentre
from .models.eddn.Scan import Scan
from .models.eddn.EDDNEnvelope import EDDNEnvelope
from .models.eddn.FSDJump import FSDJump
from .models.eddn.Docked import Docked
from .models.eddn.ApproachSettlement import ApproachSettlement
from .models.eddn.CarrierJump import CarrierJump
from .models.eddn.Market import Market
from .models.eddn.Outfitting import Outfitting
from .models.eddn.Shipyard import Shipyard
from .models.eddn.FSSSignalDiscovered import FSSSignalDiscovered
from .models.eddn.FSSBodySignals import FSSBodySignals
from .models.eddn.SAASignalsFound import SAASignalsFound

from .models.db.landmark import create_landmark_tables
from .models.db.system import create_system_tables
from .models.db.body import create_body_tables
from .models.db.station import create_station_tables
from .models.db.market import create_market_tables
from .models.db.outfitting import create_outfitting_tables
from .models.db.shipyard import create_shipyard_tables
from .models.db.signals import create_signal_tables
from .models.db.ingestion import create_ingestion_table, lock_latest_ingestion_timestamp

app = FastAPI()

@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(
        content="".join(
            traceback.format_exception(exc)
        ),
        status_code=500,
    )
    

def load_file_sync(filename: str, date_obj: date):
    year_month = date_obj.strftime("%Y-%m")
    full_date = date_obj.strftime("%Y-%m-%d")
    url = f"https://edgalaxydata.space/EDDN/{year_month}/{filename}-{full_date}.jsonl.bz2"
    print(f"Downloading data from {url}", flush=True)

    with httpx.stream("GET", url, timeout=None) as response:
        response.raise_for_status()

        decompressor = bz2.BZ2Decompressor()
        buffer = b""
        for chunk in response.iter_bytes():
            decompressed_chunk = decompressor.decompress(chunk)
            if not decompressed_chunk:
                continue
            
            buffer += decompressed_chunk
            lines = buffer.split(b'\n')
            buffer = lines.pop()  # Keep the last, possibly incomplete line

            for line_bytes in lines:
                if line_bytes:
                    line = line_bytes.decode('utf-8').strip()
                    if line and line.startswith('{"'):
                        yield line

        # Process any remaining data in the buffer
        if buffer:
            line = buffer.decode('utf-8').strip()
            if line and line.startswith('{"'):
                yield line


async def load_file(filename: str, date: date):
    year_month = date.strftime("%Y-%m")
    full_date = date.strftime("%Y-%m-%d")
    url = f"https://edgalaxydata.space/EDDN/{year_month}/{filename}-{full_date}.jsonl.bz2"
    print(f"Downloading data from {url}", flush=True)

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()

            decompressor = bz2.BZ2Decompressor()
            buffer = b""
            async for chunk in response.aiter_bytes():
                decompressed_chunk = decompressor.decompress(chunk)
                if not decompressed_chunk:
                    continue
                
                buffer += decompressed_chunk
                lines = buffer.split(b'\n')
                buffer = lines.pop()  # Keep the last, possibly incomplete line

                for line_bytes in lines:
                    if line_bytes:
                        line = line_bytes.decode('utf-8').strip()
                        #print(f"Ingesting line: {line}", flush=True)
                        if line and line.startswith('{"'):
                            yield line

            # Process any remaining data in the buffer
            if buffer:
                line = buffer.decode('utf-8').strip()
                #print(f"Ingesting line: {line}", flush=True)
                if line and line.startswith('{"'):
                    yield line

def ingest(day: date, file: str, model: type[BaseModel], convert_func: Callable[[Any, Any], Any]):
    total = 0
    success = 0
    skipped = 0
    failure = 0
    start_time = time.time()
    for line in load_file_sync(file, day):
        total += 1
        if total % 1000 == 0:
            print(f"{file}: Ingested {total} lines so far, {success} successful, {skipped} skipped, {failure} failed\n{time.time() - start_time:.2f} seconds elapsed, {total / (time.time() - start_time):.2f} lines/second", flush=True)
        try:
            envelope = EDDNEnvelope.model_validate_json(line)
            if not envelope.message.odyssey or not envelope.message.horizons:
                skipped += 1
                continue
            
            event: Any = model.model_validate(envelope.message.model_dump())

            # Convert first to know which DB models and primary keys will be affected
            models = convert_func(event, envelope)

            # Build list of (model_name, primary_key_json) for all resulting models
            model_map = {
                'systems': 'system',
                'stations': 'station',
                'bodies': 'body',
                'landmarks': 'landmark',
                'markets': 'market',
                'shipyards': 'shipyard',
                'outfittings': 'outfitting',
                'signals': 'signal'
            }
            locks: set[tuple[str, str]] = set()
            for attr, model_name in model_map.items():
                items = getattr(models, attr, [])
                if not items:
                    continue
                for m in items:
                    pk = json.dumps({k: getattr(m, k) for k in m.primary_keys}, sort_keys=True)
                    locks.add((model_name, pk))

            if not locks:
                # Nothing to write
                skipped += 1
                continue

            # Acquire locks in a stable order to avoid deadlocks
            ordered_locks = sorted(locks)

            with pg_connection() as (conn, cur):
                # Start a transaction and set a modest lock timeout
                cur.execute("BEGIN; SET LOCAL lock_timeout = '3s';")

                # Acquire per-model locks; all must succeed
                all_locked = True
                for model_name, primary_key in ordered_locks:
                    if not lock_latest_ingestion_timestamp(cur, model_name, primary_key, getattr(event, 'event'), getattr(event, 'timestamp')):
                        all_locked = False
                        break

                if not all_locked:
                    cur.execute("ROLLBACK;")
                    skipped += 1
                    continue
            
                # Perform the upserts under the same transaction
                models.upsert_all(cur)
                cur.execute("COMMIT;")
                
            success += 1
        except Exception as e:
            failure += 1
            print(f"Error ingesting line: {line}", flush=True)
            print(f"Exception: {e}", flush=True)
            traceback.print_exc()
    report: dict[str, str | int] = {"status": "success", "input": file, "total": total, "success": success, "skipped": skipped, "failure": failure}
    print(f'{file}: Finished ingesting {total} lines, {success} successful, {skipped} skipped, {failure} failed\n{time.time() - start_time:.2f} seconds elapsed, {total / (time.time() - start_time):.2f} lines/second', flush=True)
    return report


# New endpoint: /ingest/day/{model} with model optional

datasets: dict[str, dict[str, Any]] = {
    "FSDJump": {
        "file": "Journal.FSDJump",
        "model": FSDJump,
        "convert": convert_fsd_jump,
    },
    "Scan": {
        "file": "Journal.Scan",
        "model": Scan,
        "convert": convert_scan,
    },
    "ScanBaryCentre": {
        "file": "Journal.ScanBaryCentre",
        "model": ScanBaryCentre,
        "convert": convert_scanbarycentre,
    },
    "Docked": {
        "file": "Journal.Docked",
        "model": Docked,
        "convert": convert_docked,
    },
    "ApproachSettlement": {
        "file": "Journal.ApproachSettlement",
        "model": ApproachSettlement,
        "convert": convert_approach_settlement,
    },
    "CarrierJump": {
        "file": "Journal.CarrierJump",
        "model": CarrierJump,
        "convert": convert_carrier_jump,
    },
    "Market": {
        "file": "Commodity",
        "model": Market,
        "convert": convert_market,
    },
    "Outfitting": {
        "file": "Outfitting",
        "model": Outfitting,
        "convert": convert_outfitting,
    },
    "Shipyard": {
        "file": "Shipyard",
        "model": Shipyard,
        "convert": convert_shipyard,
    },
    "SAASignalsFound": {
        "file": "Journal.SAASignalsFound",
        "model": SAASignalsFound,
        "convert": convert_saa_signals_found,
    },
    "FSSSignalDiscovered": {
        "file": "Journal.FSSSignalDiscovered",
        "model": FSSSignalDiscovered,
        "convert": convert_fss_signal_discovered,
    },
    "FSSBodySignals": {
        "file": "Journal.FSSBodySignals",
        "model": FSSBodySignals,
        "convert": convert_fss_body_signals,
    },
}

# Accepts /ingest/{day} or /ingest/{day}/{model} with model optional
@app.post("/ingest/today")
@app.post("/ingest/{day}")
@app.post("/ingest/{day}/{model}")
async def ingest_for_day(
    day: date | None = None,
    model: str | None = None
):
    """
    Downloads data for a specific day, decompresses it, and ingests it line by line.
    If model is not provided, ingests all models.
    """
    reports = {}
    if not day:
        day = date.today()
    if model:
        if model not in datasets:
            return {"status": "error", "message": f"Model {model} not found."}
        dataset = datasets[model]
        report = ingest(
            day,
            dataset["file"],
            dataset["model"],
            dataset["convert"]
        )
        reports[model] = report
    else:
        # Ingest all datasets 4 at once, start the 5th once one of the first 4 is done, and so on, so a pool size of 4
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=4) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, ingest, day, dataset["file"], dataset["model"], dataset["convert"])
                for dataset in datasets.values()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for model_name, report in zip(datasets.keys(), results):
                reports[model_name] = report

    return reports



if __name__ == "__main__":
    print("Starting EDSearch-ng Ingest Service", flush=True)
    print("Creating database tables if they do not exist", flush=True)
    # Create necessary tables
    create_tables([
        create_ingestion_table(),
        create_system_tables(),
        create_body_tables(),
        create_station_tables(),
        create_landmark_tables(),
        create_market_tables(),
        create_shipyard_tables(),
        create_outfitting_tables(),
        create_signal_tables(),
    ], drop=True)
    print("Database tables created", flush=True)
    print("Starting FastAPI server", flush=True)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)