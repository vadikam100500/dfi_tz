import logging
import os

import uvicorn
from fastapi import FastAPI
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.api import api_router
from app.config.logging_settings import get_logger
from app.exceptions.exception import EntityException, NotFoundEntity

app = FastAPI(title='DFI TZ')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.getLogger("uvicorn.access").setLevel(level=logging.WARNING)
logger = get_logger(__name__)


@app.exception_handler(EntityException)
async def not_found_entity_exception_handler(_: Request, exc: EntityException):
    if isinstance(exc, NotFoundEntity):
        logger.error(f"Not found entity: {exc.message}")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": exc.message})

    logger.error(f"Unprocessable entity: {exc.message}")
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"message": exc.message})


@app.exception_handler(Exception)
async def exception_handler(req: Request, exc):
    logger.error(f"Unhandled error request: {str(req)}, body: {exc}")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Not available now"})


@app.get("/")
async def main():
    return "I'm entry point of DFI TZ"


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
