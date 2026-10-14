from fastapi import APIRouter, Depends

from app.api.dependencies import require_api_key
from app.api.v1 import candidates, jobs, recommendations
from app.schemas.common import ERROR_RESPONSES

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)],
                   responses=ERROR_RESPONSES)
router.include_router(candidates.router)
router.include_router(jobs.router)
router.include_router(recommendations.router)
