from fastapi import APIRouter
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.patients import router as patients_router
from backend.app.api.v1.screenings import router as screenings_router
from backend.app.api.v1.explainability import router as explainability_router
from backend.app.api.v1.referrals import router as referrals_router
from backend.app.api.v1.reviews import router as reviews_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.reports import router as reports_router
from backend.app.api.v1.ophthalmologist import router as ophthalmologist_router
from backend.app.api.v1.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(screenings_router)
api_router.include_router(explainability_router)
api_router.include_router(referrals_router)
api_router.include_router(reviews_router)
api_router.include_router(audit_router)
api_router.include_router(reports_router)
api_router.include_router(ophthalmologist_router)
api_router.include_router(admin_router)
