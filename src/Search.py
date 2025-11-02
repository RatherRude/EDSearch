import traceback

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from search.compat import router as search_router


app = FastAPI()

@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(
        content="".join(
            traceback.format_exception(exc)
        ),
        status_code=500,
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(search_router, prefix="/search_compat")
    
if __name__ == "__main__":
    print("Starting FastAPI server", flush=True)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)