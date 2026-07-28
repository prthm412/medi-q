import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.appointments import _assert_can_view_appointment
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User
from app.services.pdf_generator import render_prescription_pdf

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{appointment_id}/prescription")
def get_prescription(
    appointment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    _assert_can_view_appointment(db, current_user, appointment)

    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    medical_record = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.appointment_id == appointment_id)
        .first()
    )
    if not medical_record:
        raise HTTPException(
            status_code=404,
            detail="No medical record found for this appointment — a prescription cannot be generated without recorded notes",
        )

    pdf_bytes = render_prescription_pdf(
        patient_name=patient.name,
        doctor_name=doctor.name,
        doctor_specialization=doctor.specialization,
        appointment_time=appointment.scheduled_time.strftime("%Y-%m-%d %H:%M UTC"),
        urgency_level=appointment.urgency_level,
        notes=medical_record.notes,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="prescription_{appointment_id}.pdf"'},
    )