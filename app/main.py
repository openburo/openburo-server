from fastapi import FastAPI

from app.api import router

app = FastAPI(title="OpenBURO Team Backend")
app.include_router(router)
