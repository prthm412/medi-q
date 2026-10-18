from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.analytics import AnalyticsSummary
from app.services.analytics import get_summary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    dependencies=[Depends(require_role(UserRole.admin))],
)
def analytics_summary(days: int = Query(14, ge=1, le=90), db: Session = Depends(get_db)):
    return get_summary(db, days)