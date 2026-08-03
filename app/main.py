from fastapi import FastAPI

from app.api.v1.router import api_router


app = FastAPI(title="Farec API")


@app.get("/")
async def root() -> dict[str, str]:
	return {"message": "Farec API"}


app.include_router(api_router, prefix="/api/v1")