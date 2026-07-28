from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def render_prescription_pdf(
    *,
    patient_name: str,
    doctor_name: str,
    doctor_specialization: str,
    appointment_time: str,
    urgency_level: int,
    notes: str,
) -> bytes:
    template = _env.get_template("prescription.html")
    html_content = template.render(
        patient_name=patient_name,
        doctor_name=doctor_name,
        doctor_specialization=doctor_specialization,
        appointment_time=appointment_time,
        urgency_level=urgency_level,
        notes=notes,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
    return HTML(string=html_content).write_pdf()