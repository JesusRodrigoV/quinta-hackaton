from fastapi import APIRouter
from app.api.endpoints import router as audit_router
from app.api.compliance import router as compliance_router

api_router = APIRouter()

# Incluimos todas las sub-rutas
api_router.include_router(audit_router)
api_router.include_router(compliance_router)