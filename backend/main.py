from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import workflow, reviews, analysis, prd, test_cases, monitor, import_api, data_source, validation

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflow.router)
app.include_router(reviews.router)
app.include_router(analysis.router)
app.include_router(prd.router)
app.include_router(test_cases.router)
app.include_router(monitor.router)
app.include_router(import_api.router)
app.include_router(data_source.router)
app.include_router(validation.router)


@app.get("/")
async def root():
    return {"message": "App Review Insights API", "version": "1.0.0"}
