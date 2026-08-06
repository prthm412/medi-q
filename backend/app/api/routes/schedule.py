from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.schedule import ScheduleOptimizeRequest, ScheduleOptimizeResponse
from app.services.scheduling import optimize_day

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post(
    "/optimize",
    response_model=ScheduleOptimizeResponse,
    dependencies=[Depends(require_role(UserRole.admin))],
)
def optimize_schedule(payload: ScheduleOptimizeRequest, db: Session = Depends(get_db)):
    return optimize_day(db, payload.date)