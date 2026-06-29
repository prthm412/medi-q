import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.redis_client import get_async_redis
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus, UserRole
from app.models.patient import Patient
from app.models.user import User
from app.schemas.queue import CheckInRequest, QueuePositionResponse
from app.services import queue_manager

router = APIRouter(tags=["queue"])


@router.post("/queue/checkin", response_model=QueuePositionResponse, status_code=201)
def check_in(
    body: CheckInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.patient, UserRole.admin)),
):
    appointment = db.query(Appointment).filter(Appointment.id == body.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if current_user.role == UserRole.patient:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status != AppointmentStatus.scheduled:
        raise HTTPException(status_code=400, detail="Appointment is not in a checkable-in state")

    today = datetime.now(timezone.utc).date()
    if appointment.scheduled_time.astimezone(timezone.utc).date() != today:
        raise HTTPException(status_code=400, detail="Check-in is only allowed on the day of the appointment")

    position_data = queue_manager.check_in(appointment.doctor_id, appointment.patient_id)
    if position_data is None:
        raise HTTPException(status_code=409, detail="Already checked in")

    return QueuePositionResponse(patient_id=appointment.patient_id, **position_data)


@router.websocket("/ws/queue/{doctor_id}")
async def queue_websocket(
    websocket: WebSocket,
    doctor_id: uuid.UUID,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_access_token(token)
    except ValueError:
        await websocket.close(code=1008)
        return

    user = db.query(User).filter(User.id == uuid.UUID(payload["sub"])).first()
    if not user:
        await websocket.close(code=1008)
        return

    role = UserRole(payload["role"])
    patient_id: uuid.UUID | None = None

    if role == UserRole.doctor:
        doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
        if not doctor or doctor.id != doctor_id:
            await websocket.close(code=1008)
            return
    elif role == UserRole.patient:
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        patient_id = patient.id if patient else None

    await websocket.accept()

    # Send the connecting patient their own current position right away,
    # rather than making them wait for someone else's status to change first.
    if patient_id is not None:
        position_data = queue_manager.get_position(doctor_id, patient_id)
        if position_data is not None:
            await websocket.send_json({
                "type": "position_update",
                "patient_id": str(patient_id),
                **position_data,
            })

    async_redis = get_async_redis()
    pubsub = async_redis.pubsub()
    channel = queue_manager.channel_name(doctor_id)
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await async_redis.aclose()