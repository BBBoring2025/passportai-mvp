from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.dashboard import router as dashboard_router
from app.api.documents import router as documents_router
from app.api.extraction import router as extraction_router
from app.api.health import router as health_router
from app.api.invites import router as invites_router
from app.api.processing import router as processing_router
from app.api.validation import router as validation_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(invites_router)
api_router.include_router(cases_router)
api_router.include_router(documents_router)
api_router.include_router(processing_router)
api_router.include_router(extraction_router)
api_router.include_router(validation_router)
api_router.include_router(admin_router)
api_router.include_router(dashboard_router)
